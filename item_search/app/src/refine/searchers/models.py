from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from ..extractors.models import ItemFeatures
from ..config import FUZZY_SKU_THRESHOLD, FUZZY_NAME_THRESHOLD
from difflib import SequenceMatcher


@dataclass
class Match:
    item_id: str
    score: float
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResult:
    query_item_id: str
    best_match_id: Optional[str]
    best_score: float
    top_k: List[Match] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"SearchResult: query_item_id={self.query_item_id}, best_match_id={self.best_match_id}, best_score={self.best_score}"


@runtime_checkable
class VectorIndex(Protocol):
    def fit(self, corpus: ItemFeatures) -> None: ...
    def search(self, query: ItemFeatures, top_k: int = 5) -> List[List[Match]]: ...


def _price_from_meta(meta: Dict[str, Any]) -> Optional[float]:
    val = meta.get("price")
    if val is None:
        return None
    try:
        s = str(val).replace(" ", "").replace(",", ".")
        return float(s)
    except Exception:
        return None


def search(query: ItemFeatures, reference: ItemFeatures, index: VectorIndex, top_k: int = 5,
           threshold: float = 0.35) -> List[SearchResult]:
    """Run vector search, apply threshold, choose cheapest among passed.

    Returns list aligned to query.items order.
    """
    index.fit(reference)
    all_matches = index.search(query, top_k=top_k)

    results: List[SearchResult] = []
    for q_it, matches in zip(query.items, all_matches):
        # filter by similarity threshold
        passed = [m for m in matches if m.score >= threshold]
        best_id: Optional[str] = None
        best_score: float = 0.0

        if passed:
            # choose cheapest among passed (if price available), else max score
            cheapest = None
            cheapest_price = None
            for m in passed:
                price = _price_from_meta(m.meta)
                if price is not None:
                    if cheapest_price is None or price < cheapest_price:
                        cheapest = m
                        cheapest_price = price

            if cheapest is None:
                # fallback by highest score
                top_by_score = max(passed, key=lambda x: x.score)
                best_id = top_by_score.item_id
                best_score = top_by_score.score
            else:
                best_id = cheapest.item_id
                best_score = cheapest.score

        # If nothing passed threshold, apply fuzzy fallback
        if best_id is None:
            # try fuzzy SKU match: detect sku-like tokens in query text_repr
            q_text = getattr(q_it, "text_repr", "") or q_it.name
            q_tokens = [t for t in q_text.split() if any(c.isdigit() for c in t) and any(c.isalpha() for c in t)]
            candidate: Optional[Match] = None
            best_ratio = 0.0
            if q_tokens:
                for m in matches:
                    sku = str(m.meta.get("sku", ""))
                    if not sku:
                        continue
                    for qt in q_tokens:
                        r = SequenceMatcher(a=qt.lower(), b=sku.lower()).ratio()
                        if r > best_ratio:
                            best_ratio = r
                            candidate = m
                if candidate and best_ratio >= FUZZY_SKU_THRESHOLD:
                    best_id = candidate.item_id
                    best_score = candidate.score

            # fallback to name similarity if still none
            if best_id is None and q_text:
                candidate = None
                best_ratio = 0.0
                for m in matches:
                    name = str(m.meta.get("name", ""))
                    if not name:
                        continue
                    r = SequenceMatcher(a=q_text.lower()[:256], b=name.lower()[:256]).ratio()
                    if r > best_ratio:
                        best_ratio = r
                        candidate = m
                if candidate and best_ratio >= FUZZY_NAME_THRESHOLD:
                    best_id = candidate.item_id
                    best_score = candidate.score

        results.append(
            SearchResult(
                query_item_id=q_it.item_id,
                best_match_id=best_id,
                best_score=best_score,
                top_k=matches,
            )
        )

    return results


