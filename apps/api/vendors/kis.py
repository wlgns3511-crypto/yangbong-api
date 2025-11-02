# apps/api/vendors/kis.py
import os
import time
import threading
import requests
from typing import Any, Dict, Optional

APP_KEY = os.getenv("KIS_APP_KEY", "")
APP_SECRET = os.getenv("KIS_APP_SECRET", "")
BASE = os.getenv("KIS_BASE_URL", "https://openapi.koreainvestment.com:9443")

_token_lock = threading.Lock()
_token_cache: Dict[str, Any] = {"access_token": None, "exp": 0}


class KISAuthError(Exception):
    pass


class KISAPIError(Exception):
    pass


def _issue_token() -> Dict[str, Any]:
    url = f"{BASE}/oauth2/tokenP"
    body = {"grant_type": "client_credentials", "appkey": APP_KEY, "appsecret": APP_SECRET}
    r = requests.post(url, json=body, timeout=8)
    if r.status_code != 200:
        raise KISAuthError(f"token http={r.status_code} body={r.text}")
    j = r.json()
    access = j.get("access_token") or j.get("accessToken")
    exp_in = int(j.get("expires_in", 3600))
    if not access:
        raise KISAuthError(f"token parse fail: {j}")
    return {"access_token": access, "exp": time.time() + exp_in - 30}


def _get_token() -> str:
    with _token_lock:
        if _token_cache["access_token"] and time.time() < _token_cache["exp"]:
            return _token_cache["access_token"]
        fresh = _issue_token()
        _token_cache.update(fresh)
        return fresh["access_token"]


def kis_get(path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    url = f"{BASE}{path if path.startswith('/') else '/' + path}"
    for attempt in (1, 2):
        tok = _get_token()
        headers = {
            "Authorization": f"Bearer {tok}",
            "appkey": APP_KEY,
            "appsecret": APP_SECRET,
            "Content-Type": "application/json",
        }
        r = requests.get(url, headers=headers, params=params, timeout=8)
        if r.status_code == 401 and attempt == 1:
            with _token_lock:
                _token_cache["exp"] = 0
            continue
        if r.status_code != 200:
            raise KISAPIError(f"GET {path} http={r.status_code} body={r.text}")
        return r.json()
    raise KISAPIError("unreachable")

