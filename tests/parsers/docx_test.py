from pathlib import Path
from refine.parsers.docx_parser import parse_docx

docx_path = Path("samples/docx.docx")
out = parse_docx(docx_path)
print("tables:", len(out.tables))
if out.tables:
    print(out.tables[0].headers)
    print(out.tables[0].rows)