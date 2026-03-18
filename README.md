# MicroLens AI API

MicroLens 프로젝트의 AI 백엔드 저장소입니다.
FastAPI 기반의 AI 추론 서비스 3개를 멀티 레포 구조로 관리합니다.

## 서비스 구성

| 서비스 | 경로 | 역할 | 포트 |
|--------|------|------|------|
| stain-classification-api | `stain-classification-api/` | 의류 얼룩 분류 (beverage / food / pen) | 8000 |
| stain-detection-api | `stain-detection-api/` | 의류 얼룩 탐지 (위치 + 클래스) | 8000 |
| teeth-api | `teeth-api/` | 치아 이물질 탐지 (stuck_food) | 8000 |

## 디렉토리 구조

```
microlens-ai-api/
├── Jenkinsfile                 # CI/CD 파이프라인 (ECR 빌드, 매니페스트 업데이트)
├── ai-api-workflow.md          # 워크플로우 문서
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
모든 API가 동일한 응답 스키마를 사용합니다:

```json
{
  "detections": [
    {
      "label": "beverage",  // 클래스 레이블
      "confidence": 0.71,   // 신뢰도 (0-1)
      "bbox": {             // 바운딩 박스 (탐지 모델만)
        "x1": 319.28,
        "y1": 636.86,
        "x2": 539.09,
        "y2": 993.62
      }
    }
  ],
  "inference_time_ms": 456.32  // 추론 시간 (ms)
}
```

**참고**: 분류 API의 경우 `bbox` 필드는 null이거나 생략될 수 있습니다.

## 기술 스택

| 분류 | 기술 |
|------|------|
| 언어 | Python 3.10 |
| 웹 프레임워크 | FastAPI |
| 모델 서빙 | ONNX Runtime (CPU: 로컬 환경, GPU: aws 환경) |
| 컨테이너 | Docker |
| 이미지 레지스트리 | AWS ECR |
| CI/CD | Jenkins |

## CI/CD 파이프라인

Jenkins를 사용하여 자동화된 빌드 및 배포를 수행합니다.

### 파이프라인 단계
1. **ECR Login**: AWS ECR에 로그인
2. **Build & Push**: 각 API를 병렬로 Docker 이미지 빌드 및 ECR 푸시
3. **Update Manifests**: 인프라 리포지토리(`microlens-infra`)의 Kustomize 매니페스트 업데이트 및 푸시

### 환경 변수
- `AWS_REGION`: ap-northeast-2
- `INFRA_REPO`: https://github.com/MICRO-LENS/microlens-infra.git
- `IMAGE_TAG`: Git 커밋 해시 (앞 7자리)

# 로컬 개발

### Python 가상환경
> 가상환경은 루트에서 한 번만 생성. 각 API의 `requirements-dev.txt`는 동일한 패키지 구성입니다.

```bash
# 루트에서 가상환경 생성 (최초 1회)
python3.10 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
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

### Docker 실행
각 API 폴더에서 Docker Compose를 사용하여 실행:

```bash
cd stain-detection-api
docker-compose up --build
```

- **포트**: 8000
- **모델 마운트**: `./models` 디렉토리를 컨테이너에 읽기 전용으로 마운트
- **GPU 지원**: GPU 환경에서는 `docker-compose.yml`의 주석을 해제하여 NVIDIA 런타임 사용

**참고**: 동시에 여러 API를 실행하려면 각 `docker-compose.yml`의 포트를 수정하세요.

### 로컬 Docker 빌드 검증

> **목적**: Dockerfile 문법, pip install, PYTHONPATH 설정 사전 확인.
> `docker run`은 불필요 — 모델 마운트 및 GPU는 AWS 환경에서 설정.

```bash
# WSL 터미널 — 각 API 폴더에서 실행
cp .env.example .env
docker compose build
```

---

### 모델 파일 관리

`.onnx` 파일은 용량이 크므로 Git에 커밋하지 않습니다.

- **로컬**: 각 API의 `models/` 폴더에 직접 배치
- **운영(AWS)**: 컨테이너 실행 시 외부에서 마운트 (AWS 인프라 단계에서 설정)

---

# 배포

1. GitHub에 푸시하면 Jenkins 파이프라인이 자동 실행됩니다.
2. 각 API의 Docker 이미지가 ECR에 푸시됩니다.
3. 인프라 리포지토리의 Kustomize 매니페스트가 업데이트되어 Kubernetes에 자동 배포됩니다.


| 모듈 | 생성 리소스 |
|------|------------|
| `vpc` | VPC, 퍼블릭·프라이빗 서브넷 각 2개, NAT 인스턴스(t3.nano), EIP, 라우팅 테이블 |
| `ec2` | Control Plane(t3.medium), Worker Nodes(변수), Jenkins(t3.medium), IAM 인스턴스 프로파일 |
| `ecr` | stain-detection-api, stain-classification-api, teeth-api 리포지토리 |
| `s3` | 모델 가중치 버킷(버전 관리 활성화) |


## 관련 저장소

- [microlens-infra](../microlens-infra) — AWS 인프라 및 Kubernetes 배포
- [microlens-android](../microlens-android) — Android 클라이언트 앱
