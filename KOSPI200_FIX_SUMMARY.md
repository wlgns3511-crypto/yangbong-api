# 코스피200 연동 문제 해결 진행사항

## 📋 현재까지 진행사항 (2025-11-07)

### ✅ 완료된 작업

#### 1. **코스피200 데이터 파싱 개선**
   - **파일**: `yangbong-api/apps/api/market_kr.py`
   - **변경사항**:
     - 코스피200 전용 HTML 파싱 로직 추가
     - 지수별 가격 범위 검증 (KOSPI200: 300~1000)
     - 테이블 셀, `<em>`, `<strong>` 태그 우선 파싱
     - 키워드 기반 패턴 매칭 개선

#### 2. **부분 실패 처리 개선**
   - **파일**: `yangbong-api/apps/api/market_unified.py`
   - **변경사항**:
     - JSON API가 일부만 성공해도 HTML fallback 시도
     - 실패한 항목만 HTML 파싱으로 보완
     - 상세한 로깅 추가

#### 3. **로깅 강화**
   - **파일**: `yangbong-api/apps/api/naver_indices.py`
   - **변경사항**:
     - 네이버 JSON API 응답 상세 로깅
     - 에러 상황별 로깅 개선

---

## ⚠️ 현재 발견된 문제점

### 🔴 실시간 시세 연동 문제

#### 문제 상황
- 클라이언트는 30~60초마다 데이터 요청
- 서버는 **90초 TTL**로 캐시를 반환
- 결과: `stale: true` 응답으로 오래된 데이터 표시

#### 문제 원인
1. **캐시 TTL이 너무 김** (90초)
   - 클라이언트 폴링 주기(30~60초)보다 길어서 항상 캐시 반환
   
2. **실시간 업데이트 스케줄러 없음**
   - 뉴스는 스케줄러 있음 (`news_scheduler.py`)
   - 마켓 데이터는 수동 요청 시에만 갱신
   
3. **캐시 우회 옵션 부족**
   - `cache=0` 파라미터로 강제 새로고침 불가

#### 영향받는 파일
```
yangbong-api/apps/api/market_common.py
  - TTL_SEC = 90 (기본값)
  
yangbong-web/src/components/SnapshotStrip.tsx
  - setInterval(load, 60_000)  // 60초마다
  
yangbong-web/src/hooks/useMarketData.ts
  - refreshInterval: 30000  // 30초마다
```

---

## 🔧 해결 방안

### 1. 캐시 TTL 단축
```python
# market_common.py
TTL_SEC = int(os.environ.get("MARKET_TTL_SEC", "30"))  # 90 → 30초
```

### 2. 캐시 우회 옵션 추가
```python
# market_unified.py
def market(seg: str = ..., cache: int = Query(1)):  # cache=0으로 강제 새로고침
    if cache == 0:
        cached, fresh = [], False  # 캐시 무시
```

### 3. 실시간 업데이트 스케줄러 추가
```python
# scheduler.py 또는 새 파일
def collect_market_data():
    """30초마다 마켓 데이터 수집"""
    from .market_unified import market
    for seg in ["KR", "US", "CRYPTO", "CMDTY"]:
        market(seg=seg, cache=0)  # 캐시 무시하고 강제 갱신

# app.py에서 스케줄러 시작
sched.add_job(
    collect_market_data,
    'interval',
    seconds=30,
    id='market_collector',
    replace_existing=True
)
```

### 4. 클라이언트 캐시 헤더 개선
```typescript
// useMarketData.ts
const res = await fetch(url, {
    cache: 'no-store',
    headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache'
    }
});
```

---

## 📝 다음 작업 우선순위

### ✅ 완료된 작업
1. ✅ TTL을 30초로 단축 (`market_common.py`)
2. ✅ `cache=0` 파라미터로 캐시 우회 기능 추가 (`market_unified.py`, `market_kr.py`, `market_world.py`)
3. ✅ 실시간 업데이트 스케줄러 추가 (`market_scheduler.py`, `app.py`)
4. ✅ 클라이언트 캐시 헤더 개선 (`useMarketData.ts`, `SnapshotStrip.tsx`, `config.ts`)

### 중기 (성능 최적화)
- WebSocket 연결 고려 (선택사항)
- 캐시 전략 개선 (stale-while-revalidate)

### 장기 (모니터링)
- API 응답 시간 모니터링
- 에러율 추적

---

## 🔍 테스트 체크리스트

- [ ] 코스피200 값이 정상적으로 표시되는가?
- [ ] 30초 이내에 데이터가 갱신되는가?
- [ ] `stale: true` 경고가 사라졌는가?
- [ ] 캐시 우회 옵션(`cache=0`)이 동작하는가?
- [ ] 스케줄러가 정상적으로 동작하는가?

## 📦 변경된 파일 목록

### 백엔드
- `yangbong-api/apps/api/market_common.py` - TTL 90초 → 30초
- `yangbong-api/apps/api/market_unified.py` - cache=0 옵션 추가
- `yangbong-api/apps/api/market_kr.py` - cache=0 옵션 추가
- `yangbong-api/apps/api/market_world.py` - cache=0 옵션 추가
- `yangbong-api/apps/api/market_scheduler.py` - **신규**: 실시간 업데이트 스케줄러
- `yangbong-api/apps/api/app.py` - 스케줄러 시작 로직 추가

### 프론트엔드
- `yangbong-web/src/hooks/useMarketData.ts` - 캐시 헤더 추가
- `yangbong-web/src/components/SnapshotStrip.tsx` - cache=0 파라미터 추가
- `yangbong-web/src/lib/config.ts` - apiGet 캐시 헤더 추가

---

## 📚 관련 파일 목록

### 백엔드
- `yangbong-api/apps/api/market_unified.py` - 통합 마켓 API
- `yangbong-api/apps/api/market_kr.py` - 국내 지수 파싱
- `yangbong-api/apps/api/market_common.py` - 캐시 관리
- `yangbong-api/apps/api/naver_indices.py` - 네이버 JSON API
- `yangbong-api/apps/api/scheduler.py` - 스케줄러 헬퍼
- `yangbong-api/apps/api/app.py` - FastAPI 앱

### 프론트엔드
- `yangbong-web/src/components/SnapshotStrip.tsx` - 상단 스냅샷
- `yangbong-web/src/hooks/useMarketData.ts` - 마켓 데이터 훅
- `yangbong-web/src/hooks/useMarket.ts` - 마켓 훅 (레거시)

---

## 💡 참고사항

- 네이버 금융 API는 공식 API가 아니므로 변경될 수 있음
- HTML 파싱은 페이지 구조 변경에 취약함
- 과도한 요청 시 IP 차단 가능성 있음 (스케줄러 사용 권장)

