# apps/api/market_kr.py
from fastapi import APIRouter
from .vendors.kis import kis_get
import time

router = APIRouter(prefix="/market", tags=["market"])

# 👉 여기 두 줄만 KIS 문서의 실제 경로/파라미터로 바꿔줘
PATH_INDEX = "/uapi/domestic-stock/v1/market-index"  # 문서 기준 실제 경로로 교체
KR_INDICES = [
    {"id": "KOSPI", "name": "코스피", "params": {"FID_COND_MRKT_DIV_CODE": "U"}},  # 예시
    {"id": "KOSDAQ", "name": "코스닥", "params": {"FID_COND_MRKT_DIV_CODE": "J"}},  # 예시
    {"id": "KPI200", "name": "코스피200", "params": {"FID_COND_MRKT_DIV_CODE": "K"}},  # 예시
]

_cache = {"ts": 0, "data": None}
TTL = 10


def _norm(row: dict) -> dict:
    price = row.get("bstp_nmix_prpr") or row.get("closePrice") or row.get("prpr")
    chg = row.get("bstp_nmix_prdy_vrss") or row.get("compareToPreviousClosePrice") or row.get("prdy_vrss")
    pct = row.get("bstp_nmix_prdy_ctrt") or row.get("fluctuationsRatio") or row.get("prdy_ctrt")

    def f(x):
        try:
            return float(x)
        except:
            return None

    return {"close": f(price), "change": f(chg), "pct": f(pct)}


@router.get("/kr")
def market_kr():
    now = time.time()
    if _cache["data"] and now - _cache["ts"] < TTL:
        return _cache["data"]

    items = []
    for it in KR_INDICES:
        try:
            j = kis_get(PATH_INDEX, it["params"])
            out = j.get("output") or j.get("result") or j
            row = out[0] if isinstance(out, list) and out else out
            items.append({"id": it["id"], "name": it["name"], **_norm(row or {})})
        except Exception as e:
            # KIS API 오류 시 해당 지수는 스킵하고 계속 진행
            items.append({"id": it["id"], "name": it["name"], "close": None, "change": None, "pct": None})

    _cache["ts"] = now
    _cache["data"] = {"ok": True, "source": "kis", "items": items}
    return _cache["data"]
