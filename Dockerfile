# Python 3.11 slim 이미지 사용
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 파일 먼저 복사 (레이어 캐싱 최적화)
COPY requirements.txt .

# 의존성 설치
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 시작 스크립트 복사 및 실행 권한 부여
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# 포트 노출
EXPOSE 8000

# 헬스체크 제거 (빌드 단계에서 문제를 일으킬 수 있음)
# 런타임에 플랫폼이 헬스체크를 제공함

# 시작 스크립트 실행
# Railway는 PORT 환경변수를 제공하므로 스크립트에서 처리
CMD ["/app/start.sh"]

