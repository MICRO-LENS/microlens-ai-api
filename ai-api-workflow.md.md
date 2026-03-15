\[단계 1] 

**AI 추론용 API 서버 개발 및 컨테이너화 (FastAPI + ONNX + Docker)]**



>> 이 단계는 인프라에 올릴 실제 서비스(페이로드)를 준비하는 과정입니다.

서빙(모델 실행 = 추론 결과를 사용자에게 전달하는 것)



**(1) 모델 학습**

* 무거운 작업 = colab



**(2) 모델 변환** 

* 가중치 파일(.pt) → .onnx 으로 변환
* 무거운 작업 = colab
* 변환 코드에 포함된 dynamic=True 옵션

  * 안드로이드 기기마다 카메라 해상도가 다르고 크롭되는 비율이 달라서 서버로 들어오는 이미지의 크기가 매번 다름
  * 이 옵션을 적용하여 변환하면, 모델이 고정된 입력 크기에 얽매이지 않고 유연하게 추론할 수 있어 에러 발생률을 크게 낮출 수 있습니다.
* opset=17 옵션



**(3) 추론 및 서빙 환경 구축**

### [1] 로컬 비즈니스 로직 테스트 환경 구축(venv)

* (1) windows 환경 -> python 가상환경 세팅

  * AI 라이브러리 호환성이 가장 안정적인 3.10 VER
  * Python 3.10.11 설치 (사이트: python.org/downloads/windows)
* (2)  가상환경 방 만들기

&#x09;명령어: py -3.10 -m venv .venv

* 3\) 가상환경 접속하기

&#x09;명령어: .venv\\Scripts\\Activate.ps1

* 4\) 기본 빌드 도구 먼저 업데이트하기

&#x09;명령어: python -m pip install --upgrade pip setuptools wheel

* 5\) 프로젝트 요구사항 설치하기

  * 명령어: pip install -r stain-classification-api/requirements-dev.txt
  * 모델 실행(추론)만 담당하는 패키지만 구성 -> 의존성 최소화

    * fastapi==0.111.0	 >> 비동기 지원이 강력해서 머신러닝 모델 서빙에 사용

      * 비동기 = 모델 추론 중에도 다른 요청(예: 이미지 업로드, 결과 반환)을 처리 가능
    * uvicorn\[standard]==0.30. >> -  ASGI 서버. FastAPI 같은 비동기 웹 프레임워크를 실제로 실행하는 엔진 역할을 합니다. \[standard] 옵션은 websockets, uvloop 같은 성능 향상 모듈을 함께 설치해줍니다.
    * python-multipart==0.0.9 >> 이미지를 업로드하면 multipart/form-data 형식으로 전달되는데, 이를 파싱해주는 역할
    * onnxruntime==1.23.2 >> - cpu ONNX 모델 실행 엔진. PyTorch나 TensorFlow에서 변환한 ONNX 모델을 불러와서 추론을 수행할 수 있게 해줍니다. 즉, 실제 "서빙"의 핵심 라이브러리.
    * numpy==1.26.4 >> - 수치 계산 라이브러리. 배열, 행렬 연산을 빠르게 처리합니다. 
    * Pillow==10.3.0 >> - 이미지 전처리 라이브러리
    * python-dotenv==1.0.1

* 6\) 비즈니스 로직 작성
  *  Python 기반의 FastAPI 프레임워크를 사용
  * 안드로이드 앱으로부터 이미지를 받기
  * 추론 결과를 반환하는 로직 개발

* 6\) 로컬 테스트 진행
  * cd stain-classification-api
  * python main.py
  * http://127.0.0.1:8000/health
  * http://127.0.0.1:8000/docs
{

&#x20; "detections": \[

&#x20;   {

&#x20;     "label": "beverage",

&#x20;     "confidence": 0.7078766822814941,

&#x20;     "bbox": {

&#x20;       "x1": 319.2802734375,

&#x20;       "y1": 636.8619384765625,

&#x20;       "x2": 539.09912109375,

&#x20;       "y2": 993.6275634765625

&#x20;     }

&#x20;   }

&#x20; ],

&#x20; "inference\_time\_ms": 456.32

}

### [2] 로컬 Docker 최종 검증 (Build & Test)
배포 직전에 컨테이너 환경(파일 경로, 권한, GPU 설정 등)을 최종 확인하는 단계입니다.

### 이미지 빌드 및 실행
- **이미지 빌드**: `Dockerfile`의 멀티 스테이지 빌드를 통해 최적화된 이미지를 생성합니다.
  ```bash
  docker compose build
  ```
- **컨테이너 실행**: `.env` 설정값과 로컬 `models/` 디렉토리가 컨테이너에 반영됩니다.
  ```bash
  docker compose up
  ```

### 체크리스트
- [ ] `appuser`(Non-root) 권한으로 프로세스가 정상 실행되는가?
- [ ] 컨테이너 내부의 `/app/models` 경로에 모델 파일이 정상적으로 읽히는가?
- [ ] GPU 환경(필요 시)에서 `onnxruntime-gpu`가 제대로 동작하는가?

### [3] 운영 서버 배포

검증된 이미지를 운영 환경에 배포합니다.

### 이미지 푸시
- 빌드된 이미지에 태그를 지정하고 레지스트리(ECR, Docker Hub 등)에 푸시합니다.
  ```bash
  docker tag stain-api:latest <your-registry>/stain-api:v1.0.0
  docker push <your-registry>/stain-api:v1.0.0
  ```

### 운영 서버 실행
- 운영 서버의 환경 변수 설정을 확인한 후 이미지를 실행합니다.
  ```bash
  docker run -d --name stain-api \
    -p 8000:8000 \
    --env-file .env \
    -v /path/to/models:/app/models:ro \
    <your-registry>/stain-api:v1.0.0
  ```
## 파일 구조 참고
- `requirements-dev.txt`: 로컬 개발용 (CPU 기반)
- `requirements.txt`: 운영 및 Docker 빌드용 (GPU 기반)
- `Dockerfile`: 보안(Non-root) 및 크기 최적화가 적용된 멀티 스테이지 빌드
- `docker-compose.yml`: 로컬 Docker 테스트 및 볼륨 마운트 설정