from .ocr_parser import parse_ocr
from .docx_parser import parse_docx
from .tabular_parser import parse_tabular
from .odt_parser import parse_odt

__all__ = [
    "parse_ocr",
    "parse_docx",
    "parse_tabular",
    "parse_odt",
]


