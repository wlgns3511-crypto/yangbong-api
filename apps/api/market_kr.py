# apps/api/market_kr.py
# 국내 지수 크롤링 (개선 버전)

from __future__ import annotations

import time
import requests
from bs4 import BeautifulSoup
from typing import Any, Dict, List, Optional
import logging
import re

from .market_common import normalize_item

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# TTL 캐시 (15초)
_cache = {}
_cache_ttl = 15

# 스크래핑 방지 우회를 위한 완전한 헤더 설정
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0',
    'Referer': 'https://www.naver.com/',
}

INDICES = {
    'KOSPI': {
        'url': 'https://finance.naver.com/sise/sise_index.naver?code=KOSPI',
        'name': '코스피',
    },
    'KOSDAQ': {
        'url': 'https://finance.naver.com/sise/sise_index.naver?code=KOSDAQ',
        'name': '코스닥',
    },
    'KOSPI200': {
        'url': 'https://finance.naver.com/sise/sise_index.naver?code=KPI200',
        'name': '코스피200',
    },
}

# 세션 유지 (쿠키 및 연결 재사용)
_session = requests.Session()
_session.headers.update(HEADERS)


def parse_value(text: str) -> float:
    """숫자 파싱 (쉼표, 부호, % 제거)"""
    if not text:
        return 0.0
    # 공백, 쉼표, +, % 제거
    cleaned = text.strip().replace(',', '').replace('+', '').replace('%', '').strip()
    try:
        return float(cleaned)
    except ValueError:
        logger.warning(f"Failed to parse value: {text}")
        return 0.0


def fetch_index(symbol: str, url: str, name: str) -> Optional[Dict]:
    """개별 지수 크롤링 (재시도 포함, 스크래핑 방지 우회)"""
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            logger.info(f"Fetching {symbol} from {url} (attempt {attempt + 1}/{max_attempts})")
            
            # 세션을 사용하여 쿠키 유지 및 연결 재사용
            response = _session.get(url, timeout=10, allow_redirects=True)
            response.raise_for_status()
            
            # 응답 인코딩 확인
            if response.encoding is None or response.encoding == 'ISO-8859-1':
                response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 현재가 추출 (여러 선택자 시도)
            price = None
            price_selectors = [
                '#now_value',
                '.no_today .blind',
                '#contentarea .no_today .blind',
                '.no_today em',
            ]
            
            for selector in price_selectors:
                price_elem = soup.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    if price_text:
                        price = parse_value(price_text)
                        if price > 0:
                            break
            
            if not price or price <= 0:
                logger.warning(f"{symbol}: price not found or invalid. HTML preview: {response.text[:500]}")
                if attempt < max_attempts - 1:
                    time.sleep(1 + attempt)  # 점진적 대기
                    continue
                return None
            
            # 등락액 추출 (여러 방법 시도)
            change = 0.0
            change_selectors = [
                '#change_value_and_rate .blind',
                '.no_exday .blind',
                '.no_exday em',
                '#change',
            ]
            
            change_text = ""
            for selector in change_selectors:
                change_elem = soup.select_one(selector)
                if change_elem:
                    change_text = change_elem.get_text(strip=True)
                    if change_text:
                        break
            
            if change_text:
                # "상승 10 포인트" 또는 "하락 10 포인트" 형태
                if '하락' in change_text:
                    parts = change_text.split()
                    if len(parts) > 1:
                        change = -abs(parse_value(parts[1]))
                elif '상승' in change_text:
                    parts = change_text.split()
                    if len(parts) > 1:
                        change = abs(parse_value(parts[1]))
                else:
                    # 숫자만 있는 경우
                    change_val = parse_value(change_text)
                    if change_val != 0:
                        change = change_val
            
            # 등락률 추출
            change_rate = 0.0
            rate_selectors = [
                '#change_value_and_rate',
                '.no_exday',
                '#change_rate',
            ]
            
            for selector in rate_selectors:
                rate_elem = soup.select_one(selector)
                if rate_elem:
                    rate_text = rate_elem.get_text(strip=True)
                    # 정규식으로 등락률 추출 (% 포함)
                    rate_match = re.search(r'([+-]?\d+\.?\d*)%', rate_text)
                    if rate_match:
                        change_rate = parse_value(rate_match.group(1))
                        break
            
            # 등락률이 추출되지 않았고 change가 있으면 계산 시도
            if change_rate == 0.0 and change != 0.0 and price > 0:
                change_rate = (change / (price - change)) * 100
                change_rate = round(change_rate, 2)
            
            result = {
                'symbol': symbol,
                'name': name,
                'price': price,
                'change': change,
                'changeRate': change_rate,
                'time': int(time.time())
            }
            
            logger.info(f"{symbol} ({name}): 가격={price}, 변동={change}, 등락률={change_rate}%")
            return result
            
        except requests.Timeout:
            logger.error(f"{symbol}: timeout (attempt {attempt + 1}/{max_attempts})")
            if attempt < max_attempts - 1:
                time.sleep(1 + attempt)
        except requests.RequestException as e:
            logger.error(f"{symbol}: request error - {str(e)} (attempt {attempt + 1}/{max_attempts})")
            if attempt < max_attempts - 1:
                time.sleep(1 + attempt)
        except Exception as e:
            logger.error(f"{symbol}: unexpected error - {str(e)} (attempt {attempt + 1}/{max_attempts})")
            if attempt < max_attempts - 1:
                time.sleep(1 + attempt)
    
    logger.error(f"{symbol}: failed to fetch after {max_attempts} attempts")
    return None


def fetch_from_naver() -> List[Dict[str, Any]]:
    """국내 지수 전체 조회 (캐시 적용, 스크래핑 방지 우회)"""
    now = time.time()
    
    # 캐시 확인
    if 'kr_data' in _cache and (now - _cache.get('kr_timestamp', 0)) < _cache_ttl:
        logger.info("Returning cached KR data")
        return _cache['kr_data']
    
    # 크롤링 (KOSPI, KOSDAQ, KOSPI200 순서)
    items = []
    for symbol, info in INDICES.items():
        url = info['url']
        name = info['name']
        
        logger.info(f"Fetching {symbol} ({name}) from Naver Finance...")
        data = fetch_index(symbol, url, name)
        
        if data:
            # normalize_item을 사용하여 표준 포맷으로 변환
            normalized = normalize_item(data)
            if normalized.get('price') is not None:
                items.append(normalized)
                logger.info(f"Successfully fetched {symbol}: {normalized.get('price')}")
            else:
                logger.warning(f"{symbol}: invalid price after normalization")
        else:
            logger.warning(f"{symbol}: failed to fetch data")
        
        # 네이버 서버 부담 감소 및 스크래핑 방지 우회를 위한 대기
        if symbol != list(INDICES.keys())[-1]:  # 마지막 항목이 아니면 대기
            time.sleep(0.5)
    
    # 결과 확인
    if not items:
        logger.error("Failed to fetch any KR market data")
        # 캐시된 데이터가 있으면 반환
        if 'kr_data' in _cache:
            logger.info("Returning stale cached data")
            return _cache['kr_data']
    else:
        logger.info(f"Successfully fetched {len(items)} items: {[item.get('symbol') for item in items]}")
        # 캐시 저장
        _cache['kr_data'] = items
        _cache['kr_timestamp'] = now
    
    return items
