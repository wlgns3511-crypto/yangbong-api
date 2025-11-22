"""마켓 API 라우터"""

from fastapi import APIRouter, Query, HTTPException
from typing import Literal
from app.models.market import SegmentType
from app.models.schemas import APIResponse
from app.services.market_service import MarketService

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/summary")
async def get_market_summary(
    seg: SegmentType = Query(..., description="세그먼트 (KR|US|CRYPTO|COMMO)")
) -> APIResponse:
    """마켓 요약 조회"""
    try:
        data = await MarketService.get_market_summary(seg)
        return APIResponse.success_response(data)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


@router.get("/sectors")
async def get_market_sectors(
    seg: SegmentType = Query(..., description="세그먼트 (KR|US|CRYPTO|COMMO)")
) -> APIResponse:
    """마켓 섹터 조회"""
    try:
        data = await MarketService.get_market_sectors(seg)
        return APIResponse.success_response(data)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


@router.get("/flow")
async def get_market_flow(
    seg: SegmentType = Query(..., description="세그먼트 (KR|US|CRYPTO|COMMO)")
) -> APIResponse:
    """마켓 자금 흐름 조회"""
    try:
        data = await MarketService.get_market_flow(seg)
        return APIResponse.success_response(data)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

