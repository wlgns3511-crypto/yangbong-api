# apps/api/market_kr.py
from fastapi import APIRouter
from .kis_client import get_index
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/market/kr")
def get_market_kr():
    """국내 지수 API (KOSPI, KOSDAQ, KOSPI200)"""
    data = []

    # ✅ 코스피
    kospi = get_index("U", "0001")
    if kospi:
        data.append({**kospi, "symbol": "KOSPI"})

    # ✅ 코스닥
    kosdaq = get_index("J", "1001")
    if kosdaq:
        data.append({**kosdaq, "symbol": "KOSDAQ"})

    # ✅ 코스피200
    kospi200 = get_index("U", "2001")
    if kospi200:
        data.append({**kospi200, "symbol": "KOSPI200"})

    if not data:
        logger.warning("[KIS] 국내 지수 전부 조회 실패")
        return {"data": [], "error": "no data"}

    return {"data": data}
