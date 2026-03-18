# ---- Build stage ----
FROM python:3.10-slim AS builder

WORKDIR /app

COPY requirements.txt .
# 의존성 설치 (캐시 미사용 및 지정된 경로에 설치)
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- Runtime stage ----
FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04

WORKDIR /app

# 1. Python 3.10 및 pip 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3.10 python3-pip \
    && rm -rf /var/lib/apt/lists/*

# 2. K8s 보안 표준 준수를 위한 비루트(Non-root) 사용자 생성
RUN useradd -m appuser

# 3. 빌드 스테이지에서 설치된 패키지 복사 (이미지 크기 최소화)
COPY --from=builder /install /usr/local

# 4. 애플리케이션 코드 및 진입점(main.py) 복사
COPY app/ app/
COPY main.py .

# 모델 마운트용 디렉토리 생성 및 소유권 부여
RUN mkdir -p models && chown -R appuser:appuser /app

# 5. 보안을 위해 appuser로 전환하여 컨테이너 실행
USER appuser

# 환경 변수 설정
ENV MODEL_PATH=models/teeth_best.onnx \
    CONF_THRESHOLD=0.25 \
    IOU_THRESHOLD=0.45 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/usr/local/lib/python3.10/site-packages

EXPOSE 8000

# 6. 실행 명령어 (python3 -m 으로 shebang 경로 문제 방지)
CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
