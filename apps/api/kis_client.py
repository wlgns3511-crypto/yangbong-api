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
        log.debug("Using cached token")
        return _token_cache["access_token"]

    log.info("Fetching new access token")
    url = urljoin(KIS_BASE, "/oauth2/tokenP")
    headers = {"content-type": "application/json; charset=utf-8"}
    payload = {
        "grant_type": "client_credentials",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
    }
    
    log.debug(f"Token request: url={url}, appkey={APP_KEY[:8]}...")
    r = requests.post(url, json=payload, headers=headers, timeout=10)
    log.debug(f"Token response: status={r.status_code}")
    
    r.raise_for_status()
    data = r.json()
    access_token = data.get("access_token") or data.get("accessToken")
    expires_in = data.get("expires_in", 300)
    
    if not access_token:
        log.error(f"Token response missing access_token: {data}")
        raise RuntimeError(f"Token response missing access_token: {data}")
    
    log.info(f"Token obtained: expires_in={expires_in}, token_preview={access_token[:20]}...")
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
    log.info(f"[BEFORE REQUEST] get_index called: fid_cond_mrkt_div_code={fid_cond_mrkt_div_code}, fid_input_iscd={fid_input_iscd}")
    
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

    log.info(f"[BEFORE REQUEST] URL={url}, params={params}")

    last_err = None
    for tr in tr_candidates:
        try:
            log.info(f"[BEFORE REQUEST] Preparing auth headers for tr_id={tr}")
            headers = _auth_headers(tr)
            
            # 헤더 확인 (민감정보는 일부만 표시)
            log.info(f"[BEFORE REQUEST] Headers prepared: tr_id={headers.get('tr_id')}, custtype={headers.get('custtype')}, has_auth={bool(headers.get('authorization'))}, has_appkey={bool(headers.get('appkey'))}, has_appsecret={bool(headers.get('appsecret'))}")
            
            log.info(f"[BEFORE REQUEST] Sending request to KIS")
            r = requests.get(url, headers=headers, params=params, timeout=10)
            log.info(f"[AFTER REQUEST] Response received: status={r.status_code}")
            log.info(f"[AFTER REQUEST] Response headers: {dict(r.headers)}")
            
            if r.status_code == 200:
                result = r.json()
                log.info(f"[AFTER REQUEST] KIS success: tr_id={tr}, result keys={list(result.keys()) if isinstance(result, dict) else 'not dict'}")
                return result
            # 디버깅에 도움되도록 본문 함께 남김
            response_text = r.text[:500] if r.text else "(empty)"
            last_err = (r.status_code, response_text)
            log.warning(f"[AFTER REQUEST] KIS failed: tr_id={tr}, status={r.status_code}, body={response_text}")
        except requests.RequestException as e:
            last_err = (None, str(e))
            log.error(f"[AFTER REQUEST] KIS request exception: tr_id={tr}, error={e}", exc_info=True)

    log.error(f"[AFTER REQUEST] All tr_ids failed: {last_err}")
    raise RuntimeError(f"KIS error: {last_err}")


def get_overseas_price(excd: str, symb: str) -> dict:
    """
    해외주식 현재체결가 (v1_해외주식-009)
    ex) EXCD: NAS/NYS/AMS/HKS/TSE ... , SYMB: AAPL, SPY, QQQ, 2800, 1321 등
    """
    path = "/uapi/overseas-price/v1/quotations/price"
    url = urljoin(KIS_BASE, path)
    params = {"AUTH": "", "EXCD": excd, "SYMB": symb}

    r = requests.get(url, headers=_auth_headers("HHDFS00000300"),
                     params=params, timeout=10)
    r.raise_for_status()
    j = r.json()

    # output 스키마 보호적으로 파싱
    out = (j.get("output") or j.get("Output") or {})
    def num(keys, default=None):
        for k in keys:
            v = out.get(k)
            try:
                if v is None or v == "": 
                    continue
                return float(str(v).replace(',', ''))
            except Exception:
                continue
        return default

    price  = num(["last", "ovrs_now_prc", "last_prc"])
    change = num(["prdy_vrss", "net_chg", "ovrs_prdy_vrss"])
    pct    = num(["prdy_ctrt", "rate", "ovrs_prdy_ctrt"])

    return {
        "raw": j,                 # 디버깅용 원본
        "price": price,
        "change": change,
        "pct": pct,
    }
