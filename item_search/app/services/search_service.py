from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from item_search.app.src.refine.extractors.features import extract_features
from item_search.app.src.refine.extractors.models import ItemFeatures
from item_search.app.src.refine.parsers.models import ParseOutput
from item_search.app.src.refine.searchers.models import search as run_search
from item_search.app.src.refine.searchers.cosine_index import CosineIndex
from item_search.app.src.refine.config import TOP_K, SIMILARITY_THRESHOLD


def build_query_features(query_text: str) -> ItemFeatures:
    po = ParseOutput(source_path=Path("<inline>"), pages_text=[query_text])
    return extract_features(po)


def run_vector_search(
    query: ItemFeatures,
    corpus: ItemFeatures,
    index: CosineIndex,
    top_k: Optional[int],
    threshold: Optional[float],
) -> Dict[str, Any]:
    results = run_search(
        query=query,
        reference=corpus,
        index=index,
        top_k=top_k or TOP_K,
        threshold=threshold or SIMILARITY_THRESHOLD,
    )

    if not results:
        return {"best_match_id": None, "best_match_name": None, "best_score": 0.0, "top_k": []}
    r0 = results[0]
    return {
        "best_match_id": r0.best_match_id,
        "best_match_name": next((m.meta.get("name") for m in r0.top_k if m.item_id == r0.best_match_id), None),
        "best_score": r0.best_score,
        "top_k": [
            {"item_id": m.item_id, "score": m.score, "meta": dict(m.meta)} for m in r0.top_k
        ],
    }


