# apps/api/kis_client.py

import os

import time

import requests

import logging

from urllib.parse import urljoin



log = logging.getLogger("kis")

log.setLevel(logging.INFO)



KIS_BASE_URL = os.getenv("KIS_BASE_URL", "https://openapi.koreainvestment.com:9443")

KIS_APP_KEY = os.getenv("KIS_APP_KEY", "")

KIS_APP_SECRET = os.getenv("KIS_APP_SECRET", "")



_token = None

_token_exp = 0





def _auth_url() -> str:

    return urljoin(KIS_BASE_URL, "/oauth2/tokenP")





def get_access_token(force: bool = False) -> str:

    global _token, _token_exp

    now = time.time()

    if not force and _token and now < _token_exp - 30:

        return _token



    r = requests.post(_auth_url(), json={

        "grant_type": "client_credentials",

        "appkey": KIS_APP_KEY,

        "appsecret": KIS_APP_SECRET

    })

    r.raise_for_status()

    j = r.json()

    _token = j.get("access_token") or j.get("accessToken")

    _token_exp = now + int(j.get("expires_in", 900))

    log.info("[KIS] token ok (ttl=%ss)", int(j.get("expires_in", 900)))

    return _token





def _headers(tr_id: str):

    token = get_access_token()

    return {

        "authorization": f"Bearer {token}",

        "appkey": KIS_APP_KEY,

        "appsecret": KIS_APP_SECRET,

        "tr_id": tr_id,

        "custtype": "P",

    }





def get_index(market_div: str, code: str):

    """

    국내 지수 현재가 (정상 응답되는 TR)

    """

    # ✅ 엔드포인트 교체

    url = urljoin(KIS_BASE_URL, "/uapi/domestic-stock/v1/quotations/inquire-index")



    params = {

        "FID_COND_MRKT_DIV_CODE": market_div,  # "U" / "J"

        "FID_INPUT_ISCD": code,  # 0001, 1001, 2001

    }



    try:

        r = requests.get(url, headers=_headers("FHKUP03500100"), params=params, timeout=10)

        if r.status_code == 401:

            _ = get_access_token(force=True)

            r = requests.get(url, headers=_headers("FHKUP03500100"), params=params, timeout=10)

        if r.status_code == 404:

            log.warning("[KIS] 404 for %s %s", market_div, code)

            return {"_http": 404, "_raw": ""}

        return {"_http": r.status_code, "_json": r.json()}

    except Exception as e:

        log.exception("[KIS] error: %s", e)

        return {"_http": 0, "_err": str(e)}
