# apps/api/market_kr.py
# 국내 지수 크롤링 (개선 버전)

from __future__ import annotations

import time
import requests
from bs4 import BeautifulSoup
from typing import Any, Dict, List, Optional
import logging

from .market_common import normalize_item

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# TTL 캐시 (15초)
_cache = {}
_cache_ttl = 15

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://finance.naver.com/',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
}

INDICES = {
    'KOSPI': 'https://finance.naver.com/sise/sise_index.naver?code=KOSPI',
    'KOSDAQ': 'https://finance.naver.com/sise/sise_index.naver?code=KOSDAQ',
    'KOSPI200': 'https://finance.naver.com/sise/sise_index.naver?code=KPI200',
}


def parse_value(text: str) -> float:
    """숫자 파싱 (쉼표 제거)"""
    if not text:
        return 0.0
    return float(text.strip().replace(',', '').replace('+', '').replace('%', ''))


def fetch_index(symbol: str, url: str) -> Optional[Dict]:
    """개별 지수 크롤링 (재시도 포함)"""
    for attempt in range(2):
        try:
            logger.info(f"Fetching {symbol} (attempt {attempt + 1}/2)")
            
            response = requests.get(url, headers=HEADERS, timeout=8)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 현재가
            price_elem = soup.select_one('#now_value')
            if not price_elem:
                logger.warning(f"{symbol}: price element not found")
                continue
                
            price = parse_value(price_elem.text)
            
            # 등락액
            change_elem = soup.select_one('#change_value_and_rate .blind')
            change = 0.0
            if change_elem:
                change_text = change_elem.text.strip()
                # "상승 10 포인트" 또는 "하락 10 포인트" 형태
                if '하락' in change_text:
                    change = -parse_value(change_text.split()[1])
                elif '상승' in change_text:
                    change = parse_value(change_text.split()[1])
            
            # 등락률
            rate_elem = soup.select_one('#change_value_and_rate')
            change_rate = 0.0
            if rate_elem:
                rate_text = rate_elem.text.strip()
                # "10 +0.50%" 형태에서 % 부분만 추출
                parts = rate_text.split()
                for part in parts:
                    if '%' in part:
                        change_rate = parse_value(part)
                        if '하락' in rate_text or change < 0:
                            change_rate = -abs(change_rate)
                        break
            
            result = {
                'symbol': symbol,
                'name': symbol,
                'price': price,
                'change': change,
                'changeRate': change_rate,
                'time': int(time.time())
            }
            
            logger.info(f"{symbol}: {result}")
            return result
            
        except requests.Timeout:
            logger.error(f"{symbol}: timeout (attempt {attempt + 1}/2)")
            if attempt == 0:
                time.sleep(1)
        except Exception as e:
            logger.error(f"{symbol}: {str(e)} (attempt {attempt + 1}/2)")
            if attempt == 0:
                time.sleep(1)
    
    return None


def fetch_from_naver() -> List[Dict[str, Any]]:
    """국내 지수 전체 조회 (캐시 적용)"""
    now = time.time()
    
    # 캐시 확인
    if 'kr_data' in _cache and (now - _cache.get('kr_timestamp', 0)) < _cache_ttl:
        logger.info("Returning cached KR data")
        return _cache['kr_data']
    
    # 크롤링
    items = []
    for symbol, url in INDICES.items():
        data = fetch_index(symbol, url)
        if data:
            # normalize_item을 사용하여 표준 포맷으로 변환
            normalized = normalize_item(data)
            if normalized.get('price') is not None:
                items.append(normalized)
        time.sleep(0.3)  # 네이버 서버 부담 감소
    
    # 캐시 저장
    _cache['kr_data'] = items
    _cache['kr_timestamp'] = now
    
    return items
