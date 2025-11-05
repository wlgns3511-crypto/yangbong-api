# apps/api/market_nav.py

import re

import time

import random

import requests

from bs4 import BeautifulSoup

from fastapi import APIRouter, Query



router = APIRouter(prefix="/api", tags=["market_nav"])



UA_POOL = [

    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",

    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17 Safari/605.1.15",

]



KR_URLS = {

    "KOSPI":   "https://finance.naver.com/sise/sise_index.naver?code=KOSPI",

    "KOSDAQ":  "https://finance.naver.com/sise/sise_index.naver?code=KOSDAQ",

    "KOSPI200":"https://finance.naver.com/sise/sise_index.naver?code=KPI200",

}



US_URLS = {

    "다우":    "https://finance.naver.com/world/sise.naver?symbol=DJI@DJI",

    "나스닥":  "https://finance.naver.com/world/sise.naver?symbol=NAS@IXIC",

    "S&P500": "https://finance.naver.com/world/sise.naver?symbol=SPI@SPX",

    # 필요하면 유럽/아시아도 아래에 계속 추가 가능

    # "니케이225": "https://finance.naver.com/world/sise.naver?symbol=NII@NI225",

}



_NUM = re.compile(r"[-+]?[\d,]+(?:\.\d+)?")

_PCT = re.compile(r"[-+]?[\d.]+")



def _clean_num(s: str):

    if s is None: 

        return None

    m = _NUM.search(s.replace("\xa0"," ").replace(" ", ""))

    if not m: 

        return None

    try:

        return float(m.group(0).replace(",", ""))

    except:

        return None



def _clean_pct(s: str):

    if s is None: 

        return None

    s = s.replace("%", "")

    m = _PCT.search(s)

    if not m: 

        return None

    try:

        return float(m.group(0))

    except:

        return None



def _get_html(url: str) -> BeautifulSoup:

    headers = {"User-Agent": random.choice(UA_POOL)}

    r = requests.get(url, headers=headers, timeout=6)

    r.raise_for_status()

    return BeautifulSoup(r.text, "lxml")



def _pick_first_text(soup, selectors: list[str]):

    for sel in selectors:

        el = soup.select_one(sel)

        if el and el.get_text(strip=True):

            return el.get_text(strip=True)

    return None



def parse_kr(code_name: str, url: str):

    """

    네이버 국내 지수 페이지 공통 파서.

    페이지 구조 변경에 대비해 여러 셀렉터를 순차 시도.

    """

    s = _get_html(url)



    # 가격

    price_txt = _pick_first_text(s, [

        "#now_value",                              # 가장 흔함

        ".no_today .blind",                        # 대체

        ".num_s #now_value",                       # 변종

    ])



    # 전일대비 (절대값)

    chg_txt = _pick_first_text(s, [

        "#change_value",

        ".no_exday .no_up .blind",

        ".no_exday .no_down .blind",

        ".no_exday .blind",

        ".rate_info .change",                      # 변종

    ])



    # 등락률 (%)

    rate_txt = _pick_first_text(s, [

        "#change_rate",

        ".no_exday .no_up .no_exday .no_down .blind",

        ".no_exday em.blind",

        ".rate_info .change .rate",               # 변종

        ".no_exday .blind"

    ])



    price = _clean_num(price_txt)

    change = _clean_num(chg_txt)

    rate = _clean_pct(rate_txt)



    return {

        "name": code_name,

        "price": price if price is not None else 0.0,

        "change": change if change is not None else 0.0,

        "changeRate": rate if rate is not None else 0.0,

        "time": int(time.time())

    }



def parse_world(name: str, url: str):

    """

    네이버 해외 지수 페이지 공통 파서.

    """

    s = _get_html(url)



    price_txt = _pick_first_text(s, [

        "#last_current",                   # 가장 흔함

        ".price_area .num",                # 변종

        ".rate_info .num",                 # 변종

        ".no_today .blind",

    ])

    chg_txt = _pick_first_text(s, [

        "#last_change",

        ".rate_info .change",

        ".no_exday .blind",

    ])

    rate_txt = _pick_first_text(s, [

        "#last_change_rate",

        ".rate_info .change .rate",

        ".no_exday em.blind",

    ])



    price = _clean_num(price_txt)

    change = _clean_num(chg_txt)

    rate = _clean_pct(rate_txt)



    return {

        "name": name,

        "price": price if price is not None else 0.0,

        "change": change if change is not None else 0.0,

        "changeRate": rate if rate is not None else 0.0,

        "time": int(time.time())

    }



@router.get("/market")

def market(seg: str = Query(..., description="KR | US")):

    seg = seg.upper().strip()

    if seg == "KR":

        items = [parse_kr(k, u) for k, u in KR_URLS.items()]

        # 0값이 섞일 수 있으니, 모두 0이면 실패로 간주할 수도 있음(원하면 로직 추가)

        return {"ok": True, "seg": "KR", "source": "Naver", "items": items}



    if seg == "US":

        items = [parse_world(k, u) for k, u in US_URLS.items()]

        return {"ok": True, "seg": "US", "source": "Naver", "items": items}



    return {"ok": False, "error": "unsupported seg (use KR or US)"}

