from __future__ import annotations

from pathlib import Path
from typing import List

from pdf2image import convert_from_path
from .models import ParseOutput, ParsedTable
from ..config import OCR_LANGUAGE
import pytesseract
from PIL import Image
import os

# Respect environment override for Tesseract binary; otherwise use system default (PATH)
_tess_cmd = os.getenv("TESSERACT_CMD")
if _tess_cmd:
    pytesseract.pytesseract.tesseract_cmd = _tess_cmd


def _ocr_images_to_text(images: List["Image.Image"]) -> List[str]:  # type: ignore[name-defined]
    texts: List[str] = []
    for img in images:
        text = pytesseract.image_to_string(img, lang=OCR_LANGUAGE)
        texts.append(text or "")
    return texts


def _pdf_to_images(path: Path) -> List["Image.Image"]:  # type: ignore[name-defined]
    # On Windows, pdf2image may require explicit poppler path; read from env if provided
    poppler_path = os.getenv("POPPLER_PATH")
    if poppler_path:
        images = convert_from_path(str(path), poppler_path=poppler_path)
    else:
        images = convert_from_path(str(path))
    return images


def parse_ocr(path: Path) -> ParseOutput:
    """Run OCR over scanned PDF or images.

    - If input is PDF, convert pages to images, then OCR.
    - If input is an image, OCR directly.
    """
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        images = _pdf_to_images(path)
        pages_text = _ocr_images_to_text(images)
    else:
        image = Image.open(str(path))
        pages_text = _ocr_images_to_text([image])

    return ParseOutput(source_path=path, pages_text=pages_text, tables=[], items_raw=[])

