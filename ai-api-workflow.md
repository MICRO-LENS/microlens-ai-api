# [단계 1] 로컬 개발 및 로컬 검증

**AI 추론용 API 서버 개발 및 컨테이너화 (FastAPI + ONNX + Docker)**

> 이 단계는 인프라에 올릴 실제 서비스(페이로드)를 준비하는 과정입니다.
> 서빙 = 모델 실행 = 추론 결과를 사용자에게 전달하는 것

---

## 전제 조건 — 모델 준비 (Colab)

### (1) 모델 학습
- 무거운 작업이므로 Google Colab에서 진행

### (2) 모델 변환 (.pt → .onnx)
- 무거운 작업이므로 Google Colab에서 진행
- **`dynamic=True` 옵션**: 안드로이드 기기마다 카메라 해상도가 달라 서버로 들어오는 이미지 크기가 매번 다름. 이 옵션으로 모델이 고정된 입력 크기에 얽매이지 않고 유연하게 추론 가능
- **`opset=17` 옵션**: ONNX 연산자 버전 지정

변환된 모델 파일을 각 API의 `models/` 폴더에 배치:
```
stain-classification-api/models/stain_best.onnx
stain-detection-api/models/stain_detection_best.onnx
teeth-api/models/teeth_best.onnx
```

---

## 🛠️ 실제 작업 순서

### 1단계: 로컬 개발 — 비즈니스 로직 테스트 (venv + uvicorn)

> **목적**: 코드 수정 → 즉시 확인. Docker 없이 빠르게 반복하는 개발 단계.

#### 환경 세팅 (최초 1회)

작업 위치: `microlens-ai-api/` 루트

```powershell
# Python 3.10 가상환경 생성 (AI 라이브러리 호환성이 가장 안정적인 버전)
py -3.10 -m venv .venv

# 가상환경 활성화
.venv\Scripts\Activate.ps1

# 빌드 도구 업데이트
python -m pip install --upgrade pip setuptools wheel

# 개발용 의존성 설치 (CPU 기반 — 로컬 개발에는 GPU 불필요)
pip install -r stain-classification-api/requirements-dev.txt
```

**`requirements-dev.txt` 패키지 구성 이유**

| 패키지 | 역할 |
|---|---|
| `fastapi` | 비동기 지원이 강력한 웹 프레임워크. 모델 추론 중에도 다른 요청 처리 가능 |
| `uvicorn[standard]` | ASGI 서버. FastAPI를 실제로 실행하는 엔진. `[standard]`로 uvloop 등 성능 모듈 포함 |
| `python-multipart` | 이미지 업로드 시 `multipart/form-data` 형식 파싱 |
| `onnxruntime` | CPU용 ONNX 모델 실행 엔진. 실제 서빙의 핵심 라이브러리 |
| `numpy` | 배열·행렬 연산 (이미지 전처리에 사용) |
| `Pillow` | 이미지 전처리 라이브러리 |
| `python-dotenv` | `.env` 파일로 환경변수 로드 |

> `requirements.txt`(운영용)와 다른 점: `onnxruntime` vs `onnxruntime-gpu`. 로컬에서는 CPU 버전으로 충분.

#### API별 실행

```powershell
# stain-classification-api
cd stain-classification-api
python main.py

# stain-detection-api
cd stain-detection-api
python main.py

# teeth-api
cd teeth-api
python main.py
```

#### 로컬 테스트 확인

서버 실행 후 브라우저 또는 Swagger UI에서 확인:
- 헬스체크: `http://127.0.0.1:8000/health`
- Swagger UI: `http://127.0.0.1:8000/docs` → `/predict` 엔드포인트에서 이미지 업로드 테스트

정상 응답 예시:
```json
{
  "detections": [
    {
      "label": "beverage",
      "confidence": 0.7078766822814941,
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

---

### 2단계: 로컬 검증 — Docker 빌드 확인 (Jenkins 불필요)

> **목적**: Dockerfile 문법, pip install, PYTHONPATH 설정이 정상인지 확인.
> 여기서 빌드가 성공하면 Git 푸시 → CI/CD 파이프라인으로 넘어갈 준비 완료.
>
> `docker run`까지는 불필요. 모델 파일 마운트, GPU 드라이버는 AWS 환경에서 설정.

#### 전제 조건: WSL에 Docker 설치, `docker` 그룹 권한 설정

```bash
# docker 그룹에 유저 추가 (최초 1회)
sudo usermod -aG docker $USER
# 이후 WSL 재시작 필요: Windows PowerShell에서 wsl --shutdown
```

#### `.env` 파일 준비 (최초 1회)

```bash
# WSL 터미널에서 각 API 폴더로 이동 후 실행
cp .env.example .env
```

#### Docker 빌드 실행

```bash
# WSL 터미널 — 각 API 폴더에서 실행
cd /mnt/c/MyProject/micro-lens/microlens/microlens-ai-api/stain-classification-api
docker compose build

cd /mnt/c/MyProject/micro-lens/microlens/microlens-ai-api/stain-detection-api
docker compose build

cd /mnt/c/MyProject/micro-lens/microlens/microlens-ai-api/teeth-api
docker compose build
```

빌드 성공 시:
```
[+] Building 1/1
 ✔ stain-classification-api  Built
```

#### docker build로 검증되는 것 vs 안 되는 것

| 항목 | `docker build`로 확인 가능 | 비고 |
|---|---|---|
| Dockerfile 문법 오류 | ✅ | |
| pip install 실패 (버전 충돌, 오타) | ✅ | |
| COPY 경로 오류 | ✅ | |
| ENV / PYTHONPATH 설정 | ✅ | |
| 모델 파일 마운트 | ❌ | AWS 환경에서 volumes 설정 |
| GPU 실행 | ❌ | 로컬에 GPU 없으면 어차피 실패 |
| 실제 API 응답 | ❌ | 1단계 uvicorn에서 이미 확인 |

---

## 파일 구조 참고

```
microlens-ai-api/
├── stain-classification-api/
├── stain-detection-api/
└── teeth-api/
    ├── app/
    │   ├── routers/predict.py      # API 엔드포인트
    │   ├── schemas/prediction.py   # 요청/응답 스키마
    │   └── services/detector.py    # ONNX 추론 로직
    ├── models/                     # .onnx 모델 파일 (Git 제외, 별도 관리)
    ├── main.py                     # 앱 진입점
    ├── requirements.txt            # 운영용 (GPU — onnxruntime-gpu)
    ├── requirements-dev.txt        # 개발용 (CPU — onnxruntime)
    ├── Dockerfile                  # 멀티 스테이지 빌드 + Non-root 보안
    ├── docker-compose.yml          # 로컬 Docker 빌드 및 볼륨 마운트 설정
    ├── .env.example                # 환경변수 템플릿 (Git 포함)
    └── .gitignore                  # .env, *.onnx Git 제외
```
