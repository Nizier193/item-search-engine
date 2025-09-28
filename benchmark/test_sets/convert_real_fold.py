from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List


def load_catalog_jsonl(path: Path) -> List[Dict[str, object]]:
    items: List[Dict[str, object]] = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def write_jsonl(path: Path, rows: List[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')


def _normalize(s: str) -> str:
    return str(s).strip().lower()


def _resolve_hint_to_ids(hint_values: List[str], catalog: List[Dict[str, object]], gt_field: str) -> List[str]:
    # Build simple indices
    by_sku = { _normalize(it.get('sku', '')): str(it.get(gt_field, it.get('id'))) for it in catalog if it.get('sku') }
    titles = [ (_normalize(it.get('title','')), str(it.get(gt_field, it.get('id'))) ) for it in catalog ]

    resolved: List[str] = []
    for raw in hint_values:
        txt = _normalize(raw)
        if not txt:
            continue
        # Try SKU exact
        if txt in by_sku:
            resolved.append(by_sku[txt])
            continue
        # Try title contains
        for t_norm, ident in titles:
            if txt and (txt in t_norm or t_norm in txt):
                resolved.append(ident)
                break
    return resolved


def convert_real_fold(
    real_dir: Path,
    out_dir: Path,
    catalog_path: Path,
    gt_field: str = 'id',
) -> None:
    """Convert arbitrary real fold to our benchmark schema.

    Expects structure like:
      real_dir/
        odt/ or pdf/ with source documents
        raw_data/ with JSON annotations (optional), where entries contain expected ids/skus
    """
    # 1) copy/provide catalog path as reference
    catalog_items = load_catalog_jsonl(catalog_path)
    out_catalog = out_dir / 'catalog.jsonl'
    write_jsonl(out_catalog, catalog_items)

    # 2) discover target docs (pdf/odt/docx)
    doc_dir = real_dir / 'odt'
    if not doc_dir.exists():
        doc_dir = real_dir / 'pdf'
    if not doc_dir.exists():
        doc_dir = real_dir

    docs = []
    for ext in ('*.odt', '*.pdf', '*.docx'):
        docs.extend(doc_dir.glob(ext))

    # 3) load annotations if present
    gt_dir = real_dir / 'raw_data'
    hints = []
    if gt_dir.exists():
        for p in gt_dir.glob('*.json'):
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    obj = json.load(f)
                    hints.append((p.name, obj))
            except Exception:
                continue

    # 4) map hints by filename if possible (support list schema like [{"name":"...","params":"..."}])
    hint_map: Dict[str, List[str]] = {}
    for fname, obj in hints:
        # derive report name by number in transcription-X.json → report-X.pdf
        report_name = None
        if fname.startswith('transcription-') and fname.endswith('.json'):
            num = fname[len('transcription-'):-len('.json')]
            report_name = f'report-{num}.pdf'

        raw_values: List[str] = []
        if isinstance(obj, list):
            for entry in obj:
                if isinstance(entry, dict):
                    v = entry.get('name') or entry.get('params') or ''
                    if v:
                        raw_values.append(str(v))
        elif isinstance(obj, dict):
            # previous generic schema
            for k in ('expected', 'labels', 'gt', 'items'):
                if k in obj and isinstance(obj[k], list):
                    for it in obj[k]:
                        if isinstance(it, dict):
                            v = it.get(gt_field) or it.get('sku') or it.get('id')
                        else:
                            v = it
                        if v is not None:
                            raw_values.append(str(v))

            file_key = obj.get('file') or obj.get('filename') or obj.get('target')
            if file_key and not report_name:
                report_name = str(file_key)

        if not report_name:
            continue

        resolved_ids = _resolve_hint_to_ids(raw_values, catalog_items, gt_field)
        if resolved_ids:
            hint_map[report_name] = resolved_ids

    # 5) build queries.jsonl
    queries: List[Dict[str, object]] = []
    for doc in docs:
        # ground-truth by file name if available
        gt_vals = hint_map.get(doc.name, [])
        ground_truth = []
        if gt_vals:
            ground_truth.append({"expected_item_id": gt_vals[0]})

        queries.append(
            {
                "id": doc.stem,
                "target_path": str(doc.as_posix()),
                "references": [str(out_catalog.as_posix())],
                "ground_truth": ground_truth,
                "notes": "converted from real fold",
            }
        )

    write_jsonl(out_dir / 'queries.jsonl', queries)
    print(f"Converted {len(docs)} documents into {out_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description='Convert real fold to benchmark schema')
    parser.add_argument('--real-dir', type=str, required=True, help='Path to fold_real_X')
    parser.add_argument('--out', type=str, required=True, help='Output dataset fold path')
    parser.add_argument('--catalog', type=str, required=True, help='Path to reference catalog.jsonl')
    parser.add_argument('--gt-field', type=str, choices=['id', 'sku'], default='id')
    args = parser.parse_args()

    convert_real_fold(
        real_dir=Path(args.real_dir),
        out_dir=Path(args.out),
        catalog_path=Path(args.catalog),
        gt_field=args.gt_field,
    )


if __name__ == '__main__':
    main()


