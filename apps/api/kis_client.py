# apps/api/kis_client.py

import os

import time

import logging

from typing import Dict, Any, Optional

import requests

from urllib.parse import urljoin



log = logging.getLogger("kis")

log.setLevel(logging.INFO)



KIS_BASE_URL = os.getenv("KIS_BASE_URL", "https://openapi.koreainvestment.com:9443")

KIS_APP_KEY = os.getenv("KIS_APP_KEY", "")

KIS_APP_SECRET = os.getenv("KIS_APP_SECRET", "")

KIS_SCOPE = os.getenv("KIS_SCOPE", "real")  # "real" / "vps" 등



# 토큰 캐시

_token: Optional[str] = None

_token_exp: float = 0





def _auth_url() -> str:

    # 실계좌용 토큰 엔드포인트

    # (모듈/버전에 따라 /oauth2/tokenP /oauth2/token 둘 다 보이지만, 문자 수신 기준 실계좌면 tokenP 사용)

    return urljoin(KIS_BASE_URL, "/oauth2/tokenP")





def get_access_token(force: bool = False) -> str:

    global _token, _token_exp

    now = time.time()

    if not force and _token and now < _token_exp - 30:

        return _token



    body = {

        "grant_type": "client_credentials",

        "appkey": KIS_APP_KEY,

        "appsecret": KIS_APP_SECRET,

    }

    r = requests.post(_auth_url(), json=body, timeout=10)

    r.raise_for_status()

    j = r.json()

    # 표준 키 이름은 access_token / expires_in(초)

    _token = j.get("access_token") or j.get("accessToken")

    expires_in = int(j.get("expires_in", 900))

    _token_exp = now + expires_in

    log.info("[KIS] token ok, ttl=%ss", expires_in)

    return _token





def _headers(tr_id: str) -> Dict[str, str]:

    token = get_access_token()

    return {

        "authorization": f"Bearer {token}",

        "appkey": KIS_APP_KEY,

        "appsecret": KIS_APP_SECRET,

        "tr_id": tr_id,

        "custtype": "P",  # 개인

    }





def get_index(market_div: str, code: str) -> Dict[str, Any]:

    """

    KIS 국내 '지수' 현재가: 일봉차트가 아닌 '지수 현재가' 계열은 404가 떠서

    공식 지수 차트가 제공되는 엔드포인트로 조회한다.

    - FID_COND_MRKT_DIV_CODE: 'U'(유가) / 'J'(코스닥)

    - FID_INPUT_ISCD: '0001'(KOSPI), '1001'(KOSDAQ), '2001'(KOSPI200)

    """

    # ✅ 지수용 엔드포인트

    path = "/uapi/domestic-stock/v1/quotations/inquire-daily-indexchartprice"

    url = urljoin(KIS_BASE_URL, path)



    params = {

        "FID_COND_MRKT_DIV_CODE": market_div,

        "FID_INPUT_ISCD": code,

    }

    # 지수 조회용 TR

    tr_id = "FHKUP03500100"



    try:

        r = requests.get(url, headers=_headers(tr_id), params=params, timeout=10)

        if r.status_code == 401:

            # 토큰 갱신 후 1회 재시도

            _ = get_access_token(force=True)

            r = requests.get(url, headers=_headers(tr_id), params=params, timeout=10)



        if r.status_code == 404:

            log.warning("[KIS] 404 for %s %s (tr_id=%s) body=%s", market_div, code, tr_id, r.text)

            return {"_http": 404, "_raw": r.text or ""}



        r.raise_for_status()

        j = r.json()

        return {"_http": r.status_code, "_json": j}



    except requests.RequestException as e:

        log.exception("[KIS] exception for %s %s: %s", market_div, code, e)

        return {"_http": 0, "_err": str(e)}
