# 캐시 정리 안내

## 문제
현재 캐시에 잘못된 가격 데이터(`price: -8` 등)가 저장되어 있어, 패치 적용 후에도 기존 캐시가 반환될 수 있습니다.

## 해결 방법

### 방법 1: 캐시 파일 직접 삭제 (권장)

캐시 파일 경로는 환경변수 `MARKET_CACHE_PATH`로 설정되며, 기본값은 `/tmp/market_cache.json`입니다.

```bash
# 로컬 개발 환경
rm -f /tmp/market_cache.json

# 또는 Windows PowerShell
Remove-Item -Force C:\tmp\market_cache.json -ErrorAction SilentlyContinue

# Railway/서버 환경
# 환경변수로 설정된 경로 확인 후 삭제
```

### 방법 2: 백엔드 재시작 후 자동 정리

패치 적용 후 백엔드를 재시작하면:
1. 새로운 데이터 수집 시 유효성 검증이 적용됨
2. 기존 캐시에서 데이터를 읽을 때도 필터링됨
3. 잘못된 데이터는 자동으로 제외됨

하지만 **기존 캐시에 잘못된 데이터가 많으면 즉시 삭제하는 것이 좋습니다**.

### 방법 3: API로 캐시 무효화 (개발용)

```bash
# 캐시 TTL을 0으로 설정하거나
# 환경변수 MARKET_TTL_SEC=0으로 설정 후 재시작
```

## 확인

패치 적용 및 캐시 정리 후:

```bash
# API 호출 테스트
curl "https://api.yangbong.club/api/market?seg=KR" | jq '.items[] | {symbol, price}'
```

모든 `price` 값이 양수여야 합니다.

