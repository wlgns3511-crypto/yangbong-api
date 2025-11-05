# apps/api/market_kr.py

from fastapi import APIRouter, Query

from typing import Any, Dict, List, Optional

import logging, requests

from datetime import datetime



try:

    from .utils_yf import yf_hard_fallback

except Exception:

    yf_hard_fallback = None



router = APIRouter(prefix="/api/market", tags=["market"])

log = logging.getLogger("market.kr")



IDX = [

    {"name": "KOSPI",    "nav": "KOSPI",  "yf": "^KS11"},

    {"name": "KOSDAQ",   "nav": "KOSDAQ", "yf": "^KQ11"},

    {"name": "KOSPI200", "nav": "KPI200", "yf": "^KS200"},

]



NAV_URL = "https://api.finance.naver.com/siseIndex/siseIndexItem.nhn"



def _to_float(x: Any) -> float:

    if x is None: return 0.0

    if isinstance(x, (int, float)): return float(x)

    s = str(x).replace(",", "").strip()

    try: return float(s)

    except: return 0.0



def _naver_get(code: str) -> Dict[str, Any]:

    try:

        r = requests.get(NAV_URL, params={"code": code}, timeout=6, allow_redirects=True, headers={

            "User-Agent": "Mozilla/5.0"

        })

        if r.status_code != 200:

            return {"_ok": False, "_stage":"naver", "_http": r.status_code, "_raw": r.text[:200]}

        j = r.json() if r.text.strip().startswith("{") else {}

        price = _to_float(j.get("now") or j.get("close") or j.get("price"))

        change = _to_float(j.get("diff") or j.get("change"))

        pct = _to_float(j.get("rate") or j.get("changeRate"))

        ts = j.get("time") or j.get("date") or j.get("datetime") or None



        if isinstance(ts, str) and ts:

            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y.%m.%d %H:%M", "%Y%m%d%H%M%S", "%Y%m%d %H%M%S"):

                try:

                    ts = datetime.strptime(ts, fmt).isoformat()

                    break

                except:

                    pass



        if price <= 0:

            return {"_ok": False, "_stage":"naver", "_http": 200, "_raw":"parse_empty"}



        return {"_ok": True, "price": price, "change": change, "changeRate": pct, "time": ts}

    except Exception as e:

        return {"_ok": False, "_stage":"naver", "_err": f"exception:{e}"}



def _yf_bulk(symbols: List[str]) -> Dict[str, Dict[str, Any]]:

    if not yf_hard_fallback:

        return {}

    try:

        rows = yf_hard_fallback(symbols)

    except Exception:

        rows = []

    out: Dict[str, Dict[str, Any]] = {}

    for r in rows:

        sym = r.get("symbol")

        price = _to_float(r.get("regularMarketPrice"))

        if not price:

            continue

        chg = _to_float(r.get("regularMarketChange"))

        pct = _to_float(r.get("regularMarketChangePercent"))

        ts = r.get("regularMarketTime")

        if isinstance(ts, (int, float)) and ts > 0:

            try: ts = datetime.utcfromtimestamp(int(ts)).isoformat() + "Z"

            except: pass

        out[sym] = {"price": price, "change": chg, "changeRate": pct, "time": ts}

    return out



@router.get("/kr")

def get_market_kr(source: str = Query("auto", description="auto|naver|yf")) -> Dict[str, Any]:

    results: List[Dict[str, Any]] = []

    miss: List[Dict[str, Any]] = []



    yf_map = {}

    if source in ("auto", "yf"):

        yf_map = _yf_bulk([it["yf"] for it in IDX])



    for it in IDX:

        name, nav_code, yf_sym = it["name"], it["nav"], it["yf"]



        if source in ("auto", "naver"):

            nav = _naver_get(nav_code)

            if nav.get("_ok"):

                results.append({"name": name, **{k:v for k,v in nav.items() if not k.startswith("_")}})

                continue

            else:

                miss.append({"name": name, "stage":"naver", "detail": {k: nav.get(k) for k in ("_http","_raw","_err")}})

                if source == "naver":

                    continue



        y = yf_map.get(yf_sym)

        if y:

            results.append({"name": name, **y})

        else:

            miss.append({"name": name, "stage":"yf", "detail":"no_data"})



    if not results:

        return {"ok": False, "items": [], "error": "kr_no_data", "miss": miss}



    order = {it["name"]: i for i, it in enumerate(IDX)}

    results.sort(key=lambda x: order.get(x["name"], 999))

    return {"ok": True, "items": results, "error": None, "miss": miss}
