"""API v1 라우터 통합"""

from fastapi import APIRouter
from app.api.v1 import market, stocks, ai, news

router = APIRouter(prefix="/api/v1")

router.include_router(market.router)
router.include_router(stocks.router)
router.include_router(ai.router)
router.include_router(news.router)
