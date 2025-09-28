from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from ..parsers.models import ParseOutput, ParsedItem, ParsedTable
from .models import ItemFeatures, ItemFeature
from ..utils import normalize_text, simple_tokenize, filter_stopwords, normalize_numbers
from ..config import WINDOW_SIZE, WINDOW_STRIDE


def _make_item_id(prefix: str, index: int) -> str:
    return f"{prefix}:{index}"


def _feature_from_parsed_item(pi: ParsedItem, idx: int) -> ItemFeature:
    name = pi.name or ""
    parts: List[str] = [name]

    # Flatten attrs into text representation (non-null only)
    if pi.brand:
        parts.append(str(pi.brand))
    if pi.sku:
        parts.append(str(pi.sku))
    if pi.unit:
        parts.append(str(pi.unit))

    # Convert numeric price to string if present
    if pi.price is not None:
        parts.append(str(pi.price))

    # Append key=value pairs from attrs to enrich searchability
    for k, v in (pi.attrs or {}).items():
        if v is None:
            continue
        parts.append(f"{k}:{v}")

    text_repr = normalize_numbers(normalize_text(" ".join(parts)))
    tokens = filter_stopwords(simple_tokenize(text_repr))
    attrs: Dict[str, str] = {}
    if pi.brand:
        attrs["brand"] = str(pi.brand)
    if pi.sku:
        attrs["sku"] = str(pi.sku)
    if pi.price is not None:
        attrs["price"] = str(pi.price)

    # carry raw id/marketplace if present
    if pi.attrs:
        for k in ("id", "marketplace", "source"):
            if k in pi.attrs and pi.attrs[k] is not None:
                attrs[k] = str(pi.attrs[k])

    return ItemFeature(
        item_id=_make_item_id("raw", idx),
        name=name,
        tokens=tokens,
        attrs=attrs,
        text_repr=text_repr,
        embedding=None,
    )


def _features_from_table(table: ParsedTable, base_idx: int) -> List[ItemFeature]:
    features: List[ItemFeature] = []
    headers = [normalize_text(h) for h in (table.headers or [])]

    # Heuristic columns
    def _col_index(candidates: List[str]) -> int:
        for i, h in enumerate(headers):
            if any(c in h for c in candidates):
                return i
        return -1

    name_idx = _col_index(["наименование", "товар", "название", "item", "name", "title"])
    sku_idx = _col_index(["sku", "артикул", "код", "id"])
    brand_idx = _col_index(["бренд", "brand"])
    price_idx = _col_index(["цена", "price", "стоимость"])

    for r_i, row in enumerate(table.rows or []):
        parts: List[str] = []
        name = ""

        if 0 <= name_idx < len(row):
            name = str(row[name_idx] or "")
            parts.append(name)
        else:
            # fallback: join all row cells as name-like text
            name = " ".join(str(v) for v in row if v is not None)
            parts.append(name)

        attrs: Dict[str, str] = {}
        if 0 <= sku_idx < len(row) and row[sku_idx] is not None:
            sku = str(row[sku_idx])
            parts.append(sku)
            attrs["sku"] = sku
        if 0 <= brand_idx < len(row) and row[brand_idx] is not None:
            brand = str(row[brand_idx])
            parts.append(brand)
            attrs["brand"] = brand
        if 0 <= price_idx < len(row) and row[price_idx] is not None:
            price_str = str(row[price_idx])
            parts.append(price_str)
            attrs["price"] = price_str

        # add header:value pairs for extra signal
        for c_i, cell in enumerate(row):
            val = str(cell) if cell is not None else ""
            if c_i < len(headers) and headers[c_i]:
                parts.append(f"{headers[c_i]}:{val}")
            else:
                parts.append(val)

        text_repr = normalize_numbers(normalize_text(" ".join(parts)))
        tokens = filter_stopwords(simple_tokenize(text_repr))

        features.append(
            ItemFeature(
                item_id=_make_item_id("tbl", base_idx + r_i),
                name=name,
                tokens=tokens,
                attrs=attrs,
                text_repr=text_repr,
                embedding=None,
            )
        )

    return features


def _features_from_pages_text(pages_text: List[str], base_idx: int) -> List[ItemFeature]:
    features: List[ItemFeature] = []
    for i, page in enumerate(pages_text or []):
        full = normalize_numbers(normalize_text(page))
        tokens = filter_stopwords(simple_tokenize(full))
        # windowing
        if not tokens:
            continue
        start = 0
        w = WINDOW_SIZE
        s = WINDOW_STRIDE
        wid = 0
        while start < len(tokens):
            chunk = tokens[start : start + w]
            if not chunk:
                break
            text_repr = " ".join(chunk)
            features.append(
                ItemFeature(
                    item_id=_make_item_id("txt", base_idx + i * 10_000 + wid),
                    name=text_repr[:80],
                    tokens=chunk,
                    attrs={},
                    text_repr=text_repr,
                    embedding=None,
                )
            )
            wid += 1
            start += s
    return features


def extract_features(parse_output: ParseOutput) -> ItemFeatures:
    """Convert heterogeneous ParseOutput into ItemFeatures.

    Priority order per source:
    - items_raw → точечные товарные записи
    - tables → строки таблиц как кандидаты
    - pages_text → страницы/параграфы как текстовые кандидаты
    """
    items: List[ItemFeature] = []

    # 1) items_raw
    for idx, pi in enumerate(parse_output.items_raw or []):
        items.append(_feature_from_parsed_item(pi, idx))

    base = len(items)

    # 2) tables — избегаем дублей: если items_raw уже есть, таблицы не добавляем
    if not (parse_output.items_raw and len(parse_output.items_raw) > 0):
        for t_i, table in enumerate(parse_output.tables or []):
            items.extend(_features_from_table(table, base + t_i * 10_000))

    # 3) pages_text
    base = len(items)
    items.extend(_features_from_pages_text(parse_output.pages_text or [], base))

    return ItemFeatures(items=items, meta={"source": str(parse_output.source_path)})



