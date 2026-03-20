# MicroLens AI API

MicroLens 프로젝트의 AI 백엔드 저장소입니다.
FastAPI 기반의 AI 추론 서비스 3개를 멀티 레포 구조로 관리합니다.

## 서비스 구성

| 서비스 | 경로 | 역할 | 모델 파일 | 런타임 |
|--------|------|------|-----------|--------|
| stain-classification-api | `stain-classification-api/` | 의류 얼룩 분류 (beverage / food / pen) | `stain_classification_best.onnx` | CPU |
| stain-detection-api | `stain-detection-api/` | 의류 얼룩 탐지 (위치 + 클래스) | `stain_detection_best.onnx` | GPU |
| teeth-api | `teeth-api/` | 치아 이물질 탐지 (stuck_food) | `teeth_best.onnx` | GPU |

> `stain-classification-api`는 운영 환경에서도 CPU(`onnxruntime`) 기반으로 동작합니다.
> `stain-detection-api`, `teeth-api`는 운영 환경에서 GPU(`onnxruntime-gpu`, CUDA 12.4.1 + cuDNN 9) 기반으로 동작합니다.

## 디렉토리 구조

```
microlens-ai-api/
├── Jenkinsfile                 # CI/CD 파이프라인 (ECR 빌드, 매니페스트 업데이트)
├── ai-api-workflow.md          # 로컬 개발 및 검증 워크플로우 상세 문서
├── stain-classification-api/
├── stain-detection-api/
└── teeth-api/
    ├── app/
    │   ├── routers/predict.py      # POST /predict 엔드포인트
    │   ├── schemas/prediction.py   # 요청/응답 Pydantic 스키마
    │   └── services/detector.py    # YOLOv8 ONNX 추론 로직
    ├── models/                     # .onnx 모델 파일 (Git 제외)
    ├── main.py                     # FastAPI 앱 진입점
    ├── requirements.txt            # 운영용 의존성
    ├── requirements-dev.txt        # 개발용 의존성 (onnxruntime CPU)
    ├── Dockerfile                  # 멀티 스테이지 빌드 + Non-root 보안
    ├── docker-compose.yml          # 로컬 Docker 빌드 및 볼륨 마운트
    ├── .env.example                # 환경변수 템플릿 (Git 포함)
    └── .gitignore                  # .env, *.onnx Git 제외
```

## API 엔드포인트

모든 서비스 공통:

```
POST /predict    — 이미지 업로드 후 탐지/분류 결과 반환
GET  /health     — 서버 상태 확인
```

### 요청 형식

- **Method**: POST
- **Endpoint**: `/predict`
- **Content-Type**: `multipart/form-data`
- **Body**: `file` (이미지 파일)

### 응답 형식

```json
{
  "detections": [
    {
      "label": "beverage",
      "confidence": 0.71,
      "bbox": {
        "x1": 319.28,
        "y1": 636.86,
        "x2": 539.09,
        "y2": 993.62
      }
    }
  ],
  "inference_time_ms": 456.32
}
```

### 환경 변수 (`.env.example` 기준)

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `MODEL_PATH` | 서비스별 상이 | ONNX 모델 파일 경로 |
| `CONF_THRESHOLD` | `0.25` | 신뢰도 임계값 |
| `IOU_THRESHOLD` | `0.45` | NMS IoU 임계값 |

## 기술 스택

| 분류 | 기술 |
|------|------|
| 언어 | Python 3.10 |
| 웹 프레임워크 | FastAPI 0.111.0 |
| 모델 | YOLOv8 (ONNX 포맷, opset 17, dynamic shape) |
| 모델 서빙 | ONNX Runtime 1.19.2 (CPU: 로컬·분류 API, GPU: 탐지·치아 API) |
| 컨테이너 | Docker (멀티 스테이지 빌드, Non-root 실행) |
| 이미지 레지스트리 | AWS ECR |
| CI/CD | Jenkins |
| 오케스트레이션 | Kubernetes + Kustomize |

## CI/CD 파이프라인

GitHub 푸시 시 Jenkins가 자동 실행됩니다.

### 파이프라인 단계

1. **ECR Login** — AWS ECR 로그인
2. **Build & Push** — 3개 API를 병렬로 Docker 이미지 빌드 및 ECR 푸시
3. **Update Manifests** — `microlens-infra` 리포지토리의 Kustomize 매니페스트 이미지 태그 업데이트 및 푸시

### 환경 변수

| 변수 | 값 |
|------|----|
| `AWS_REGION` | `ap-northeast-2` |
| `IMAGE_TAG` | Git 커밋 해시 앞 7자리 |
| `INFRA_REPO` | `https://github.com/MICRO-LENS/microlens-infra.git` |
| Kustomize 경로 | `k8s/overlays/phase2/kustomization.yaml` |

---

# 로컬 개발

> 상세 워크플로우는 [`ai-api-workflow.md`](ai-api-workflow.md)를 참고하세요.

### 모델 파일 준비

`.onnx` 파일은 Git에 포함되지 않습니다. 각 API의 `models/` 폴더에 직접 배치하세요.

```
stain-classification-api/models/stain_classification_best.onnx
stain-detection-api/models/stain_detection_best.onnx
teeth-api/models/teeth_best.onnx
```

- **로컬**: `models/` 폴더에 직접 배치
- **운영(AWS)**: 컨테이너 실행 시 외부 볼륨으로 마운트

### Python 가상환경 (로컬 실행)

```bash
# 루트에서 가상환경 생성 (최초 1회)
python3.10 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
pip install --upgrade pip setuptools wheel

# 개발용 의존성 설치 (CPU 기반 ONNX Runtime)
pip install -r stain-classification-api/requirements-dev.txt
```

각 API 실행:

```bash
cd stain-classification-api && python main.py
cd stain-detection-api     && python main.py
cd teeth-api               && python main.py
```

실행 후 확인:
- 헬스체크: `http://127.0.0.1:8000/health`
- API 문서: `http://127.0.0.1:8000/docs` (Swagger UI)

### Docker 빌드 검증

> **목적**: Dockerfile 문법, pip install, PYTHONPATH 설정 사전 확인.
> `docker run`은 불필요 — 모델 마운트 및 GPU는 AWS 환경에서 설정.

```bash
# 각 API 폴더에서 실행
cp .env.example .env
docker compose build
```

**참고**: 동시에 여러 API를 실행하려면 각 `docker-compose.yml`의 포트를 수정하세요.

---

## 관련 저장소

- [microlens-infra](../microlens-infra) — AWS 인프라 및 Kubernetes 배포
- [microlens-client](../microlens-client) — React + Vite 웹 클라이언트
