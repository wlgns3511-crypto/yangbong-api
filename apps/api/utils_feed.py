# apps/api/utils_feed.py

import requests, time

from typing import Optional, Tuple

from urllib.parse import urljoin



DEFAULT_HEADERS = {"User-Agent": "Mozilla/5.0"}



def fetch_url(url: str, max_hops: int = 3, timeout: int = 8) -> Tuple[int, str, str]:

    """

    리다이렉트 따라가며 최종 컨텐츠를 반환.

    return: (status_code, final_url, text[:])

    """

    cur = url

    for _ in range(max_hops+1):

        r = requests.get(cur, headers=DEFAULT_HEADERS, timeout=timeout, allow_redirects=False)

        sc = r.status_code

        if sc in (301, 302, 303, 307, 308):

            loc = r.headers.get("Location") or ""

            if not loc:

                return sc, cur, r.text

            # 상대경로 보정

            cur = urljoin(cur, loc)

            continue

        return sc, cur, r.text

    return 599, cur, ""

