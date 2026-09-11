# Simple FastAPI backend for TTB Label Verifier Prototype

from fastapi import FastAPI, File, HTTPException, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from PIL import Image, UnidentifiedImageError
import asyncio
import io
import logging
from pathlib import PurePath
import time
from typing import List, Optional

from .concurrency import ConcurrentProcessor
from .ocr import ocr_image
from .parsers import parse_fields

logger = logging.getLogger(__name__)

app = FastAPI(
    title="TTB Label Verifier Prototype",
    version="1.0.0",
    description="AI-powered alcohol label verification system",
)
PROCESSOR = ConcurrentProcessor(max_workers=4)
MAX_FILE_SIZE = 10 * 1024 * 1024
MAX_BATCH_SIZE = 20
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")


class ExtractResponse(BaseModel):
    fields: dict
    ocr_text: str
    latency_ms: float


class BatchExtractResponse(BaseModel):
    total_latency_ms: float
    count: int
    results: List[dict]


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "TTB Label Verifier"}


@app.post("/api/extract", response_model=ExtractResponse)
async def extract(file: UploadFile = File(...), application_brand: Optional[str] = Form(None)):
    start = time.time()
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    extension = PurePath(file.filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large")
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        image = Image.open(io.BytesIO(contents)).convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        logger.warning("Invalid image uploaded as %s: %s", file.filename, exc)
        raise HTTPException(status_code=400, detail=f"Invalid image: {exc}") from exc

    try:
        ocr_result = ocr_image(image)
    except (OSError, RuntimeError) as exc:
        logger.exception("OCR failed for %s", file.filename)
        raise HTTPException(status_code=500, detail="OCR processing failed") from exc
    full_text = ocr_result.get("text", "")
    try:
        fields = parse_fields(full_text, application_brand)
    except (TypeError, ValueError) as exc:
        logger.exception("Parsing failed for %s", file.filename)
        raise HTTPException(status_code=500, detail="Field parsing failed") from exc

    latency_ms = (time.time() - start) * 1000.0

    return {"fields": fields, "ocr_text": full_text, "latency_ms": latency_ms}


@app.post("/api/batch-extract", response_model=BatchExtractResponse)
async def batch_extract(
    files: List[UploadFile] = File(...),
    application_brand: Optional[List[str]] = Form(None),
):
    """Accept multiple files (files can be provided multiple times in form-data).
    Returns a JSON array of per-file results and total processing time.
    """
    if len(files) > MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Max {MAX_BATCH_SIZE} files per request",
        )
    if application_brand and len(application_brand) not in (1, len(files)):
        raise HTTPException(
            status_code=400,
            detail="Provide one application_brand or one brand per file",
        )

    total_start = time.time()

    def process_file(file: UploadFile, brand: Optional[str] = None) -> dict:
        item_start = time.time()
        contents = file.file.read()
        if not contents:
            return {"filename": file.filename, "error": "empty file", "latency_ms": 0}
        if len(contents) > MAX_FILE_SIZE:
            return {"filename": file.filename, "error": "file too large", "latency_ms": 0}
        try:
            image = Image.open(io.BytesIO(contents)).convert("RGB")
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            return {
                "filename": file.filename,
                "error": f"invalid image: {exc}",
                "latency_ms": (time.time() - item_start) * 1000.0,
            }

        ocr_result = ocr_image(image)
        full_text = ocr_result.get("text", "")
        fields = parse_fields(full_text, brand)
        item_latency = (time.time() - item_start) * 1000.0
        return {
            "filename": file.filename,
            "fields": fields,
            "ocr_text": full_text,
            "latency_ms": item_latency,
        }

    if application_brand and len(application_brand) == len(files):
        def process_with_brand(item: tuple[int, UploadFile]) -> dict:
            index, file = item
            return process_file(file, application_brand[index])

        results = await asyncio.to_thread(
            PROCESSOR.process_batch,
            enumerate(files),
            process_with_brand,
        )
    else:
        results = await asyncio.to_thread(PROCESSOR.process_batch, files, process_file)
    total_latency = (time.time() - total_start) * 1000.0
    return {"total_latency_ms": total_latency, "count": len(results), "results": results}
