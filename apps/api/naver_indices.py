# apps/api/naver_indices.py

from __future__ import annotations

import re

from typing import Dict, Tuple

import httpx

from bs4 import BeautifulSoup



UA = (

    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "

    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

)



# 네이버 지수 페이지

NAVER_URLS: Dict[str, str] = {

    "KOSPI":  "https://finance.naver.com/sise/sise_index.naver?code=KOSPI",

    "KOSDAQ": "https://finance.naver.com/sise/sise_index.naver?code=KOSDAQ",

    "KOSPI200": "https://finance.naver.com/sise/sise_index.naver?code=KPI200",

}



def _parse_number(text: str) -> float:

    t = text.strip().replace(",", "")

    # 1,234.56 ▲ 12.3 같은 꼬리표 제거

    t = re.sub(r"[^\d\.\-\+]", "", t)

    return float(t) if t else 0.0



def _extract_from_dom(html: str) -> Tuple[float, float]:

    """

    네이버 DOM 구조 변화에 대비해서 2가지 방식으로 시도:

    1) 주요 값 영역의 숫자들(span/strong)에서 현재가 근처 값을 추정

    2) 스크립트 내 임베디드 데이터의 'now'/'changeRate' 패턴 정규식

    """

    soup = BeautifulSoup(html, "lxml")



    # 1) 화면에 보이는 현재가/등락률 후보들 긁기

    #   - 코스피/코스닥 페이지는 보통 현재가가 .num 또는 .num_sise 영역에 큼직하게 표시됨

    for sel in ["#now_value", "strong#now_value", ".num .num", ".num", ".price", ".now", "em#nowVal", "em#_nowVal"]:

        el = soup.select_one(sel)

        if el and el.get_text(strip=True):

            now_val = _parse_number(el.get_text())

            # 등락률은 퍼센트 기호 있는 첫 요소 추정

            pct_el = soup.find(string=re.compile(r"%"))

            if pct_el:

                pct = _parse_number(pct_el)

                return now_val, pct



    # 2) 스크립트 내 JSON 유사 데이터에서 now/changeRate 뽑기

    m_now = re.search(r'"now"\s*:\s*([0-9\.\-]+)', html)

    m_pct = re.search(r'"changeRate"\s*:\s*([0-9\.\-]+)', html)

    if m_now and m_pct:

        return float(m_now.group(1)), float(m_pct.group(1))



    # 3) 백업: 가장 큰 숫자를 현재가로, 그 다음 %가 있는 첫 숫자를 등락률로 가정

    nums = [ _parse_number(x.get_text()) for x in soup.find_all(text=True) if re.search(r"\d", x) ]

    now_guess = max(nums) if nums else 0.0

    pct_match = re.search(r"([+\-]?\d+(\.\d+)?)\s*%", html)

    pct_guess = float(pct_match.group(1)) if pct_match else 0.0

    return now_guess, pct_guess



async def fetch_index(session: httpx.AsyncClient, name: str) -> Dict:

    url = NAVER_URLS[name]

    r = await session.get(url, headers={"User-Agent": UA}, timeout=10)

    r.raise_for_status()

    now, pct = _extract_from_dom(r.text)

    return {

        "name": name,

        "price": now,

        "changeRate": pct,

        "time": None,

    }



async def fetch_kr_indices() -> Dict:

    """

    네이버 1순위로 KOSPI/KOSDAQ/KOSPI200 동시 수집.

    """

    out = {"ok": True, "items": [], "error": None, "miss": []}

    async with httpx.AsyncClient(follow_redirects=True, headers={"User-Agent": UA}) as client:

        for name in ("KOSPI", "KOSDAQ", "KOSPI200"):

            try:

                item = await fetch_index(client, name)

                if item["price"] == 0:

                    out["miss"].append({"name": name, "status": 0, "raw": "parse_zero"})

                out["items"].append(item)

            except Exception as e:

                out["miss"].append({"name": name, "status": 500, "raw": str(e)})

    return out

