from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from refine.parsers import parse_ocr, parse_docx, parse_odt
from refine.parsers.tabular_parser import parse_tabular
from refine.extractors.features import extract_features
from refine.extractors.models import ItemFeatures
from refine.searchers.cosine_index import CosineIndex
from refine.searchers.models import SearchResult, search
from .metrics import compute_all_metrics, MetricResult


def _parse_target(path: Path):
    suffix = path.suffix.lower()
    if suffix == '.pdf':
        return parse_ocr(path)
    if suffix == '.docx':
        return parse_docx(path)
    if suffix == '.odt':
        return parse_odt(path)
    # fallback OCR for unknown
    return parse_ocr(path)


def run_dataset(queries_jsonl: Path, top_k: int = 5, threshold: float = 0.35) -> MetricResult:
    y_true: List[str] = []
    y_pred_topk: List[List[str]] = []

    with open(queries_jsonl, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            q = json.loads(line)

            target_path = Path(q["target_path"])  # doc path
            references = [Path(p) for p in q.get("references", [])]

            # parse target
            parsed = _parse_target(target_path)
            query_features: ItemFeatures = extract_features(parsed)

            # parse references (merge)
            ref_features_list: List[ItemFeatures] = []
            for rp in references:
                ref_parsed = parse_tabular(rp)
                ref_features_list.append(extract_features(ref_parsed))
            merged_ref = ItemFeatures(items=[it for rf in ref_features_list for it in rf.items])

            # search
            index = CosineIndex()
            results: List[SearchResult] = search(
                query=query_features,
                reference=merged_ref,
                index=index,
                top_k=top_k,
                threshold=threshold,
            )
            
            # ground-truth collection: expect single label per query for now
            gt_items = q.get("ground_truth", [])
            if not gt_items:
                continue
            gt_id = str(gt_items[0]["expected_item_id"])  # minimal schema

            # collapse results to top_k ids
            # Align by the first query item (simplified baseline)
            if not results:
                continue
            # prefer catalog identifiers from meta to match ground truth
            top_ids = [
                str(m.meta.get('id') or m.meta.get('sku') or m.item_id)
                for m in results[0].top_k[:top_k]
            ]
    
            y_true.append(gt_id)
            y_pred_topk.append(top_ids)

    return compute_all_metrics(y_true, y_pred_topk)


