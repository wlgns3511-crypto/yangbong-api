FROM python:3.11-slim

# 기본 설정
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=on

# 작업 디렉토리 설정
WORKDIR /app

# 컨텍스트(루트 또는 apps/api)와 무관하게 동작하도록 전체 복사 후 requirements 탐지 설치
COPY . .
RUN if [ -f ./apps/api/requirements.txt ]; then \
      pip install --no-cache-dir -r ./apps/api/requirements.txt; \
    elif [ -f ./requirements.txt ]; then \
      pip install --no-cache-dir -r ./requirements.txt; \
    else \
      echo "requirements.txt not found (looked in ./apps/api and ./)" && exit 1; \
    fi

# Uvicorn 실행: 모듈 경로 자동 판별 (apps.api.app 우선, 실패 시 app)
CMD sh -c "uvicorn apps.api.app:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${UVICORN_WORKERS:-1} --proxy-headers || uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${UVICORN_WORKERS:-1} --proxy-headers"

