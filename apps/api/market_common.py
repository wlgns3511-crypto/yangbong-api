from __future__ import annotations

import json, os, time

from typing import Any, Dict, List, Tuple



CACHE_PATH = os.environ.get("MARKET_CACHE_PATH", "/tmp/market_cache.json")

TTL_SEC = int(os.environ.get("MARKET_TTL_SEC", "90"))



CANON = {

    "KOSPI": ["코스피","KS11"],

    "KOSDAQ": ["코스닥"],

    "KOSPI200": ["코스피200","KPI200"],

    "DJI": ["DOW","다우","DJI@DJI","^DJI"],

    "IXIC": ["NASDAQ","나스닥","NAS@IXIC","^IXIC"],

    "GSPC": ["SPX","S&P500","SNP","S&P","^GSPC"],

}



def _norm(s: str|None) -> str:

    return (s or "").strip().upper()



REV = {k:k for k in CANON.keys()}

for c, aliases in CANON.items():

    for a in aliases: REV[_norm(a)] = c



def canonicalize(s: str|None) -> str:

    k = _norm(s)

    return REV.get(k, k)



def _load() -> Dict[str, Any]:

    if not os.path.exists(CACHE_PATH):

        return {}

    try:

        with open(CACHE_PATH, "r", encoding="utf-8") as f:

            return json.load(f)

    except Exception:

        return {}



def _dump(obj: Dict[str, Any]) -> None:

    tmp = CACHE_PATH + ".tmp"

    try:

        with open(tmp, "w", encoding="utf-8") as f:

            json.dump(obj, f, ensure_ascii=False)

        os.replace(tmp, CACHE_PATH)

    except Exception:

        pass



def get_cache(seg: str) -> Tuple[List[Dict[str, Any]], bool]:

    store = _load()

    entry = store.get(seg.upper())

    if not entry: return [], False

    age = int(time.time()) - int(entry.get("ts", 0))

    return entry.get("items", []), age <= TTL_SEC



def set_cache(seg: str, items: List[Dict[str, Any]]) -> None:

    store = _load()

    store[seg.upper()] = {"ts": int(time.time()), "items": items}

    _dump(store)



def normalize_item(raw: Dict[str, Any]) -> Dict[str, Any]:

    sym = raw.get("symbol") or raw.get("code") or raw.get("name") or ""

    name = raw.get("name") or sym

    canon = canonicalize(sym) or canonicalize(name)

    return {

        "symbol": canon,

        "name": name,

        "price": float(raw.get("price") or raw.get("close") or raw.get("now") or raw.get("last") or 0),

        "change": float(raw.get("change") or raw.get("diff") or 0),

        "changeRate": float(raw.get("changeRate") or raw.get("rate") or 0),

        "time": raw.get("time") or raw.get("updatedAt") or raw.get("ts") or None,

    }

