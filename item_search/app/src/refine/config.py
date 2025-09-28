from __future__ import annotations

# minimal config placeholders

OCR_LANGUAGE = "rus+eng"
TOP_K = 5
SIMILARITY_THRESHOLD = 0.35  # baseline threshold for "similar enough"

# Windowing for long text
WINDOW_SIZE = 60
WINDOW_STRIDE = 30

# Query TF clipping
QUERY_TF_CLIP = 2

# DF pruning (vocab)
MIN_DF = 2
MAX_DF_RATIO = 0.7  # drop tokens that appear in >70% of documents

# Field boosts (corpus)
NAME_BOOST = 3.0
SKU_FIELD_BOOST = 3.0
BRAND_BOOST = 1.5

# Anchors (query)
SKU_ANCHOR_BOOST = 3.0

# Fuzzy fallbacks
FUZZY_SKU_THRESHOLD = 0.85
FUZZY_NAME_THRESHOLD = 0.6



