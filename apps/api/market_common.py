from __future__ import annotations

import json, os, time, math

from typing import Any, Dict, List, Tuple

import logging

log = logging.getLogger(__name__)



CACHE_PATH = os.environ.get("MARKET_CACHE_PATH", "/tmp/market_cache.json")

TTL_SEC = int(os.environ.get("MARKET_TTL_SEC", "90"))



CANON = {

    "KOSPI": ["코스피","KS11"],

    "KOSDAQ": ["코스닥"],

    "KOSPI200": ["코스피200","KPI200"],

    "DJI": ["DOW","다우","DJI@DJI","^DJI"],

    "IXIC": ["NASDAQ","나스닥","NAS@IXIC","^IXIC"],

    "GSPC": ["SPX","S&P500","SNP","S&P","^GSPC"],

}



def _norm(s: str|None) -> str:

    return (s or "").strip().upper()



REV = {k:k for k in CANON.keys()}

for c, aliases in CANON.items():

    for a in aliases: REV[_norm(a)] = c



def canonicalize(s: str|None) -> str:

    k = _norm(s)

    return REV.get(k, k)



def _is_valid_price(x) -> bool:

    try:

        v = float(x)

    except Exception:

        return False

    # 음수/0/NaN/Inf/비현실적 값 차단

    if not math.isfinite(v):

        return False

    if v <= 0:

        return False

    # 10억 같은 비정상 값도 가드 (지수 범위 가정)

    if v > 10_000_000:

        return False

    return True



def _load() -> Dict[str, Any]:

    if not os.path.exists(CACHE_PATH):

        return {}

    try:

        with open(CACHE_PATH, "r", encoding="utf-8") as f:

            return json.load(f)

    except Exception:

        return {}



def _dump(obj: Dict[str, Any]) -> None:

    tmp = CACHE_PATH + ".tmp"

    try:

        with open(tmp, "w", encoding="utf-8") as f:

            json.dump(obj, f, ensure_ascii=False)

        os.replace(tmp, CACHE_PATH)

    except Exception:

        pass



def _filter_valid(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:

    """유효한 가격을 가진 아이템만 필터링"""

    return [it for it in items if it and isinstance(it, dict) and it.get("price") is not None and _is_valid_price(it.get("price"))]



def get_cache(seg: str) -> Tuple[List[Dict[str, Any]], bool]:

    store = _load()

    entry = store.get(seg.upper())

    if not entry: return [], False

    age = int(time.time()) - int(entry.get("ts", 0))

    items = entry.get("items", [])

    # 로드 시에도 한번 더 필터

    items = _filter_valid(items)

    return items, age <= TTL_SEC



def set_cache(seg: str, items: List[Dict[str, Any]]) -> None:

    # 유효한 데이터만 저장

    items = _filter_valid(items)

    store = _load()

    store[seg.upper()] = {"ts": int(time.time()), "items": items}

    _dump(store)



def normalize_item(raw: Dict[str, Any]) -> Dict[str, Any]:

    sym = raw.get("symbol") or raw.get("code") or raw.get("name") or ""

    name = raw.get("name") or sym

    canon = canonicalize(sym) or canonicalize(name)

    src_price = raw.get("price") or raw.get("close") or raw.get("now") or raw.get("last")

    price = float(src_price) if _is_valid_price(src_price) else 0.0

    out = {

        "symbol": canon,

        "name": name,

        "price": price,

        "change": float(raw.get("change") or raw.get("diff") or 0),

        "changeRate": float(raw.get("changeRate") or raw.get("rate") or 0),

        "time": raw.get("time") or raw.get("updatedAt") or raw.get("ts") or None,

    }

    # 최종 검증: 가격이 유효하지 않으면 None 마킹 (상위 레이어에서 필터)

    if not _is_valid_price(out["price"]):

        log.warning("normalize_item invalid price: %s (%s)", out["price"], raw)

        out["price"] = None

    return out

