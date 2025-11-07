# apps/api/naver_indices.py

from typing import Dict, Any, List, Optional

import requests

from datetime import datetime



NAV_URL = "https://api.finance.naver.com/siseIndex/siseIndexItem.nhn"

HEADERS = {"User-Agent": "Mozilla/5.0"}



def _to_float(x: Any) -> float:

    if x is None: return 0.0

    if isinstance(x, (int, float)): return float(x)

    s = str(x).replace(",", "").strip()

    try: return float(s)

    except: return 0.0



def _normalize_time(ts: Optional[str]) -> Optional[str]:

    if not ts: return None

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y.%m.%d %H:%M", "%Y%m%d%H%M%S", "%Y%m%d %H%M%S"):

        try:

            return datetime.strptime(ts, fmt).isoformat()

        except:

            pass

    return ts



def fetch_kr_indices(codes: List[str]) -> Dict[str, Dict[str, Any]]:

    """

    codes 예: ["KOSPI","KOSDAQ","KPI200"]

    반환: { "KOSPI": {price, change, changeRate, time}, ... }

    """

    import logging

    log = logging.getLogger("naver_indices")

    out: Dict[str, Dict[str, Any]] = {}

    for code in codes:

        try:

            r = requests.get(NAV_URL, params={"code": code}, headers=HEADERS, timeout=6)

            if r.status_code != 200:

                log.warning("naver_indices: %s HTTP %s", code, r.status_code)

                out[code] = {}

                continue

            text = r.text.strip()

            if not text.startswith("{"):

                log.warning("naver_indices: %s non-JSON response (first 100 chars: %s)", code, text[:100])

                out[code] = {}

                continue

            j = r.json()

            price = _to_float(j.get("now") or j.get("close") or j.get("price"))

            change = _to_float(j.get("diff") or j.get("change"))

            pct = _to_float(j.get("rate") or j.get("changeRate"))

            ts = _normalize_time(j.get("time") or j.get("date") or j.get("datetime"))

            if price > 0:

                out[code] = {"price": price, "change": change, "changeRate": pct, "time": ts}

                log.debug("naver_indices: %s OK price=%.2f change=%.2f rate=%.2f%%", code, price, change, pct)

            else:

                log.warning("naver_indices: %s invalid price (raw JSON: %s)", code, j)

                out[code] = {}

        except Exception as e:

            log.error("naver_indices: %s exception: %s", code, e, exc_info=True)

            out[code] = {}

    return out
