from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class WarmupRequest(BaseModel):
    catalog_id: str = Field(..., description="Logical catalog identifier")
    references: List[str] = Field(..., description="Relative paths under src/catalogues/")
    limit_items: Optional[int] = Field(None, description="Optional cap on number of items to index for faster testing")


class WarmupResponse(BaseModel):
    status: str
    catalog_id: str
    items_indexed: int


class SearchRequest(BaseModel):
    catalog_id: str
    query_text: str
    top_k: Optional[int] = None
    threshold: Optional[float] = None


class MatchDTO(BaseModel):
    item_id: str
    score: float
    meta: Dict[str, Any] = {}


class SearchResponse(BaseModel):
    catalog_id: str
    query_text: str
    best_match_id: Optional[str]
    best_match_name: Optional[str] = None
    best_score: float
    top_k: List[MatchDTO]


