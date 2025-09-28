from __future__ import annotations

from pathlib import Path
from typing import List

from .parsers.models import ParseOutput
from .parsers.ocr_parser import parse_ocr
from .parsers.docx_parser import parse_docx
from .parsers.tabular_parser import parse_tabular
from .parsers import parse_odt  # type: ignore[attr-defined]
from .extractors.features import extract_features
from .extractors.models import ItemFeatures
from .searchers.models import SearchResult, search
from .searchers.cosine_index import CosineIndex
from .config import TOP_K, SIMILARITY_THRESHOLD
from .io.excel import to_excel


#
from tqdm import tqdm

def run_pipeline(
    target_pdf: Path,
    reference_tables: List[Path],
    dest_table: Path,
) -> Path:
    """End-to-end baseline pipeline (stubbed internals)."""

    parsed: ParseOutput
    if target_pdf.suffix.lower() == '.pdf':
        parsed = parse_ocr(target_pdf)

    elif target_pdf.suffix.lower() == '.docx':
        parsed = parse_docx(target_pdf)

    elif target_pdf.suffix.lower() == '.odt':
        parsed = parse_odt(target_pdf)

    else:
        parsed = parse_ocr(target_pdf)

    # 2) parse references and merge
    ref_parsed: List[ParseOutput] = []
    for p in reference_tables:
        ref_parsed.append(parse_tabular(p))

    # 3) extract features
    print("Вытаскиваем фичи из query")
    query_features: ItemFeatures = extract_features(parsed)

    # Для каждого из каталогов выгружаем его товары
    ref_features_list: List[ItemFeatures] = []
    for rp in tqdm(ref_parsed, desc="Вытаскиваем фичи из рефки", total=len(ref_parsed)):
        ref_features_list.append(extract_features(rp))

    # Сливаем рефку воедино
    merged_ref = ItemFeatures(items=[it for rf in ref_features_list for it in rf.items])

    # 4) search with TF-IDF baseline
    index = CosineIndex()
    results: List[SearchResult] = search(
        query=query_features,
        reference=merged_ref,
        index=index,
        top_k=TOP_K,
        threshold=SIMILARITY_THRESHOLD,
    )

    # 5) export
    return to_excel(results, dest_table)