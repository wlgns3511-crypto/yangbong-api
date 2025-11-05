# apps/api/kis_client.py
import os
import time
import logging
from urllib.parse import urljoin

import requests

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

KIS_BASE = os.getenv("KIS_BASE", "https://openapi.koreainvestment.com:9443")
KIS_APP_KEY = os.getenv("KIS_APP_KEY", "")
KIS_APP_SECRET = os.getenv("KIS_APP_SECRET", "")

# ✅ 지수용 TR ID
TR_ID_INDEX = "FHKUP03500100"

_TOKEN_CACHE = {"token": None, "exp": 0}


def get_access_token() -> str:
    """KIS 인증 토큰 발급 및 캐싱"""
    now = int(time.time())
    if _TOKEN_CACHE["token"] and now < _TOKEN_CACHE["exp"] - 30:
        return _TOKEN_CACHE["token"]

    url = urljoin(KIS_BASE, "/oauth2/tokenP")
    data = {
        "grant_type": "client_credentials",
        "appkey": KIS_APP_KEY,
        "appsecret": KIS_APP_SECRET,
    }
    try:
        res = requests.post(url, json=data, timeout=10)
        res.raise_for_status()
        js = res.json()
        token = js.get("access_token")
        expires_in = int(js.get("expires_in", 0)) or 3600
        if token:
            _TOKEN_CACHE["token"] = token
            _TOKEN_CACHE["exp"] = now + expires_in
            logger.info("[KIS] token refreshed")
            return token
        else:
            logger.warning(f"[KIS] token response without token: {js}")
            return ""
    except Exception as e:
        logger.warning(f"[KIS] token error: {e}")
        return ""


def kis_api(tr_id: str, params: dict):
    """KIS API 호출 공통 함수"""
    token = get_access_token()
    headers = {
        "authorization": f"Bearer {token}",
        "appkey": KIS_APP_KEY,
        "appsecret": KIS_APP_SECRET,
        "tr_id": tr_id,
        "custtype": "P",
        "Content-Type": "application/json",
    }

    url = urljoin(KIS_BASE, "/uapi/domestic-stock/v1/quotations/inquire-index-price")
    res = requests.get(url, headers=headers, params=params, timeout=5)
    
    if res.status_code != 200:
        raise RuntimeError(f"KIS HTTP {res.status_code}: {res.text}")
    
    data = res.json()
    return data


def get_index(mrkt: str, code: str):
    """
    국내 지수 조회
    mrkt: "U" (코스피/코스피200) or "J" (코스닥)
    code: "0001" (코스피), "1001" (코스닥), "2001" (코스피200)
    """
    try:
        params = {
            "FID_COND_MRKT_DIV_CODE": mrkt,  # "U" or "J"
            "FID_INPUT_ISCD": code,           # "0001", "1001", "2001"
        }
        res = kis_api(TR_ID_INDEX, params)

        output = res.get("output", {})
        if not output:
            logger.warning(f"[KIS] output missing for {code}: {res}")
            return None

        return {
            "name": output.get("IDX_NM", ""),
            "price": float(output.get("BAS_PRC", 0)),
            "change": float(output.get("CMPPREVDD_PRC", 0)),
            "rate": float(output.get("FLUC_RT", 0)),
            "time": output.get("BSTP_NM", ""),
        }

    except Exception as e:
        logger.error(f"[KIS] Error for {code}: {e}")
        return None


def get_overseas_price(excd: str, symb: str) -> dict:
    """
    해외주식 현재체결가 (v1_해외주식-009)
    ex) EXCD: NAS/NYS/AMS/HKS/TSE ... , SYMB: AAPL, SPY, QQQ, 2800, 1321 등
    실패 시 예외를 던지지 않고 빈 dict 반환
    """
    path = "/uapi/overseas-price/v1/quotations/price"
    url = urljoin(KIS_BASE, path)
    params = {"AUTH": "", "EXCD": excd, "SYMB": symb}

    try:
        token = get_access_token()
        headers = {
            "authorization": f"Bearer {token}",
            "appkey": KIS_APP_KEY,
            "appsecret": KIS_APP_SECRET,
            "tr_id": "HHDFS00000300",
            "custtype": "P",
            "Content-Type": "application/json",
        }
        res = requests.get(url, headers=headers, params=params, timeout=10)
        res.raise_for_status()
        j = res.json()

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
    except Exception as e:
        logger.warning(f"[KIS] overseas price error for {excd}/{symb}: {e}")
        return {
            "raw": {},
            "price": None,
            "change": None,
            "pct": None,
        }
