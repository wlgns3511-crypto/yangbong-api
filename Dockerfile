# ------------------------
# 🐍 Python 환경 설정
# ------------------------
FROM python:3.11-slim

# 작업 폴더 생성
WORKDIR /app

# 종속성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 파일 복사
COPY . .

# 환경 변수 설정
ENV PORT=8080
EXPOSE 8080

# FastAPI 실행 (Gunicorn + Uvicorn Worker)
CMD ["gunicorn", "-w", "2", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8080", "app:app"]
