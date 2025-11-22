"""AI 서비스"""

from app.models.ai import MarketBriefingResponse
from datetime import datetime


class AIService:
    """AI 관련 비즈니스 로직"""

    @staticmethod
    async def get_market_briefing() -> MarketBriefingResponse:
        """마켓 브리핑 생성 (Mock 데이터)"""
        # TODO: 실제 OpenAI API 연동으로 교체
        # 예시: OpenAI API를 사용하여 마켓 뉴스와 데이터를 분석하여 브리핑 생성
        
        return MarketBriefingResponse(
            briefing=(
                "오늘 주요 시장은 상승세를 보였습니다. KOSPI는 전일 대비 0.61% 상승하며 2500선을 돌파했고, "
                "S&P 500은 0.57% 상승했습니다. 암호화폐 시장도 강세를 보이며 비트코인은 2% 이상 상승했습니다. "
                "기관 투자자들은 순매수로 전환했으며, 외국인 투자자들은 소폭 순매도를 기록했습니다."
            ),
            summary="주요 시장 전반적인 상승세, 기관 순매수 전환, 암호화폐 강세 지속",
            key_points=[
                "KOSPI 0.61% 상승, 2500선 돌파",
                "S&P 500 0.57% 상승, 기술주 강세",
                "비트코인 2% 이상 상승",
                "기관 투자자 순매수 전환",
            ],
            generated_at=datetime.utcnow().isoformat() + "Z",
        )

