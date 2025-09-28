import io
import os
import requests

BASE = os.environ.get("API_BASE", "http://localhost:8000")


def _post_file(endpoint: str, filename: str, content: bytes, content_type: str = "application/octet-stream"):
    files = {"file": (filename, io.BytesIO(content), content_type)}
    return requests.post(f"{BASE}{endpoint}", files=files, timeout=30)


def test_parse_empty_file():
    r = _post_file("/parse/file", "empty.txt", b"")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data.get("pages"), list)


def test_parse_broken_file():
    # random bytes as pdf
    r = _post_file("/parse/file", "broken.pdf", b"%PDF-xxx\x00\xff\x00garbage")
    # service should not 500; accept 200 with empty pages or 400 bad request
    assert r.status_code in (200, 400)


def test_parse_invalid_chars():
    content = "абв\udcffгдеж".encode("utf-8", errors="ignore")
    r = _post_file("/parse/file", "weird.txt", content, "text/plain")
    assert r.status_code == 200


def test_parse_no_extension():
    r = _post_file("/parse/file", "file", b"some text")
    assert r.status_code == 200


def test_parse_wrong_extension():
    r = _post_file("/parse/file", "file.xyz", b"some text")
    # default OCR path should still handle as OCR/text
    assert r.status_code in (200, 400)


