from pydantic import BaseModel
from typing import List, Dict, Any


class Box(BaseModel):
    text: str
    conf: int
    box: List[int]


class ExtractResponse(BaseModel):
    fields: Dict[str, Any]
    ocr_text: str
    latency_ms: float
