# apps/api/kis_client.py
import os
import time
import requests
import logging
from urllib.parse import urljoin

log = logging.getLogger("kis_client")

KIS_BASE = os.getenv("KIS_BASE_URL", "https://openapi.koreainvestment.com:9443")
APP_KEY = os.getenv("KIS_APP_KEY", "")
APP_SECRET = os.getenv("KIS_APP_SECRET", "")

_token_cache = {"access_token": None, "expires_at": 0}


def _token_alive() -> bool:
    return _token_cache["access_token"] and _token_cache["expires_at"] - time.time() > 30


def get_access_token() -> str:
    if _token_alive():
        return _token_cache["access_token"]

    url = urljoin(KIS_BASE, "/oauth2/tokenP")
    headers = {"content-type": "application/json; charset=utf-8"}
    payload = {
        "grant_type": "client_credentials",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
    }
    r = requests.post(url, json=payload, headers=headers, timeout=10)
    r.raise_for_status()
    data = r.json()
    access_token = data.get("access_token") or data.get("accessToken")
    expires_in = data.get("expires_in", 300)
    if not access_token:
        raise RuntimeError(f"Token response missing access_token: {data}")
    _token_cache.update(
        {"access_token": access_token, "expires_at": time.time() + int(expires_in)}
    )
    return access_token


def _auth_headers(tr_id: str) -> dict:
    return {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {get_access_token()}",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
        "tr_id": tr_id,
        "custtype": "P",
    }


def get_index(fid_cond_mrkt_div_code: str, fid_input_iscd: str) -> dict:
    """
    지수 시세 조회
    - fid_cond_mrkt_div_code: 'U' (통합)
    - fid_input_iscd: '0001'(코스피), '1001'(코스닥), '2001'(코스피200)
    """
    path = "/uapi/domestic-stock/v1/quotations/inquire-index"
    url = urljoin(KIS_BASE, path)

    tr_candidates = [
        "FHKST03010100",   # ✅ 지수 조회 정식 TR
        "FHKUP03500100",   # 보조
        "CTCA0903R",       # 폴백
    ]

    # ✅ 여기를 모두 소문자로 수정
    params = {
        "fid_cond_mrkt_div_code": fid_cond_mrkt_div_code,
        "fid_input_iscd": fid_input_iscd,
    }

    last_err = None
    for tr in tr_candidates:
        try:
            headers = _auth_headers(tr)
            log.info(f"Trying KIS: url={url}, tr_id={tr}, params={params}")
            r = requests.get(url, headers=headers, params=params, timeout=10)
            log.info(f"KIS response: status={r.status_code}, headers={dict(r.headers)}")
            if r.status_code == 200:
                result = r.json()
                log.info(f"KIS success: tr_id={tr}, result keys={list(result.keys()) if isinstance(result, dict) else 'not dict'}")
                return result
            # 디버깅에 도움되도록 본문 함께 남김
            response_text = r.text[:500] if r.text else "(empty)"
            last_err = (r.status_code, response_text)
            log.warning(f"KIS failed: tr_id={tr}, status={r.status_code}, body={response_text}")
        except requests.RequestException as e:
            last_err = (None, str(e))
            log.error(f"KIS request exception: tr_id={tr}, error={e}")

    raise RuntimeError(f"KIS error: {last_err}")
