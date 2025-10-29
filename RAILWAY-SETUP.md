# Railway 배포 설정 가이드

## Railway 빌드 실패 (Railpack) 회피 체크리스트

### 현재 설정: Nixpacks 모드 사용 (Dockerfile.off로 비활성화됨)

### 1. 서비스 설정

#### API 서비스
- **Root Directory**: `apps/api`로 설정
- **Builder**: Nixpacks (자동 감지)
- **Build Command**: 비워둠 (자동 추론)
- **Start Command**: (선택사항) 아래 명령 사용 가능
  ```
  cd apps/api && uvicorn app:app --host 0.0.0.0 --port $PORT --workers ${UVICORN_WORKERS:-1} --proxy-headers
  ```

#### Web 서비스
- **Root Directory**: `apps/web`로 설정
- **Builder**: Nixpacks (자동 감지)
- **Build Command**: 비워둠 (자동 추론)
- **Start Command**: 비워둠 (자동 추론)

### 2. 환경 변수 설정

#### API 서비스
- `UVICORN_WORKERS`: `1` (권장 - 멀티워커 초기화 문제 방지)
- `PYTHONUNBUFFERED`: `1` (로그 버퍼링 방지)
- `PORT`: Railway가 자동으로 설정 (동적 포트) - 설정 불필요

#### Web 서비스
- `NEXT_PUBLIC_API_BASE`: API의 공개 URL
  - **직접 연결 시**: API 서비스의 Railway 공개 URL (예: `https://xxx.up.railway.app`)
- `NODE_ENV`: `production` (선택사항)

### 3. 포트 설정

- Railway는 동적 포트를 할당하므로 `$PORT` 환경 변수를 사용해야 함
- Start Command에서 `--port $PORT` 사용
- `--proxy-headers` 플래그로 X-Forwarded-* 헤더 자동 처리

### 4. 확인 사항

- [ ] 각 서비스의 Root Directory가 올바르게 설정되어 있는가? (apps/api, apps/web)
- [ ] Railway Settings > Build > Builder가 **Nixpacks**로 표시되는가?
- [ ] API 서비스의 Start Command가 올바른가? (또는 자동 추론 확인)
- [ ] Web 서비스의 `NEXT_PUBLIC_API_BASE`가 올바르게 설정되어 있는가?
- [ ] 환경 변수 `UVICORN_WORKERS=1`, `PYTHONUNBUFFERED=1` 설정 확인

### 5. 배포 순서

1. API 서비스를 먼저 배포
2. API 서비스의 공개 URL 확인
3. Web 서비스의 `NEXT_PUBLIC_API_BASE` 설정
4. Web 서비스 배포

### 6. 트러블슈팅

#### Nixpacks 빌드 실패
- Root Directory 확인 (`apps/api` 또는 `apps/web`)
- Settings > Build > Builder가 Nixpacks인지 확인
- Build Command 비워두기 (자동 추론)

#### 포트 에러
- `$PORT` 환경 변수 확인 (Railway 자동 설정)
- Start Command에 `--port $PORT` 포함 확인

#### API 연결 실패
- `NEXT_PUBLIC_API_BASE` 환경 변수 확인
- CORS 설정 확인 (현재 `allow_origins=["*"]`)

#### Dockerfile 모드로 돌아가려면
- 레포 루트의 `Dockerfile.off`를 `Dockerfile`로 이름 변경
- Settings > Build > Builder가 Dockerfile로 자동 전환됨

