from __future__ import annotations

import argparse
import json
import os
import random
import string
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict

from odf.opendocument import OpenDocumentText
from odf import text as odf_text


@dataclass
class CatalogItem:
    id: str
    title: str
    description: str
    price: float
    sku: str
    marketplace: str = "synthetic"


WORDS = (
    "арбуз банан огурец помидор капуста морковь документ таблица система каталог индекс поиск цена бренд артикул модель",
    "поставка заявка спецификация контракт позиция упаковка размер материал цвет плотность объем вес длина ширина высота",
    "параграф текст данные обработка извлечение фича токен окно страница изображение скан ocr нормализация сегментация",
)


def _rnd_digits(n: int, rng: random.Random) -> str:
    return "".join(rng.choice(string.digits) for _ in range(n))


def _rnd_token(rng: random.Random) -> str:
    base = rng.choice(" ".join(WORDS).split())
    if rng.random() < 0.2:
        return base.capitalize()
    return base


def make_catalog(n: int, rng: random.Random) -> List[CatalogItem]:
    items: List[CatalogItem] = []
    for i in range(n):
        sku = _rnd_digits(6, rng)
        title = f"Товар {i+1} SKU {sku}"
        desc = f"Синтетическое описание для товара {i+1} со SKU {sku}."
        price = round(rng.uniform(100.0, 50000.0), 2)
        items.append(CatalogItem(id=_rnd_digits(7, rng), title=title, description=desc, price=price, sku=sku))
    return items


def write_catalog_jsonl(items: List[CatalogItem], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for it in items:
            obj: Dict[str, object] = {
                "id": it.id,
                "title": it.title,
                "description": it.description,
                "price": it.price,
                "sku": it.sku,
                "marketplace": it.marketplace,
            }
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def make_odt_with_mentions(out_path: Path, mentions: List[str], filler_words: int, rng: random.Random) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc = OpenDocumentText()

    # Compose a long paragraph with filler + mentions inserted at random positions
    tokens: List[str] = []
    for _ in range(filler_words):
        tokens.append(_rnd_token(rng))
        if rng.random() < 0.02:
            tokens.append(",")

    # Insert mentions
    insert_positions = sorted(rng.sample(range(10, max(11, len(tokens) - 10)), k=min(len(mentions), max(1, len(mentions)))))
    for pos, mention in zip(insert_positions, mentions):
        tokens.insert(pos, mention)

    # Split into paragraphs of ~60-100 tokens
    cur = 0
    while cur < len(tokens):
        span = rng.randint(60, 100)
        chunk = tokens[cur : min(cur + span, len(tokens))]
        p = odf_text.P(text=" ".join(chunk))
        doc.text.addElement(p)
        cur += span

    doc.save(str(out_path))


def write_queries_jsonl(out_path: Path, queries: List[Dict[str, object]]) -> None:
    with open(out_path, "w", encoding="utf-8") as f:
        for q in queries:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")


def generate_fold(
    out_dir: Path,
    num_items: int = 50,
    num_queries: int = 20,
    filler_words: int = 1000,
    min_mentions: int = 1,
    max_mentions: int = 3,
    seed: int = 42,
    gt_field: str = "id",  # or "sku"
) -> None:
    rng = random.Random(seed)

    # 1) catalog
    catalog_items = make_catalog(num_items, rng)
    catalog_path = out_dir / "catalog.jsonl"
    write_catalog_jsonl(catalog_items, catalog_path)

    # 2) ODT queries and ground-truth
    odt_dir = out_dir / "odt"
    queries: List[Dict[str, object]] = []
    for i in range(num_queries):
        k = rng.randint(min_mentions, max_mentions)
        picked = rng.sample(catalog_items, k=k)

        # mentions: use product titles (can mix with SKU variants)
        mentions = []
        for it in picked:
            choice = rng.random()
            if choice < 0.7:
                mentions.append(it.title)
            else:
                mentions.append(f"SKU {it.sku}")

        odt_path = odt_dir / f"query_{i+1:03d}.odt"
        make_odt_with_mentions(odt_path, mentions, filler_words=filler_words, rng=rng)

        # ground-truth: take the first picked as primary label (baseline runner supports single label)
        primary = picked[0]
        expected_value = getattr(primary, gt_field)
        queries.append(
            {
                "id": f"q{i+1:03d}",
                "target_path": str(odt_path.as_posix()),
                "references": [str(catalog_path.as_posix())],
                "ground_truth": [{"expected_item_id": str(expected_value)}],
                "notes": f"mentions: {[getattr(p, gt_field) for p in picked]}",
            }
        )

    write_queries_jsonl(out_dir / "queries.jsonl", queries)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic fold with ODT queries and catalog.jsonl")
    parser.add_argument("--out", type=str, default="datasets/fold_1", help="Output directory for the fold")
    parser.add_argument("--num-items", type=int, default=50)
    parser.add_argument("--num-queries", type=int, default=20)
    parser.add_argument("--filler-words", type=int, default=1000)
    parser.add_argument("--min-mentions", type=int, default=1)
    parser.add_argument("--max-mentions", type=int, default=3)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--gt-field", type=str, choices=["id", "sku"], default="id", help="Which field to use in ground_truth")
    args = parser.parse_args()

    out_dir = Path(args.out)
    generate_fold(
        out_dir=out_dir,
        num_items=args.num_items,
        num_queries=args.num_queries,
        filler_words=args.filler_words,
        min_mentions=args.min_mentions,
        max_mentions=args.max_mentions,
        seed=args.seed,
        gt_field=args.gt_field,
    )
    print(f"Fold generated at: {out_dir}")


if __name__ == "__main__":
    main()