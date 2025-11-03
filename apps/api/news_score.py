import re
from datetime import datetime, timedelta

KEYWORDS = ["주식", "증시", "코스피", "코스닥", "비트코인", "ETF", "경제", "금리", "환율", "AI", "블록체인"]
GOOD_SOURCES = ["한국경제", "매일경제", "이데일리", "조선비즈", "이투데이", "머니투데이", "서울경제"]

def calc_score(news):
    score = 0
    title = news.get("title", "")
    summary = news.get("summary", "")
    source = news.get("source", "")
    published_at = news.get("published_at")

    # 키워드 매칭
    for kw in KEYWORDS:
        if kw in title or kw in summary:
            score += 5
            break

    # 신뢰도 높은 출처
    if any(s in source for s in GOOD_SOURCES):
        score += 5

    # 요약문 길이 (적당한 기사만)
    if 50 <= len(summary) <= 200:
        score += 3

    # 최신성 (24시간 이내)
    if published_at:
        if isinstance(published_at, datetime):
            pub_dt = published_at
        else:
            try:
                pub_dt = datetime.fromisoformat(str(published_at).replace("Z", "+00:00"))
                if pub_dt.tzinfo:
                    pub_dt = pub_dt.replace(tzinfo=None)
            except:
                pub_dt = datetime.utcnow()
        
        if (datetime.utcnow() - pub_dt) < timedelta(days=1):
            score += 5

    # 썸네일
    if news.get("thumbnail"):
        score += 2

    # 광고/홍보/스팸 감점
    if re.search(r"(이벤트|협찬|P2E|에어드롭|쿠폰|공동구매)", title + summary):
        score -= 10

    return max(score, 0)

