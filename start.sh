#!/bin/sh
# Railway 배포용 시작 스크립트
# PORT 환경변수를 읽어서 uvicorn 실행

PORT=${PORT:-8000}
echo "Starting server on port $PORT"
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"

