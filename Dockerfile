# ---- Base ----
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# ---- deps ----
# requirements.txt가 레포 루트에 있다고 가정
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 앱 소스만 복사 (불필요한 상위 파일까지 다 안 끌고 오게)
COPY apps/api ./apps/api

# ---- runtime env ----
ENV PORT=8080 \
    UVICORN_WORKERS=1

EXPOSE 8080

# ---- start ----
# 반드시 0.0.0.0 + $PORT로 바인딩
CMD ["bash", "-lc", "cd apps/api && uvicorn app:app --host 0.0.0.0 --port ${PORT} --workers ${UVICORN_WORKERS} --proxy-headers"]

