from pathlib import Path
from refine.parsers.odt_parser import parse_odt

odt_path = Path("samples/odt.odt")
out = parse_odt(odt_path)
print("pages_text:", out.items_raw)
print("tables:", len(out.tables))