# microlens-ai-api

MicroLens 프로젝트의 AI 백엔드 저장소입니다.
FastAPI 기반의 AI 추론 서비스 3개를 멀티 레포 구조로 관리합니다.

---

## 서비스 구성

| 서비스 | 경로 | 역할 |
|--------|------|------|
| stain-classification-api | `stain-classification-api/` | 의류 얼룩 분류 (beverage / food / pen) |
| stain-detection-api | `stain-detection-api/` | 의류 얼룩 탐지 (위치 + 클래스) |
| teeth-api | `teeth-api/` | 치아 이물질 탐지 (stuck_food) |

---

## 디렉토리 구조

```
microlens-ai-api/
├── stain-classification-api/
├── stain-detection-api/
└── teeth-api/
    ├── app/
    │   ├── routers/predict.py      # POST /predict 엔드포인트
    │   ├── schemas/prediction.py   # 요청/응답 Pydantic 스키마
    │   └── services/detector.py    # ONNX 추론 로직
    ├── models/                     # .onnx 모델 파일 (Git 제외)
    ├── main.py                     # FastAPI 앱 진입점
    ├── requirements.txt            # 운영용 (onnxruntime-gpu)
    ├── requirements-dev.txt        # 개발용 (onnxruntime CPU)
    ├── Dockerfile                  # 멀티 스테이지 빌드 + Non-root 보안
    ├── docker-compose.yml          # 로컬 Docker 빌드 및 볼륨 마운트
    ├── .env.example                # 환경변수 템플릿 (Git 포함)
    └── .gitignore                  # .env, *.onnx Git 제외
```

---

## API 엔드포인트

모든 서비스 공통:

```
POST /predict    — 이미지 업로드 후 탐지 결과 반환
GET  /health     — 서버 상태 확인
```

얼룩탐지모델 응답 예:
```json
{
  "detections": [
    {
      "label": "beverage",
      "confidence": 0.71,
      "bbox": { "x1": 319.28, "y1": 636.86, "x2": 539.09, "y2": 993.62 }
    }
  ],
  "inference_time_ms": 456.32
}
```

---

## 기술 스택

| 분류 | 기술 |
|------|------|
| 언어 | Python 3.10 |
| 웹 프레임워크 | FastAPI |
| 모델 서빙 | ONNX Runtime(로컬에서만, 서버에서는 gpu 사용) |
| 컨테이너 | Docker |
| 이미지 레지스트리 | AWS ECR |

---

## 로컬 개발

> 가상환경은 루트에서 한 번만 생성. 각 API의 `requirements-dev.txt`는 동일한 패키지 구성입니다.

```powershell
# 루트에서 가상환경 생성 (최초 1회)
py -3.10 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel

# 개발용 의존성 설치 (CPU 기반)
pip install -r stain-classification-api/requirements-dev.txt
```

각 API 실행:
```powershell
cd stain-classification-api && python main.py
cd stain-detection-api     && python main.py
cd teeth-api               && python main.py
```

실행 후 확인:
- 헬스체크: `http://127.0.0.1:8000/health`
- Swagger UI: `http://127.0.0.1:8000/docs`

---

## 로컬 Docker 빌드 검증

> **목적**: Dockerfile 문법, pip install, PYTHONPATH 설정 사전 확인.
> `docker run`은 불필요 — 모델 마운트 및 GPU는 AWS 환경에서 설정.

```bash
# WSL 터미널 — 각 API 폴더에서 실행
cp .env.example .env
docker compose build
```

---

## 모델 파일 관리

`.onnx` 파일은 용량이 크므로 Git에 커밋하지 않습니다.

- **로컬**: 각 API의 `models/` 폴더에 직접 배치
- **운영(AWS)**: 컨테이너 실행 시 외부에서 마운트 (AWS 인프라 단계에서 설정)

---

## 관련 저장소

- [microlens-infra](../microlens-infra) — AWS 인프라 및 Kubernetes 배포
- [microlens-android](../microlens-android) — Android 클라이언트 앱
