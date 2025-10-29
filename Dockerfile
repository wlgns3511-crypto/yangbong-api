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
    APP_MODULE=app:app
# APP_MODULE이 필요하면 Railway Variables에서 APP_MODULE=main:app 처럼 바꿔도 됨
# 현재 구조(apps/api/app.py)를 사용하려면 APP_MODULE=apps.api.app:app로 설정

EXPOSE 8080

# ---- start ----
CMD ["bash", "-lc", "uvicorn ${APP_MODULE} --host 0.0.0.0 --port ${PORT:-8080} --workers ${UVICORN_WORKERS:-1} --proxy-headers"]
