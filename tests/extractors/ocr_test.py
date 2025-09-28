from pathlib import Path
from refine.parsers.ocr_parser import parse_ocr
from refine.extractors.features import extract_features

pdf_path = Path("samples/mvd.pdf")
po = parse_ocr(pdf_path)
feats = extract_features(po)
print(len(feats.items))
print(feats.items[0].text_repr[:200])