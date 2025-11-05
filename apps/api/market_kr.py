# apps/api/market_kr.py
from fastapi import APIRouter
from .kis_client import get_index
import logging

router = APIRouter(prefix="/api/market", tags=["market"])
logger = logging.getLogger(__name__)


@router.get("/kr")
def get_market_kr():
    """국내 지수 API (KOSPI, KOSDAQ, KOSPI200)"""
    mapping = [
        ("KOSPI",   "U", "0001"),
        ("KOSDAQ",  "J", "1001"),
        ("KOSPI200","U", "2001"),
    ]
    
    out, errs = [], []
    
    for name, mrkt, code in mapping:
        status, payload, raw = get_index(mrkt, code)
        
        if status == 200 and payload and payload.get("output"):
            o = payload["output"]
            out.append({
                "name": name,
                "symbol": name,  # 프론트엔드 호환성
                "price": float(o.get("bstp_nmix_prpr") or 0),   # 지수 현재가
                "changeRate": float(o.get("prdy_ctrt") or 0),   # 등락률(%)
                "change": float(o.get("prdy_vrss") or 0),    # 전일대비 (호환성)
                "rate": float(o.get("prdy_ctrt") or 0),   # 등락률(%) (호환성)
                "prevClose": float(o.get("prdy_vrss") or 0),    # 전일대비
                "time": o.get("stck_bsop_hour")                 # 시간
            })
        else:
            errs.append({"name": name, "status": status, "raw": raw})
    
    if out:
        return {"data": out, "error": None, "miss": errs}
    
    # 전부 실패 시
    return {"data": [], "error": "kis_no_data", "miss": errs}
