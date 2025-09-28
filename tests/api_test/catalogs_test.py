import os
import requests

BASE = os.environ.get("API_BASE", "http://localhost:8000")


def test_warmup_ok():
    payload = {
        "catalog_id": "test-cat-1",
        "references": ["test_catalogue.jsonl"],
        "limit_items": 5000,
    }
    r = requests.post(f"{BASE}/warmup", json=payload, timeout=120)
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["items_indexed"] >= 0


def test_warmup_missing_catalog_file():
    payload = {
        "catalog_id": "test-cat-missing",
        "references": ["no_such.jsonl"],
        "limit_items": 5000,
    }
    r = requests.post(f"{BASE}/warmup", json=payload, timeout=60)
    # Expect 500 or 400 depending on error handling
    assert r.status_code in (400, 500)


def test_warmup_five_catalogs_limit():
    # Depending on implementation, we limit to 3 loaded catalogs
    # Try to load 5 distinct ids and expect failures after the cap
    failures = 0
    for i in range(5):
        payload = {"catalog_id": f"bulk-{i}", "references": ["catalog.jsonl"], "limit_items": 5000}
        r = requests.post(f"{BASE}/warmup", json=payload, timeout=120)
        if r.status_code not in (200, 201):
            failures += 1
    assert failures >= 2  # at least two should fail if cap is 3


