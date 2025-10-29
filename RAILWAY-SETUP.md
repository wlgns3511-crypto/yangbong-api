# Railway 배포 설정 가이드

## Railway 빌드 실패 (Railpack) 회피 체크리스트

### 1. 서비스 설정

#### API 서비스
- **Root Directory**: `apps/api`로 설정
- **Build Command**: 비워둠 (Dockerfile 사용)
- **Start Command**: 비워둠 (Dockerfile CMD 사용)

#### Web 서비스
- **Root Directory**: `apps/web`로 설정
- **Build Command**: 비워둠 (Dockerfile 사용)
- **Start Command**: 비워둠 (Dockerfile CMD 사용)

### 2. 환경 변수 설정

#### API 서비스
- `UVICORN_WORKERS`: `2` (선택사항, 기본값 1)
- `PORT`: Railway가 자동으로 설정 (동적 포트)

#### Web 서비스
- `NEXT_PUBLIC_API_BASE`: API의 공개 URL
  - **Nginx 프록시 사용 시**: `/api`
  - **직접 연결 시**: API 서비스의 Railway 공개 URL (예: `https://xxx.up.railway.app`)
- `NODE_ENV`: `production` (선택사항)

### 3. 포트 설정

- Railway는 동적 포트를 할당하므로 `$PORT` 환경 변수를 사용해야 함
- API Dockerfile에서 `${PORT:-8000}`로 기본값 처리됨
- `--proxy-headers` 플래그로 X-Forwarded-* 헤더 자동 처리

### 4. 확인 사항

- [ ] 각 서비스의 Root Directory가 올바르게 설정되어 있는가?
- [ ] Build/Start Command가 비워져 있는가?
- [ ] Dockerfile이 각 서비스 루트에 존재하는가?
- [ ] Web 서비스의 `NEXT_PUBLIC_API_BASE`가 올바르게 설정되어 있는가?

### 5. 배포 순서

1. API 서비스를 먼저 배포
2. API 서비스의 공개 URL 확인
3. Web 서비스의 `NEXT_PUBLIC_API_BASE` 설정
4. Web 서비스 배포

### 6. 트러블슈팅

#### Railpack 빌드 실패
- Root Directory 확인
- Build Command 비워두기 (Dockerfile 자동 감지)

#### 포트 에러
- `$PORT` 환경 변수 확인
- Dockerfile의 CMD가 `${PORT:-8000}` 형식인지 확인

#### API 연결 실패
- `NEXT_PUBLIC_API_BASE` 환경 변수 확인
- CORS 설정 확인 (현재 `allow_origins=["*"]`)

