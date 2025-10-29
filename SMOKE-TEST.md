# 스모크 테스트 가이드

## 1. 로컬 (docker-compose) 스모크 테스트

### 초기화 및 빌드
```bash
docker compose down -v
docker compose up -d --build
docker ps
```

### 헬스체크
```bash
# Windows PowerShell
Invoke-WebRequest -Uri http://localhost/api/health -UseBasicParsing | Select-Object -ExpandProperty Content
# 예상 출력: {"ok":true}

# 프론트엔드 확인
$response = Invoke-WebRequest -Uri http://localhost/ -UseBasicParsing
$response.Content.Substring(0, [Math]::Min(200, $response.Content.Length))
# 예상 출력: <!DOCTYPE html><html lang="en">...
```

### 로그 확인 (문제 발생 시)
```bash
docker compose logs -f api
docker compose logs -f web
docker compose logs -f nginx
```

### 워커 확인
```bash
docker compose exec api ps aux
# uvicorn 프로세스가 --workers 2로 실행되는지 확인
```

## 2. 로컬 (dev 서버) 스모크 테스트

### 백엔드 시작
```bash
cd apps\api
.\.venv\Scripts\python.exe -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### 프론트엔드 시작 (새 터미널)
```bash
cd apps\web
npm run dev
```

### 브라우저 확인
- `http://localhost:3000` 접속
- 세계지수 9종 그리드 표시 확인
- API 탭(health/ping) 정상 응답 확인

## 3. Railway 스모크 테스트

### 서비스 설정

#### API 서비스
- **Root Directory**: `apps/api`
- **Build Command**: (비워둠)
- **Start Command**: (비워둠)

#### Web 서비스
- **Root Directory**: `apps/web`
- **Build Command**: (비워둠)
- **Start Command**: (비워둠)

### 환경 변수 설정

#### Web 서비스 ENV
- `NEXT_PUBLIC_API_BASE` = API 퍼블릭 URL 
  - 예: `https://<api-subdomain>.railway.app`

### 재배포 후 확인

```bash
# API 헬스체크
curl https://<api-subdomain>.railway.app/health
# 예상 출력: {"ok":true}

# Web 홈
curl https://<web-subdomain>.railway.app/
# HTML 응답 및 세계지수 그리드 표시 확인
```

### 문제 발생 시 확인
- Railway > Service > Deploy Logs
- Railway > Variables (PORT, NEXT_PUBLIC_API_BASE)

## 4. 빠른 자가진단 (문제 발생 시)

### 웹에서 API 호출 4xx/5xx
- `NEXT_PUBLIC_API_BASE` 값 확인
- Railway에서는 절대경로 URL 필요 (`https://...`)

### API 502/timeout
- `nginx.conf`에서 `/api/` 프록시 경로/슬래시 확인
- API 컨테이너 헬스체크 상태: `docker ps` 확인

### CORS
- FastAPI 미들웨어: `allow_origins=["*"]` 설정됨
- 프록시 뒤에서도 정상 작동

### 워커 반영 여부
```bash
docker compose exec api ps aux
# --workers 2 확인
```

### 이미지 비대
- `.dockerignore` 적용 여부 확인
```bash
docker history <image>
```

## 5. 최종 커밋/태그 (선택)

```bash
git add -A
git commit -m "chore: prod-ready docker/nginx/railway setup"
git tag -a v1.0.0 -m "first prod cut"
git push origin main --tags
```

