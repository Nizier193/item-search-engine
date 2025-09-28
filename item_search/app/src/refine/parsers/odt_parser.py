from __future__ import annotations

from pathlib import Path
from typing import List

from .models import ParseOutput, ParsedTable
from odf.opendocument import load
from odf import text as odf_text
from odf import table as odf_table


def parse_odt(path: Path) -> ParseOutput:
    """Parse ODT text and tables using odfpy (no try/except on import).

    Notes:
    - Requires 'odfpy' package.
    - Extracts paragraphs and basic table cells.
    """

    doc = load(str(path))

    # paragraphs
    paras: List[str] = []
    for p in doc.getElementsByType(odf_text.P):
        content = "".join(node.data for node in p.childNodes if hasattr(node, "data"))
        if content.strip():
            paras.append(content.strip())

    # tables
    parsed_tables: List[ParsedTable] = []
    for t in doc.getElementsByType(odf_table.Table):
        rows: List[List[str]] = []
        headers: List[str] = []
        for i, r in enumerate(t.getElementsByType(odf_table.TableRow)):
            cells = []
            for c in r.getElementsByType(odf_table.TableCell):
                texts = []
                for n in c.getElementsByType(odf_text.P):
                    seg = "".join(node.data for node in n.childNodes if hasattr(node, "data"))
                    if seg:
                        texts.append(seg)
                cells.append(" ".join(texts).strip())
            if i == 0:
                headers = cells
            else:
                rows.append(cells)
        parsed_tables.append(ParsedTable(headers=headers, rows=rows, meta={}))

    pages_text = ["\n".join(paras)] if paras else []
    return ParseOutput(source_path=path, pages_text=pages_text, tables=parsed_tables)


