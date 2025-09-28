from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ParsedTable:
    headers: List[str] = field(default_factory=list)
    rows: List[List[str]] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedItem:
    name: str
    qty: Optional[float] = None
    unit: Optional[str] = None
    brand: Optional[str] = None
    sku: Optional[str] = None
    price: Optional[float] = None
    attrs: Dict[str, Any] = field(default_factory=dict)
    raw_row: Optional[Dict[str, Any]] = None


@dataclass
class ParseOutput:
    source_path: Path
    pages_text: List[str] = field(default_factory=list)
    tables: List[ParsedTable] = field(default_factory=list)
    items_raw: List[ParsedItem] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)


def parse_ocr(path: Path) -> ParseOutput:  # stub signature for colab tests
    raise NotImplementedError


def parse_docx(path: Path) -> ParseOutput:  # stub signature for colab tests
    raise NotImplementedError


def parse_tabular(path: Path) -> ParseOutput:  # for reference catalogs (csv/xlsx/jsonl)
    raise NotImplementedError


def parse_odt(path: Path) -> ParseOutput:  # for ODT documents
    raise NotImplementedError


