# Simple FastAPI backend for TTB Label Verifier Prototype

from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image
import io
import time

from app.ocr import ocr_image
from app.parsers import parse_fields

app = FastAPI(title="TTB Label Verifier Prototype")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ExtractResponse(BaseModel):
    fields: dict
    ocr_text: str
    latency_ms: float


@app.post("/api/extract", response_model=ExtractResponse)
async def extract(file: UploadFile = File(...), application_brand: str | None = Form(None)):
    start = time.time()
    contents = await file.read()
    image = Image.open(io.BytesIO(contents)).convert("RGB")

    ocr_result = ocr_image(image)
    full_text = ocr_result.get("text", "")
    boxes = ocr_result.get("boxes", [])

    fields = parse_fields(full_text, application_brand)

    latency_ms = (time.time() - start) * 1000.0

    return {"fields": fields, "ocr_text": full_text, "latency_ms": latency_ms}
