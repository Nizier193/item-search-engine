from __future__ import annotations

# Placeholder for FAISS adapter; keeps interface but no dependency at baseline
from .models import VectorIndex


class FaissIndex(VectorIndex):  # type: ignore[misc]
    def __init__(self):
        raise NotImplementedError("FAISS adapter not implemented in baseline")


