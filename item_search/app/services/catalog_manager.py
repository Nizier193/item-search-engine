from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any

from item_search.app.config import CATALOGUES_ROOT, MAX_LOADED_CATALOGS
from item_search.app.services.search_service import build_query_features, run_vector_search

from item_search.app.src.refine.parsers.tabular_parser import parse_tabular
from item_search.app.src.refine.extractors.features import extract_features
from item_search.app.src.refine.extractors.models import ItemFeatures
from item_search.app.src.refine.searchers.cosine_index import CosineIndex


@dataclass
class CatalogState:
    corpus: ItemFeatures
    index: CosineIndex


class CatalogManager:
    def __init__(self) -> None:
        self._catalogs: Dict[str, CatalogState] = {}

    def loaded_catalogs(self) -> List[str]:
        return list(self._catalogs.keys())

    def is_loaded(self, catalog_id: str) -> bool:
        return catalog_id in self._catalogs

    def warmup(self, catalog_id: str, references: List[str], limit_items: Optional[int] = None) -> int:
        if len(self._catalogs) >= MAX_LOADED_CATALOGS and catalog_id not in self._catalogs:
            raise RuntimeError("Max loaded catalogs reached")

        print("Warming up!")
        ref_features_list: List[ItemFeatures] = []
        for rel in references:
            path = (CATALOGUES_ROOT / rel).resolve()
            if not path.exists():
                raise FileNotFoundError(f"Reference not found: {path}")

            parsed = parse_tabular(path)
            ref_features_list.append(extract_features(parsed))

        print("Merging items.")
        items = [it for rf in ref_features_list for it in rf.items]
        if limit_items is not None and limit_items > 0:
            items = items[:limit_items]

        merged_ref = ItemFeatures(items=items)
        index = CosineIndex()
        index.fit(merged_ref)

        self._catalogs[catalog_id] = CatalogState(corpus=merged_ref, index=index)
        return len(merged_ref.items)

    def search_text(
        self,
        catalog_id: str,
        query_text: str,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None,
    ) -> Dict[str, Any]:
        if catalog_id not in self._catalogs:
            raise RuntimeError("Catalog not loaded")
            
        query_features = build_query_features(query_text)
        state = self._catalogs[catalog_id]
        return run_vector_search(query_features, state.corpus, state.index, top_k, threshold)


