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
KIS_VIRTUAL = os.getenv("KIS_VIRTUAL", "0") == "1"  # 가상계좌 여부

# 표준/대체 TR
TR_IDS = [
    "FHKUP03500100",  # 표준
    "CTCA0903R",      # 대체
]

_TOKEN_CACHE = {"token": None, "exp": 0}


def _get_token() -> str:
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
            return None
    except Exception as e:
        logger.warning(f"[KIS] token error: {e}")
        return None


def _headers(tr_id: str) -> dict:
    tok = _get_token()
    return {
        "authorization": f"Bearer {tok}" if tok else "",
        "appkey": KIS_APP_KEY,
        "appsecret": KIS_APP_SECRET,
        "tr_id": tr_id,
        "custtype": "P",
        "Content-Type": "application/json",
    }


def get_access_token() -> str:
    """호환성을 위한 래퍼 함수"""
    return _get_token() or ""


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
        res = requests.get(url, headers=_headers("HHDFS00000300"),
                         params=params, timeout=10)
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


def get_index(mkt: str, code: str):
    """
    KIS 지수 호가 조회.
    실패(404/empty 등) 시 예외를 던지지 않고 None 반환.
    mkt: "U"(코스피), "J"(코스닥) 등 KIS 입력에 맞게 사용 중인 값 유지
    code: 지수 코드
    """
    endpoint = "/uapi/domestic-stock/v1/quotations/inquire-index-price"
    url = urljoin(KIS_BASE, endpoint)
    payload = {"FID_COND_MRKT_DIV_CODE": mkt, "FID_INPUT_ISCD": code}

    last_err = None
    for tr_id in TR_IDS:
        try:
            res = requests.get(url, headers=_headers(tr_id), params=payload, timeout=10)
            if res.status_code == 404:
                # 종종 body가 (empty)로 옴
                logger.warning(f"[KIS] 404 for {code} (tr_id={tr_id}) body=({res.text})")
                last_err = "404"
                continue
            res.raise_for_status()
            js = res.json()
            # KIS 성공 구조에 맞춰 추출 (필드명 프로젝트에 맞게 유지)
            output = js.get("output", {})
            now_prc = output.get("bstp_nmix_prpr") or output.get("prpr")
            prdy_vrss = output.get("prdy_vrss")  # 전일 대비
            prdy_ctrt = output.get("prdy_ctrt")  # 등락률(%)

            if now_prc is None:
                logger.warning(f"[KIS] output missing price for {code}: {js}")
                return None

            return {
                "output": {
                    "bstp_nmix_prpr": str(now_prc),
                    "prdy_vrss": str(prdy_vrss) if prdy_vrss not in (None, "") else None,
                    "prdy_ctrt": str(prdy_ctrt) if prdy_ctrt not in (None, "") else None,
                },
                "source": "KIS",
            }
        except Exception as e:
            last_err = e
            logger.warning(f"[KIS] Error for {code}: {e}")
            time.sleep(0.2)

    logger.warning(f"[KIS] All TRs failed for {code}: {last_err}")
    return None
