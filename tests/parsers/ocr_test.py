from pathlib import Path
from refine.parsers.ocr_parser import parse_ocr

pdf_path = Path("samples/mvd.pdf")

out = parse_ocr(pdf_path)
print(len(out.pages_text), "pages")
print(out.pages_text[0][:400])