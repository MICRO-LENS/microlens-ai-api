# microlens-ai-api

MicroLens 프로젝트의 AI 백엔드 저장소입니다.
FastAPI 기반의 두 가지 AI 서비스를 모노레포 구조로 관리합니다.

---

## 서비스 구성

| 서비스 | 경로 | 역할 |
|--------|------|------|
| stain-api | `stain-api/` | 렌즈 얼룩 탐지 (이미지 분류/탐지 모델) |
| teeth-api | `teeth-api/` | 치아 상태 확인 (이미지 분석 모델) |

---

## 디렉토리 구조

```
microlens-ai-api/
├── stain-api/
│   ├── app/
│   │   ├── main.py         # FastAPI 엔트리포인트
│   │   ├── routers/        # API 라우터
│   │   ├── services/       # 모델 추론 로직
│   │   └── schemas/        # Pydantic 요청/응답 스키마
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
└── teeth-api/
    ├── app/
    │   ├── main.py
    │   ├── routers/
    │   ├── services/
    │   └── schemas/
    ├── Dockerfile
    ├── requirements.txt
    └── .env.example
```

---

## API 엔드포인트 (예시)

### stain-api
```
POST /predict        — 이미지 업로드 후 얼룩 탐지 결과 반환
GET  /health         — 서버 상태 확인
```

### teeth-api
```
POST /predict        — 이미지 업로드 후 치아 상태 분석 결과 반환
GET  /health         — 서버 상태 확인
```

---

## 기술 스택

| 분류 | 기술 |
|------|------|
| 언어 | Python 3.11 |
| 웹 프레임워크 | FastAPI |
| 모델 서빙 | PyTorch / ONNX Runtime |
| 컨테이너 | Docker |
| 이미지 레지스트리 | AWS ECR |

---

## 모델 가중치 파일 관리

`.pt`, `.onnx` 등 대용량 모델 파일은 **Git에 커밋하지 않습니다.**

- 개발 환경: S3에서 직접 다운로드 (`scripts/download_models.sh`)
- 프로덕션: Pod 기동 시 S3에서 마운트

---

## 로컬 개발 환경 설정

```bash
# stain-api 예시
cd stain-api
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # 환경변수 설정 후 사용
uvicorn app.main:app --reload
```

### Docker로 실행

```bash
cd stain-api
docker build -t microlens-stain-api .
docker run -p 8000:8000 microlens-stain-api
```

---

## 관련 저장소

- [microlens-infra](../microlens-infra) — AWS 인프라 및 Kubernetes 배포
- [microlens-android](../microlens-android) — Android 클라이언트 앱
