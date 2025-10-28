FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# FastAPI 실행 (app.py 안의 'app' 객체를 기준으로)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
