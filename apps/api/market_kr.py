# apps/api/market_kr.py
from fastapi import APIRouter, HTTPException
from .kis_client import get_index

router = APIRouter(prefix="/market", tags=["market-kr"])

@router.get("/kr")
def market_kr():
    try:
        kospi = get_index("U", "0001")
        kosdaq = get_index("U", "1001")
        kospi200 = get_index("U", "2001")
        return {
            "ok": True,
            "source": "kis",
            "items": [
                {"label": "코스피", "raw": kospi},
                {"label": "코스닥", "raw": kosdaq},
                {"label": "코스피200", "raw": kospi200},
            ],
        }
    except Exception as e:
        # KIS 원문 에러를 그대로 보여주면 문제 원인 파악이 쉬움
        raise HTTPException(status_code=502, detail=str(e))
