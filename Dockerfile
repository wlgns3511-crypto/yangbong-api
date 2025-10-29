# ---- Base ----
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# ---- deps ----
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# ---- app ----
COPY . .

# ---- runtime ----
ENV PORT=8080 \
    UVICORN_WORKERS=1 \
    APP_MODULE=app:app \
    PYTHONPATH=/app/apps/api:/app
# PYTHONPATH 설정으로 apps/api 디렉토리를 Python 모듈 경로에 추가
# APP_MODULE=app:app은 PYTHONPATH에 /app/apps/api가 있어서 apps/api/app.py를 찾을 수 있음

EXPOSE 8080

# ---- start ----
# PYTHONPATH 설정으로 apps/api를 모듈 경로에 추가, cd 없이 실행
CMD ["bash", "-lc", "uvicorn ${APP_MODULE} --host 0.0.0.0 --port ${PORT:-8080} --workers ${UVICORN_WORKERS:-1} --proxy-headers"]
