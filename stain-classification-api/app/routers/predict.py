from fastapi import APIRouter, File, UploadFile, HTTPException
from PIL import Image
import io

from app.schemas.prediction import PredictResponse, Detection, BoundingBox
from app.services.detector import detector

router = APIRouter()


@router.post("/predict", response_model=PredictResponse)
async def predict(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="업로드 파일은 이미지여야 합니다.")

    contents = await file.read()
    try:
        image = Image.open(io.BytesIO(contents))
    except Exception:
        raise HTTPException(status_code=400, detail="이미지를 읽을 수 없습니다.")

    raw_detections, inference_ms = detector.predict(image)

    detections = [
        Detection(
            label=d["label"],
            confidence=d["confidence"],
            bbox=BoundingBox(**d["bbox"]),
        )
        for d in raw_detections
    ]
    return PredictResponse(detections=detections, inference_time_ms=round(inference_ms, 2))
