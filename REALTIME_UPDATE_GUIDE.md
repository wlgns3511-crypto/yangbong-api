# 🔄 실시간 시세 갱신 가이드

## ✅ 완료된 작업

### 백엔드 (4개 파일)
1. ✅ `apps/api/market_common.py` - TTL 30초 + 유틸
2. ✅ `apps/api/cache.py` - 파일 기반 캐시 (load_cache/save_cache)
3. ✅ `apps/api/market_unified.py` - cache=0 우회 + 신선도 판단
4. ✅ `apps/api/market_scheduler.py` - 30초 주기 수집 + 파일 락

### 프론트엔드 (3개 파일)
1. ✅ `src/lib/config.ts` - 공통 fetch (no-cache 헤더)
2. ✅ `src/hooks/useMarketData.ts` - 30초 폴링 + 캐시 우회 (SWR)
3. ✅ `src/components/SnapshotStrip.tsx` - cache=0 사용

---

## 🚀 배포 체크리스트

### 1. 환경변수 설정
```bash
# 서버 환경변수에 추가
export RUN_SCHEDULER=true
```

또는 `.env` 파일:
```env
RUN_SCHEDULER=true
```

### 2. 서버 재시작
```bash
# FastAPI 서버 재시작
# 스케줄러가 자동으로 시작됨
```

### 3. 캐시 디렉토리 확인
```bash
# 기본 경로: /tmp
# 환경변수로 변경 가능: MARKET_CACHE_DIR=/path/to/cache
ls -la /tmp/market_*.json
```

---

## 🔍 테스트 방법

### 1. 브라우저 개발자도구 확인
1. Network 탭 열기
2. `/api/market?seg=KR&cache=0` 요청 확인
3. 응답에서 `source: "live"`, `stale: false` 확인

### 2. 30초 대기 후 확인
1. 값이 변경되는지 확인
2. `time` 필드가 업데이트되는지 확인

### 3. 스케줄러 로그 확인
```bash
# 서버 로그에서 확인
grep "market_scheduler" logs/app.log
```

예상 로그:
```
market_scheduler: started (30s interval)
market_scheduler: KR updated (3 items)
market_scheduler: US updated (3 items)
```

---

## 🐛 문제 해결

### 캐시가 갱신되지 않을 때

1. **캐시 파일 삭제**
```bash
rm /tmp/market_KR.json
rm /tmp/market_US.json
```

2. **스케줄러 락 파일 확인**
```bash
ls -la /tmp/yb_scheduler.lock
# 다른 인스턴스가 실행 중일 수 있음
```

3. **환경변수 확인**
```bash
echo $RUN_SCHEDULER
# "true"여야 함
```

### stale: true가 계속 나올 때

1. **네이버 API 확인**
   - 네트워크 오류인지 확인
   - HTML 파싱이 실패하는지 확인

2. **로그 확인**
```python
# market_unified.py에서 로그 확인
log.warning("live fetch failed")
```

---

## 📊 동작 원리

### 1. 스케줄러 (백그라운드)
- 30초마다 자동으로 데이터 수집
- `/tmp/market_KR.json`, `/tmp/market_US.json`에 저장
- 파일 락으로 단일 인스턴스 보장

### 2. API 요청 (프론트엔드)
- `cache=0`: 캐시 무시, 라이브 데이터 요청
- `cache=1`: 캐시 사용 (30초 이내면 신선한 데이터)

### 3. 클라이언트 폴링
- SWR이 30초마다 자동 요청
- `forceLive=true`면 항상 `cache=0` 사용

---

## 🔧 커스터마이징

### TTL 변경
```python
# market_common.py
TTL_SECONDS = 60  # 30초 → 60초로 변경
```

### 폴링 주기 변경
```typescript
// useMarketData.ts
refreshInterval: 60_000,  // 30초 → 60초로 변경
```

### 스케줄러 간격 변경
```python
# market_scheduler.py
scheduler.add_job(
    _collect_all,
    "interval",
    seconds=60,  # 30초 → 60초로 변경
    ...
)
```

---

## 📝 참고사항

- 스케줄러는 `RUN_SCHEDULER=true`일 때만 동작
- 파일 락으로 여러 워커에서도 안전하게 동작
- 캐시 파일은 `/tmp` 디렉토리에 저장 (환경변수로 변경 가능)
- 브라우저 캐시는 `Cache-Control: no-cache` 헤더로 제어

