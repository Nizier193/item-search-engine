from __future__ import annotations

from pathlib import Path
from typing import List

from item_search.app.src.refine.parsers.ocr_parser import parse_ocr
from item_search.app.src.refine.parsers.docx_parser import parse_docx
from item_search.app.src.refine.parsers.odt_parser import parse_odt
from item_search.app.src.refine.parsers.models import ParseOutput


def parse_any(path: Path) -> ParseOutput:
    suf = path.suffix.lower()
    if suf in (".jpg", ".jpeg", ".png"):
        return parse_ocr(path)
    if suf == ".pdf":
        return parse_ocr(path)
    if suf == ".docx":
        return parse_docx(path)
    if suf == ".odt":
        return parse_odt(path)
    if suf == ".txt":
        text = Path(path).read_text(encoding="utf-8", errors="ignore")
        return ParseOutput(source_path=path, pages_text=[text])
    # default to OCR
    return parse_ocr(path)


