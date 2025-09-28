# Benchmarking

## Dataset schema (JSONL)

Place a JSONL file under `datasets/baseline/queries.jsonl` with entries:

```
{
  "id": "query_0001",
  "target_path": "path/to/input/file.pdf|.docx|.odt",
  "references": ["path/to/ref1.jsonl", "path/to/ref2.csv"],
  "ground_truth": [
    { "query_key": "<optional query item id>", "expected_item_id": "<reference id/sku>" }
  ],
  "notes": "optional"
}
```

- `target_path`: документ, который парсим (OCR/DOCX/ODT).
- `references`: список референсных каталогов (json/jsonl/csv/xlsx) для поиска.
- `ground_truth`: список эталонных ответов. Минимально достаточно одного объекта с `expected_item_id` из каталога. Если у вас разметка по нескольким позициям в документе — заполняйте массивом.

Alternative compact schema (per-item): `datasets/baseline/items.jsonl`
```
{
  "query_text": "строка-сегмент из документа",
  "references": ["path/to/ref.jsonl"],
  "expected_item_id": "sku|id"
}
```

## Metrics
- precision@1, recall@k, MRR, hit rate, average rank.

## Running
Provide a small runner that loads dataset, runs pipeline to get SearchResult[top_k], and computes metrics.

