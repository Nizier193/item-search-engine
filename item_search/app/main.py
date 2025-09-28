from __future__ import annotations

from pathlib import Path
import tempfile
from typing import Any, Dict, Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse

from item_search.app.models import (
    WarmupRequest,
    WarmupResponse,
    SearchRequest,
    SearchResponse,
    MatchDTO,
)
from item_search.app.services.catalog_manager import CatalogManager
from item_search.app.services.ocr import parse_any
from item_search.app.services.search_service import run_vector_search
from item_search.app.src.refine.extractors.features import extract_features


app = FastAPI(title="Item Search Service", version="0.1.0")
manager = CatalogManager()


@app.get("/healthz")
def healthz() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
def readyz(catalog_id: Optional[str] = None) -> Dict[str, Any]:
    if catalog_id is None:
        return {"status": "ok", "loaded_catalogs": manager.loaded_catalogs()}
    return {"status": "ok", "ready": manager.is_loaded(catalog_id)}


@app.post("/warmup", response_model=WarmupResponse)
def warmup(req: WarmupRequest) -> WarmupResponse:
    try:
        items = manager.warmup(req.catalog_id, req.references, limit_items=req.limit_items)
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return WarmupResponse(status="ok", catalog_id=req.catalog_id, items_indexed=items)


@app.post("/search", response_model=SearchResponse)
def search(req: SearchRequest) -> SearchResponse:
    if not manager.is_loaded(req.catalog_id):
        raise HTTPException(status_code=400, detail="Catalog is not warmed up. Call /warmup first.")
    result = manager.search_text(
        catalog_id=req.catalog_id,
        query_text=req.query_text,
        top_k=req.top_k,
        threshold=req.threshold,
    )
    return SearchResponse(
        catalog_id=req.catalog_id,
        query_text=req.query_text,
        best_match_id=result["best_match_id"],
        best_match_name=result.get("best_match_name"),
        best_score=result["best_score"],
        top_k=[MatchDTO(**m) for m in result["top_k"]],
    )


@app.post("/search/file", response_model=SearchResponse)
async def search_file(
    catalog_id: str = Form(...),
    file: UploadFile = File(...),
    top_k: Optional[int] = Form(None),
    threshold: Optional[float] = Form(None),
) -> SearchResponse:
    if not manager.is_loaded(catalog_id):
        raise HTTPException(status_code=400, detail="Catalog is not warmed up. Call /warmup first.")

    # Save to temp and parse (cross-platform)
    suffix = Path(file.filename or "uploaded").suffix
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = Path(tmp.name)

    try:
        parsed = parse_any(tmp_path)
        query_features = extract_features(parsed)
        state = manager._catalogs[catalog_id]  # internal access for performance
        result = run_vector_search(query_features, state.corpus, state.index, top_k, threshold)
        return SearchResponse(
            catalog_id=catalog_id,
            query_text=parsed.pages_text[0] if parsed.pages_text else "",
            best_match_id=result["best_match_id"],
            best_match_name=result.get("best_match_name"),
            best_score=result["best_score"],
            top_k=[MatchDTO(**m) for m in result["top_k"]],
        )
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass


@app.post("/parse/file")
async def parse_file(file: UploadFile = File(...)) -> JSONResponse:
    suffix = Path(file.filename or "uploaded").suffix
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = Path(tmp.name)
    try:
        parsed = parse_any(tmp_path)
        return JSONResponse({
            "pages": parsed.pages_text,
            "tables": len(parsed.tables),
            "source": str(parsed.source_path),
        })
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass
