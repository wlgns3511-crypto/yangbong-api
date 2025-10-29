# 문제 진단 결과

## 발견된 주요 문제점

### 1. **모듈 경로 불일치** ⚠️
- **Dockerfile**: `APP_MODULE=app:app` (루트에서 app.py 찾음)
- **실제 위치**: `apps/api/app.py` (서브디렉토리에 있음)
- **결과**: `ModuleNotFoundError: No module named 'app'` 발생 가능

### 2. **Import 경로 문제** ⚠️
- `apps/api/app.py`에서 `from market_world import router`
- `market_world.py`도 `apps/api/` 디렉토리에 있음
- COPY . . 후 Python이 `apps/api`를 모듈로 인식하지 못함

### 3. **PYTHONPATH 미설정** ⚠️
- Dockerfile에 PYTHONPATH 설정이 없음
- Python이 `apps/api` 디렉토리를 모듈 경로로 찾지 못함

## 해결 방안

### 방안 1: Dockerfile 수정 (PYTHONPATH + APP_MODULE)
```dockerfile
ENV PYTHONPATH=/app/apps/api
ENV APP_MODULE=app:app
```

### 방안 2: APP_MODULE을 전체 경로로 변경
Railway Variables: `APP_MODULE=apps.api.app:app`

### 방안 3: apps/api 내용을 루트로 복사
Dockerfile에서 빌드 시 복사

