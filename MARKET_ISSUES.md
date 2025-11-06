# 시세 데이터 파싱 문제 정리

## 🔴 발견된 문제

### 1. **음수 가격이 파싱됨** (`price: -8`)
- **위치**: `market_kr.py`의 `_parse_naver()` 함수
- **원인**: HTML에서 첫 번째 숫자를 무조건 가격으로 사용
- **문제**: 변화량(-8)이 첫 번째로 나오면 그것을 가격으로 착각
- **영향**: 캐시에 잘못된 데이터가 저장되어 계속 반환됨

### 2. **가격 검증 로직 없음**
- **위치**: `market_common.py`의 `normalize_item()` 함수
- **문제**: 음수나 0인 가격을 그대로 통과시킴
- **영향**: 잘못된 데이터가 프론트엔드까지 전달됨

### 3. **HTML 파싱의 한계**
- **위치**: `market_kr.py`의 `_parse_naver()` 함수
- **문제**: 
  - HTML에서 숫자를 찾는 방식이 너무 단순함
  - 가격/변화량/변화율을 구분하지 못함
  - 페이지 구조 변경에 취약함

### 4. **네이버 JSON API 미사용**
- **위치**: `naver_indices.py`의 `fetch_kr_indices()` 함수
- **문제**: 
  - JSON API가 있는데 HTML 파싱을 사용 중
  - JSON API가 더 정확하고 안정적임
  - 현재 `market_unified.py`에서 `fetch_kr_indices`를 사용하지 않음

## 📋 수정 필요 사항

### 우선순위 1: 가격 검증 추가
```python
# market_common.py의 normalize_item() 함수에 추가
price = float(raw.get("price") or raw.get("close") or raw.get("now") or raw.get("last") or 0)
if price <= 0:  # 음수나 0인 가격은 무효
    price = 0.0  # 또는 캐시에서 가져오기
```

### 우선순위 2: HTML 파싱 개선
```python
# market_kr.py의 _parse_naver() 함수 개선
def _parse_naver(html: str) -> Dict[str, float]:
    # 1. 큰 숫자만 찾기 (가격은 보통 100 이상)
    # 2. 음수 제외
    # 3. 특정 HTML 구조에서 가격 위치 찾기
    # 4. 실패 시 JSON API로 fallback
```

### 우선순위 3: 네이버 JSON API 우선 사용
```python
# market_unified.py에서
# 1. 먼저 fetch_kr_indices() (JSON API) 시도
# 2. 실패 시 fetch_from_naver() (HTML 파싱) fallback
# 3. 둘 다 실패 시 캐시 사용
```

### 우선순위 4: 캐시 검증
```python
# 캐시에서 데이터를 가져올 때도 검증
def get_cache(seg: str) -> Tuple[List[Dict[str, Any]], bool]:
    cached, fresh = _load_cache(seg)
    # 가격이 유효한지 검증
    validated = [item for item in cached if item.get("price", 0) > 0]
    return validated, fresh
```

## 🔧 즉시 적용 가능한 임시 수정

### 방법 1: 가격 필터링 추가
```python
# market_kr.py의 fetch_from_naver() 함수
def fetch_from_naver() -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for sym, url in K_NAV.items():
        try:
            r = requests.get(url, headers=UA, timeout=6)
            if r.status_code != 200:
                log.warning("naver %s %s", sym, r.status_code); continue
            d = _parse_naver(r.text)
            price = d.get("price", 0)
            # 음수나 0인 가격은 무시
            if price <= 0:
                log.warning("naver %s invalid price: %s", sym, price)
                continue
            out.append({
                "symbol": sym,
                "name": sym,
                "price": price,
                "change": 0,
                "changeRate": 0,
                "time": None,
            })
        except Exception as e:
            log.warning("naver err %s: %s", sym, e)
    return out
```

### 방법 2: normalize_item에서 검증
```python
# market_common.py의 normalize_item() 함수
def normalize_item(raw: Dict[str, Any]) -> Dict[str, Any]:
    # ... 기존 코드 ...
    price = float(raw.get("price") or raw.get("close") or raw.get("now") or raw.get("last") or 0)
    # 가격 검증: 음수나 0이면 0으로 설정 (또는 None으로 해서 필터링)
    if price <= 0:
        price = 0.0
    return {
        "symbol": canon,
        "name": name,
        "price": price,
        # ... 나머지 ...
    }
```

## 📝 참고 파일 목록

1. **`market_kr.py`** - KR 시장 데이터 파싱 (HTML)
2. **`market_unified.py`** - 통합 라우터 (현재 HTML 파싱 사용)
3. **`market_common.py`** - 공통 유틸리티 (정규화, 캐시)
4. **`naver_indices.py`** - 네이버 JSON API 파서 (현재 미사용)
5. **`market_world.py`** - US 시장 데이터 (비슷한 문제 가능성)

## 🎯 권장 해결 순서

1. **즉시**: `normalize_item()`에 가격 검증 추가 (음수/0 필터링)
2. **단기**: `fetch_from_naver()`에서 가격 검증 추가
3. **중기**: `naver_indices.py`의 JSON API를 우선 사용하도록 변경
4. **장기**: HTML 파싱 로직 개선 또는 완전히 JSON API로 전환

