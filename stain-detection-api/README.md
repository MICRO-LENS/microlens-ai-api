# stain-detection-api

얼룩 탐지 API입니다. YOLOv12 ONNX 모델을 CPU에서 추론합니다.

## 모델

- 아키텍처: YOLOv12
- 런타임: onnxruntime (CPU)
- 클래스: `stain`

> GPU(VRAM) 사용률이 2% 미만으로 측정되어 CPU 환경으로 전환했습니다.

## 실행

```bash
cp .env.example .env
docker-compose up --build
```

## 환경 변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `MODEL_PATH` | `models/stain_detection_best.onnx` | ONNX 모델 경로 |
| `CONF_THRESHOLD` | `0.25` | 신뢰도 임계값 |
| `IOU_THRESHOLD` | `0.25` | NMS IoU 임계값 |

## API

### `POST /predict`

이미지 파일을 업로드하면 탐지 결과를 반환합니다.

**Request:** `multipart/form-data`, 필드명 `file`

**Response:**
```json
{
  "detections": [
    {
      "label": "stain",
      "confidence": 0.91,
      "bbox": { "x1": 50, "y1": 80, "x2": 200, "y2": 250 }
    }
  ],
  "inference_time_ms": 38.2
}
```

### `GET /health`

서버 상태를 반환합니다.
