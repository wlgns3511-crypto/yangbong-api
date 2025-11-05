# apps/api/market_kr.py
from fastapi import APIRouter, Query
from .kis_client import get_index
import logging

router = APIRouter(prefix="/api/market", tags=["market"])
logger = logging.getLogger(__name__)


@router.get("/kr")
def get_market_kr(seg: str = Query("KR", description="세그먼트 (KR만 지원)")):
    """국내 지수 조회: KOSPI, KOSDAQ, KOSPI200"""
    if seg != "KR":
        return {"error": "invalid seg", "data": []}

    data = []

    # ✅ KOSPI
    kospi = get_index("U", "0001")
    if kospi:
        data.append({**kospi, "symbol": "KOSPI"})

    # ✅ KOSDAQ
    kosdaq = get_index("J", "1001")
    if kosdaq:
        data.append({**kosdaq, "symbol": "KOSDAQ"})

    # ✅ KOSPI200
    kospi200 = get_index("U", "2001")
    if kospi200:
        data.append({**kospi200, "symbol": "KOSPI200"})

    return {"ok": True, "data": data, "items": data}  # 호환성 유지
