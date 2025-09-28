from __future__ import annotations

import re
from typing import List


def normalize_text(text: str) -> str:
    t = text.lower().strip()
    t = re.sub(r"\s+", " ", t)
    return t


def simple_tokenize(text: str) -> List[str]:
    text = normalize_text(text)
    return re.findall(r"[\w\-]+", text, flags=re.UNICODE)


# Minimal RU/EN stopwords (extendable)
STOPWORDS = set([
    "и", "в", "на", "для", "от", "до", "с", "по", "из", "а", "но", "или", "как", "что",
    "the", "a", "an", "for", "of", "to", "in", "on", "by", "and", "or", "with",
])


def filter_stopwords(tokens: List[str]) -> List[str]:
    return [t for t in tokens if t not in STOPWORDS]


def normalize_numbers(text: str) -> str:
    # Join number patterns like '330 x 233 мм' -> '330x233мм'
    t = re.sub(r"\s*x\s*", "x", text)
    t = re.sub(r"\s+мм", "мм", t)
    return t


