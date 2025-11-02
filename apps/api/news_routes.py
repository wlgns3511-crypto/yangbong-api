from fastapi import APIRouter, Query
from typing import List, Dict, Any

router = APIRouter(prefix="/news", tags=["news"])

@router.get("")
def get_news(limit: int = Query(3, ge=1, le=50)) -> List[Dict[str, Any]]:
    # TODO: 실제 크롤러/피드 연동하기
    return []  # 일단 빈 배열이라도 반환하면 404는 사라짐
