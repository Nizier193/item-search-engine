import os
import requests

BASE = os.environ.get("API_BASE", "http://localhost:8000")


def _ensure_warmup():
    r = requests.get(f"{BASE}/readyz?catalog_id=smoke", timeout=10)
    ready = r.status_code == 200 and r.json().get("ready") is True
    if not ready:
        payload = {"catalog_id": "smoke", "references": ["test_catalogue.jsonl"], "limit_items": 5000}
        requests.post(f"{BASE}/warmup", json=payload, timeout=120).raise_for_status()


def test_search_pen_paper_eraser():
    _ensure_warmup()
    samples = [
        ("синяя ручка", ["руч", "pen"]),
        ("бумага a4", ["бумага", "paper", "a4"]),
        ("ластик", ["ласт", "eraser"]),
    ]
    for query, must_keywords in samples:
        r = requests.post(
            f"{BASE}/search",
            json={"catalog_id": "smoke", "query_text": query, "top_k": 5},
            timeout=30,
        )
        assert r.status_code == 200
        data = r.json()
        # Ensure we have both id and readable name
        assert "best_match_id" in data
        assert "best_match_name" in data
        # Validate top_k has names in meta
        for m in data.get("top_k", []):
            meta = m.get("meta", {})
            assert "name" in meta
        # Heuristic check: best_match_name contains any of required keywords
        name = (data.get("best_match_name") or "").lower()
        assert any(k in name for k in must_keywords), f"Query '{query}' got name '{name}'"


