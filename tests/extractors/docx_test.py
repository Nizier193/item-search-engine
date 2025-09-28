from pathlib import Path
from refine.parsers.docx_parser import parse_docx
from refine.extractors.features import extract_features

docx_path = Path("samples/docx.docx")
po = parse_docx(docx_path)
feats = extract_features(po)
print(len(feats.items), feats.items[0])