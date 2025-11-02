# apps/api/market_kr.py
from fastapi import APIRouter
from .kis_client import get_index
import time
import logging

log = logging.getLogger("market_kr")

router = APIRouter(prefix="/market", tags=["market"])

TTL = 30
_cache = {"ts": 0, "data": None}

CODES = {
    "KOSPI": "0001",
    "KOSDAQ": "1001",
    "KOSPI200": "2001",
}

@router.get("/kr")
def market_kr(cache: int = 1):
    now = time.time()
    if cache and _cache["data"] and now - _cache["ts"] < TTL:
        return _cache["data"]

    items = []
    for name, code in CODES.items():
        try:
            log.info(f"Fetching index: {name} (code={code})")
            res = get_index("U", code)
            log.info(f"Got response for {name}: keys={list(res.keys()) if isinstance(res, dict) else 'not dict'}")
            output = res.get("output", {})
            if not output:
                log.warning(f"No 'output' key in response for {name}: response={res}")
                items.append({"id": name, "error": f"No output in response: {list(res.keys())}"})
            else:
                items.append({
                    "id": name,
                    "name": output.get("bstp_nmix_prpr_name") or name,
                    "close": float(output.get("bstp_nmix_prpr") or 0),
                    "change": float(output.get("prdy_vrss") or 0),
                    "pct": float(output.get("prdy_ctrt") or 0),
                })
        except Exception as e:
            log.error(f"Error fetching {name}: {e}", exc_info=True)
            items.append({"id": name, "error": str(e)})

    payload = {"ok": True, "source": "KIS", "items": items}
    _cache.update({"ts": now, "data": payload})
    return payload
