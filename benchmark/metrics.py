from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class MetricResult:
    precision_at_1: float
    recall_at_k: float
    mrr: float
    hit_rate: float
    avg_rank: Optional[float]


def precision_at_1(y_true: List[str], y_pred_top1: List[Optional[str]]) -> float:
    assert len(y_true) == len(y_pred_top1)
    correct = 0
    total = len(y_true)
    for gt, pred in zip(y_true, y_pred_top1):
        if pred is not None and str(pred) == str(gt):
            correct += 1
    return correct / total if total else 0.0


def recall_at_k(y_true: List[str], y_pred_topk: List[List[str]]) -> float:
    assert len(y_true) == len(y_pred_topk)
    hits = 0
    total = len(y_true)
    for gt, topk in zip(y_true, y_pred_topk):
        if any(str(c) == str(gt) for c in topk):
            hits += 1
    return hits / total if total else 0.0


def mean_reciprocal_rank(y_true: List[str], y_pred_topk: List[List[str]]) -> float:
    assert len(y_true) == len(y_pred_topk)
    total = len(y_true)
    s = 0.0
    for gt, topk in zip(y_true, y_pred_topk):
        rr = 0.0
        for i, cand in enumerate(topk, start=1):
            if str(cand) == str(gt):
                rr = 1.0 / i
                break
        s += rr
    return s / total if total else 0.0


def average_rank(y_true: List[str], y_pred_topk: List[List[str]]) -> Optional[float]:
    ranks: List[int] = []
    for gt, topk in zip(y_true, y_pred_topk):
        for i, cand in enumerate(topk, start=1):
            if str(cand) == str(gt):
                ranks.append(i)
                break
    if not ranks:
        return None
    return sum(ranks) / len(ranks)


def compute_all_metrics(y_true: List[str], y_pred_topk: List[List[str]]) -> MetricResult:
    top1 = [row[0] if row else None for row in y_pred_topk]
    p1 = precision_at_1(y_true, top1)
    r_at_k = recall_at_k(y_true, y_pred_topk)
    mrr = mean_reciprocal_rank(y_true, y_pred_topk)
    hr = r_at_k  # hit rate == recall@k at query-level
    avg_r = average_rank(y_true, y_pred_topk)
    return MetricResult(precision_at_1=p1, recall_at_k=r_at_k, mrr=mrr, hit_rate=hr, avg_rank=avg_r)


