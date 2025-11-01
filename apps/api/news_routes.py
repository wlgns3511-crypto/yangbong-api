# -*- coding: utf-8 -*-
from fastapi import APIRouter, Query, HTTPException
from datetime import datetime, timezone
from typing import List, Dict, Any
import time
import re

from .news import get_news_kr, get_news_us, get_news_crypto  # 이전에 만든 실기사 수집 함수 재사용

router = APIRouter()

# 인메모리 스토어(데모용) — 배포/재시작 시 초기화됨
STORE: Dict[str, Dict[str, Any]] = {}       # id -> article
IDX_BY_TYPE: Dict[str, List[str]] = {"kr": [], "us": [], "crypto": []}
LAST_REFETCH: Dict[str, float] = {"kr": 0, "us": 0, "crypto": 0}
TTL = 60 * 5  # 5분마다 리프레시


def _now_ts() -> int:
    return int(time.time())


def _mk_id(url: str) -> str:
    # url 기반 간단 id
    return re.sub(r"[^a-zA-Z0-9]+", "", url)[-32:] or str(abs(hash(url)))


def _upsert(type_: str, items: List[Dict[str, Any]]):
    added = 0
    for it in items:
        aid = _mk_id(it["url"])
        if aid not in STORE:
            STORE[aid] = {
                "id": aid,
                "type": type_,
                "title": it["title"],
                "summary": it.get("summary") or "",
                "source": it.get("source") or "",
                "source_url": it["url"],
                "image": it.get("image"),
                "tags": it.get("tags") or [],
                "published_at": it.get("published_at") or "",
                "views": 0,
                "hot_score": 0.0,
                "created_ts": _now_ts(),
            }
            IDX_BY_TYPE[type_].append(aid)
            added += 1
    # 최신순 정렬
    IDX_BY_TYPE[type_].sort(key=lambda x: STORE[x].get("published_at",""), reverse=True)
    return added


def _refetch_if_needed(type_: str, limit: int):
    now = _now_ts()
    if now - LAST_REFETCH[type_] < TTL and len(IDX_BY_TYPE[type_]) >= limit:
        return
    if type_ == "kr":
        data = get_news_kr(limit)
    elif type_ == "us":
        data = get_news_us(limit)
    else:
        data = get_news_crypto(limit)
    _upsert(type_, data)
    LAST_REFETCH[type_] = now


def _slice_by_cursor(ids: List[str], cursor: str|None, limit: int):
    if not cursor:
        return ids[:limit], None
    try:
        idx = ids.index(cursor)
        nxt = ids[idx+1: idx+1+limit]
        next_cursor = nxt[-1] if nxt else None
        return nxt, next_cursor
    except ValueError:
        return ids[:limit], (ids[limit-1] if len(ids)>=limit else None)


@router.get("/news/list")
def news_list(type: str = Query("kr", pattern="^(kr|us|crypto)$"),
              limit: int = 20, cursor: str | None = None):
    _refetch_if_needed(type, max(limit, 50))
    ids = IDX_BY_TYPE[type]
    page, next_cursor = _slice_by_cursor(ids, cursor, limit)
    items = [STORE[i] for i in page]
    return {"status":"ok","type":type,"items":items,"next_cursor":next_cursor}


@router.get("/news/hot")
def news_hot(type: str = Query("kr", pattern="^(kr|us|crypto)$"), limit: int = 5):
    _refetch_if_needed(type, 50)
    ids = IDX_BY_TYPE[type]
    # views 기반 간단 랭킹 (최근 24h 가중치 없이 단순)
    ranked = sorted([STORE[i] for i in ids], key=lambda a: (a["views"], a["created_ts"]), reverse=True)
    return {"status":"ok","type":type,"items": ranked[:limit]}


@router.get("/news/{news_id}")
def news_detail(news_id: str):
    a = STORE.get(news_id)
    if not a: raise HTTPException(404, "not found")
    a["views"] += 1
    return {"status":"ok","item": a}


@router.get("/news/search")
def news_search(q: str, type: str = Query("kr|us|crypto")):
    # type 필터: "kr", "us", "crypto" 또는 파이프 여러개 "kr|crypto"
    types = set([t for t in type.split("|") if t in ("kr","us","crypto")])
    pool = []
    for t in types or ("kr","us","crypto"):
        pool += [STORE[i] for i in IDX_BY_TYPE[t]]
    qs = q.strip().lower()
    hit = [a for a in pool if qs in a["title"].lower() or qs in a.get("summary","").lower()
           or any(qs in (tg.lower()) for tg in a.get("tags", []))]
    # 최신순
    hit.sort(key=lambda a: a.get("published_at",""), reverse=True)
    return {"status":"ok","items": hit[:50]}

