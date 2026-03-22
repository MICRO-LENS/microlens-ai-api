# teeth-api

치아 이물질(stuck_food) 탐지 API입니다. YOLOv8 ONNX 모델을 CPU에서 추론합니다.

## 모델

- 아키텍처: YOLOv8
- 런타임: onnxruntime (CPU)
- 클래스: `stuck_food`

> GPU(VRAM) 사용률이 2% 미만으로 측정되어 CPU 환경으로 전환했습니다.

## 실행

```bash
cp .env.example .env
docker-compose up --build
```

## 환경 변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `MODEL_PATH` | `models/teeth_best.onnx` | ONNX 모델 경로 |
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
      "label": "stuck_food",
      "confidence": 0.87,
      "bbox": { "x1": 100, "y1": 200, "x2": 300, "y2": 400 }
    }
  ],
  "inference_time_ms": 42.5
}
```

### `GET /health`

서버 상태를 반환합니다.
