# Simple FastAPI backend for TTB Label Verifier Prototype

from fastapi import FastAPI, File, HTTPException, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from PIL import Image, UnidentifiedImageError
import asyncio
import io
import time
from typing import List, Optional

from .concurrency import ConcurrentProcessor
from .ocr import ocr_image
from .parsers import parse_fields

app = FastAPI(title="TTB Label Verifier Prototype")
PROCESSOR = ConcurrentProcessor(max_workers=4)
MAX_FILE_SIZE = 10 * 1024 * 1024
MAX_BATCH_SIZE = 20

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


@app.post("/api/extract", response_model=ExtractResponse)
async def extract(file: UploadFile = File(...), application_brand: Optional[str] = Form(None)):
    start = time.time()
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large")

    try:
        image = Image.open(io.BytesIO(contents)).convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"Invalid image: {exc}") from exc

    ocr_result = ocr_image(image)
    full_text = ocr_result.get("text", "")
    boxes = ocr_result.get("boxes", [])

    fields = parse_fields(full_text, application_brand)

    latency_ms = (time.time() - start) * 1000.0

    return {"fields": fields, "ocr_text": full_text, "latency_ms": latency_ms}


@app.post("/api/batch-extract")
async def batch_extract(files: List[UploadFile] = File(...)):
    """Accept multiple files (files can be provided multiple times in form-data).
    Returns a JSON array of per-file results and total processing time.
    """
    if len(files) > MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Max {MAX_BATCH_SIZE} files per request",
        )

    total_start = time.time()

    def process_file(file: UploadFile) -> dict:
        item_start = time.time()
        contents = file.file.read()
        try:
            image = Image.open(io.BytesIO(contents)).convert("RGB")
        except (OSError, ValueError):
            return {"filename": file.filename, "error": "invalid image"}

        ocr_result = ocr_image(image)
        full_text = ocr_result.get("text", "")
        fields = parse_fields(full_text, None)
        item_latency = (time.time() - item_start) * 1000.0
        return {
            "filename": file.filename,
            "fields": fields,
            "ocr_text": full_text,
            "latency_ms": item_latency,
        }

    results = await asyncio.to_thread(PROCESSOR.process_batch, files, process_file)
    total_latency = (time.time() - total_start) * 1000.0
    return {"total_latency_ms": total_latency, "count": len(results), "results": results}
