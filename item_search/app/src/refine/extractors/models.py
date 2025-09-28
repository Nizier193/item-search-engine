from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ItemFeature:
    item_id: str
    name: str
    tokens: List[str] = field(default_factory=list)
    attrs: Dict[str, str] = field(default_factory=dict)
    text_repr: str = ""
    embedding: Optional[List[float]] = None


@dataclass
class ItemFeatures:
    items: List[ItemFeature] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"ItemFeatures: len={len(self.items)}; meta={self.meta}"

    
    def __len__(self) -> int:
        return len(self.items)


def extract_features(parse_output) -> ItemFeatures:  # stub signature for colab tests
    raise NotImplementedError


