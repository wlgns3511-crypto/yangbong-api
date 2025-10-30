FROM python:3.11-slim

# 기본 설정
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=on

# 작업 디렉토리 설정
WORKDIR /app

# requirements 복사 및 설치
COPY apps/api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 전체 복사
COPY . .

# Uvicorn 실행 (app.py 경로 명시)
CMD sh -c "uvicorn apps.api.app:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${UVICORN_WORKERS:-1} --proxy-headers"

