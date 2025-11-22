"""AI API 라우터"""

from fastapi import APIRouter, HTTPException
from app.models.schemas import APIResponse
from app.services.ai_service import AIService

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/market-briefing")
async def get_market_briefing() -> APIResponse:
    """마켓 브리핑 생성"""
    try:
        data = await AIService.get_market_briefing()
        return APIResponse.success_response(data)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

