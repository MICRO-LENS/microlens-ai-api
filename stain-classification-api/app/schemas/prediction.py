from pydantic import BaseModel
from typing import List


class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


class Detection(BaseModel):
    label: str
    confidence: float
    bbox: BoundingBox


class PredictResponse(BaseModel):
    detections: List[Detection]
    inference_time_ms: float
