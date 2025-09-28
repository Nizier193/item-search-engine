from __future__ import annotations

from collections import Counter, defaultdict
from math import log, sqrt
from typing import Dict, List, Tuple

from .models import Match, VectorIndex
from ..extractors.models import ItemFeatures
from ..config import QUERY_TF_CLIP, SKU_ANCHOR_BOOST, NAME_BOOST, SKU_FIELD_BOOST, BRAND_BOOST, MIN_DF, MAX_DF_RATIO


class CosineIndex(VectorIndex):
    """Sparse TF-IDF cosine index with inverted lists.

    - No external dependencies
    - Scales to large catalogs via postings per token
    """

    def __init__(self) -> None:
        self._vocab: Dict[str, int] = {}
        self._idf: List[float] = []
        self._postings: Dict[int, List[Tuple[int, float]]] = {}
        self._doc_norms: List[float] = []
        self._doc_meta: List[Dict[str, str]] = []
        self._doc_ids: List[str] = []

    def fit(self, corpus: ItemFeatures) -> None:
        self._build(corpus)

    def _build(self, corpus: ItemFeatures) -> None:
        num_docs = len(corpus.items)
        self._doc_ids = [it.item_id for it in corpus.items]

        # 1) build df and vocab
        df_counter: Counter[str] = Counter()
        tokenized_docs: List[List[str]] = []
        for it in corpus.items:
            tokens = list(dict.fromkeys(it.tokens))  # unique per doc
            tokenized_docs.append(it.tokens)
            df_counter.update(tokens)

        # DF pruning
        max_df = max(1, int(MAX_DF_RATIO * num_docs))
        kept_tokens = [t for t, df in df_counter.items() if df >= MIN_DF and df <= max_df]

        self._vocab = {}
        for token in kept_tokens:
            self._vocab[token] = len(self._vocab)

        # 2) idf
        self._idf = [0.0] * len(self._vocab)
        for token, df in df_counter.items():
            if token not in self._vocab:
                continue
            tid = self._vocab[token]
            # smooth idf
            self._idf[tid] = log((1.0 + num_docs) / (1.0 + df)) + 1.0

        # 3) postings and norms
        postings: Dict[int, List[Tuple[int, float]]] = defaultdict(list)
        doc_norms: List[float] = [0.0] * num_docs
        doc_meta: List[Dict[str, str]] = []

        for doc_idx, it in enumerate(corpus.items):
            tf = Counter(it.tokens)
            # field boosts via attrs hints
            name_hint = it.name or ""
            sku_hint = it.attrs.get("sku") if hasattr(it, "attrs") else None
            brand_hint = it.attrs.get("brand") if hasattr(it, "attrs") else None
            weights: Dict[int, float] = {}
            for token, cnt in tf.items():
                if token not in self._vocab:
                    continue
                tid = self._vocab[token]
                boost = 1.0
                if sku_hint and token in str(sku_hint).lower():
                    boost *= SKU_FIELD_BOOST
                if brand_hint and token in str(brand_hint).lower():
                    boost *= BRAND_BOOST
                if name_hint and token in name_hint.lower():
                    boost *= NAME_BOOST
                w = float(cnt) * self._idf[tid] * boost
                weights[tid] = w
            norm = sqrt(sum(w * w for w in weights.values())) or 1.0
            doc_norms[doc_idx] = norm
            for tid, w in weights.items():
                postings[tid].append((doc_idx, w))

            # store meta (price, sku, marketplace, name)
            meta: Dict[str, str] = {}
            for k in ("price", "sku", "marketplace", "id"):
                if k in it.attrs:
                    meta[k] = str(it.attrs[k])
            meta["name"] = it.name
            doc_meta.append(meta)

        self._postings = postings
        self._doc_norms = doc_norms
        self._doc_meta = doc_meta

    def _query_vector(self, tokens: List[str]) -> Tuple[Dict[int, float], float]:
        # clip tf and apply anchor boosts (sku-like)
        tf = Counter(tokens)
        q_weights: Dict[int, float] = {}
        # simple sku anchor detection
        has_sku_anchor = any(any(ch.isdigit() for ch in t) and any(ch.isalpha() for ch in t) for t in tokens)
        for token, cnt in tf.items():
            tid = self._vocab.get(token)
            if tid is None:
                continue
            clipped = min(int(cnt), QUERY_TF_CLIP)
            boost = SKU_ANCHOR_BOOST if has_sku_anchor and any(c.isdigit() for c in token) and any(c.isalpha() for c in token) else 1.0
            q_weights[tid] = float(clipped) * self._idf[tid] * boost
        q_norm = sqrt(sum(w * w for w in q_weights.values())) or 1.0
        return q_weights, q_norm

    def search(self, query: ItemFeatures, top_k: int = 5) -> List[List[Match]]:
        results: List[List[Match]] = []
        for it in query.items:
            q_weights, q_norm = self._query_vector(it.tokens)
            if not q_weights:
                results.append([])
                continue

            scores: Dict[int, float] = defaultdict(float)
            for tid, qw in q_weights.items():
                for doc_idx, dw in self._postings.get(tid, ()):  # postings for token
                    scores[doc_idx] += qw * dw

            # cosine
            matches: List[Tuple[int, float]] = []
            for doc_idx, dot in scores.items():
                denom = self._doc_norms[doc_idx] * q_norm
                if denom <= 0.0:
                    continue
                sim = dot / denom
                if sim > 0.0:
                    matches.append((doc_idx, sim))

            matches.sort(key=lambda x: x[1], reverse=True)
            top = matches[:top_k]

            out: List[Match] = []
            for doc_idx, score in top:
                meta = self._doc_meta[doc_idx]
                out.append(
                    Match(
                        item_id=self._doc_ids[doc_idx],
                        score=score,
                        meta=meta,
                    )
                )
            results.append(out)
        return results


