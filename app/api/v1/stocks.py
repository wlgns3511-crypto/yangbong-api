"""주식 API 라우터"""

from fastapi import APIRouter, Query, HTTPException
from app.models.stocks import MarketType
from app.models.schemas import APIResponse
from app.services.stocks_service import StocksService

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("/popular")
async def get_popular_stocks(
    market: MarketType = Query(..., description="시장 (KR|US)"),
    limit: int = Query(default=6, ge=1, le=100, description="조회 개수")
) -> APIResponse:
    """인기 주식 조회"""
    try:
        data = await StocksService.get_popular_stocks(market, limit)
        return APIResponse.success_response(data)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


@router.get("/surging")
async def get_surging_stocks(
    limit: int = Query(default=6, ge=1, le=100, description="조회 개수"),
    mix: bool = Query(default=True, description="KR/US 믹스 여부")
) -> APIResponse:
    """급등 주식 조회"""
    try:
        data = await StocksService.get_surging_stocks(limit, mix)
        return APIResponse.success_response(data)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

