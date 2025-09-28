from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable, List, Dict, Any, cast

import openpyxl
from .models import ParseOutput, ParsedTable, ParsedItem


def _load_json(path: Path) -> Iterable[Dict[str, Any]]:
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        if isinstance(data, list):
            for row in data:
                if isinstance(row, dict):
                    yield row
        elif isinstance(data, dict):
            yield data


def _load_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    yield obj
            except Exception:
                continue


def _load_csv(path: Path) -> Iterable[Dict[str, Any]]:
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield dict(row)


def _load_xlsx(path: Path) -> Iterable[Dict[str, Any]]:
    wb = openpyxl.load_workbook(str(path), read_only=True, data_only=True)
    ws = cast(Any, wb.active)
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []
    headers = [str(h).strip() if h is not None else "" for h in rows[0]]
    for r in rows[1:]:
        obj = {headers[i]: r[i] for i in range(len(headers))}
        yield obj


def parse_tabular(path: Path) -> ParseOutput:
    """Load a reference catalog file (CSV/XLSX/JSON/JSONL) into ParsedTable and ParsedItem list."""
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        rows_iter = _load_jsonl(path)
    elif suffix == ".json":
        rows_iter = _load_json(path)
    elif suffix == ".csv":
        rows_iter = _load_csv(path)
    elif suffix == ".xlsx":
        rows_iter = _load_xlsx(path)
    else:
        raise ValueError(f"Unsupported tabular format: {suffix}")

    rows: List[Dict[str, Any]] = list(rows_iter)
    headers: List[str] = sorted({k for r in rows for k in r.keys()}) if rows else []

    # Table view
    table_rows: List[List[str]] = [[str(r.get(h, "")) for h in headers] for r in rows]
    table = ParsedTable(headers=headers, rows=table_rows, meta={"count": len(rows)})

    # Items view (project commonly used fields)
    items: List[ParsedItem] = []
    for r in rows:
        raw_price = r.get("price")
        price_val: Any
        if raw_price is None:
            price_val = None
        else:
            s = str(raw_price).strip()
            price_val = float(s.replace(" ", "").replace(",", ".")) if s else None

        items.append(
            ParsedItem(
                name=str(r.get("title", r.get("name", ""))),
                sku=None if r.get("sku") is None else str(r.get("sku")),
                price=price_val,
                brand=None if r.get("brand") is None else str(r.get("brand")),
                attrs={"marketplace": r.get("marketplace"), "id": r.get("id")},
                raw_row=r,
            )
        )

    return ParseOutput(source_path=path, pages_text=[], tables=[table], items_raw=items)

