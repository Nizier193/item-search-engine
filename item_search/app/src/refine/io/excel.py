from __future__ import annotations

from pathlib import Path
from typing import List

from ..searchers.models import SearchResult


def to_excel(results: List[SearchResult], dest: Path) -> Path:
    """Write results to CSV baseline with required fields."""
    dest = dest.with_suffix('.csv')
    with open(dest, 'w', encoding='utf-8') as f:
        f.write('Needed Item,Found Item,Score,Price,SKU,Source\n')
        for r in results:
            needed = r.query_item_id
            found = r.best_match_id or ''
            score = f"{r.best_score:.6f}" if r.best_score else ''

            # Try to pick meta of best_match from top_k
            price = ''
            sku = ''
            source = ''
            if r.best_match_id:
                for m in r.top_k:
                    if m.item_id == r.best_match_id:
                        price = str(m.meta.get('price', ''))
                        sku = str(m.meta.get('sku', ''))
                        source = str(m.meta.get('marketplace', m.meta.get('source', '')))
                        break

            f.write(f"{needed},{found},{score},{price},{sku},{source}\n")
    return dest


