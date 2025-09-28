from __future__ import annotations

from pathlib import Path


# Base directories
APP_ROOT = Path(__file__).resolve().parent
SRC_ROOT = APP_ROOT / "src"
CATALOGUES_ROOT = SRC_ROOT / "catalogues"


# Limits
MAX_LOADED_CATALOGS = 3
SEARCH_CACHE_SIZE = 2000
SEARCH_CACHE_TTL_SEC = 900


# Defaults (proxy to refine defaults if needed at runtime)
DEFAULT_TOP_K = 5
DEFAULT_THRESHOLD = 0.35
OCR_LANGUAGE = "rus+eng"


