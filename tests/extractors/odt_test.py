from pathlib import Path
from refine.parsers.odt_parser import parse_odt
from refine.extractors.features import extract_features

odt_path = Path("samples/odt.odt")
po = parse_odt(odt_path)
feats = extract_features(po)
print(feats.items)