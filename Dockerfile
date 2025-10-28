﻿FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PORT=8080
EXPOSE 8080
CMD ["gunicorn","-w","2","-k","uvicorn.workers.UvicornWorker","-b","0.0.0.0:8080","app:app"]
