# apps/api/market_world.py
# 해외 지수 크롤링 (개선 버전)

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
    'DJI': {
        'name': '다우존스',
        'url': 'https://finance.naver.com/world/sise.naver?symbol=DJI@DJI'
    },
    'IXIC': {
        'name': '나스닥',
        'url': 'https://finance.naver.com/world/sise.naver?symbol=NAS@IXIC'
    },
    'GSPC': {
        'name': 'S&P500',
        'url': 'https://finance.naver.com/world/sise.naver?symbol=SPI@SPX'
    }
}


def parse_value(text: str) -> float:
    """숫자 파싱"""
    if not text:
        return 0.0
    return float(text.strip().replace(',', '').replace('+', '').replace('%', ''))


def fetch_world_index(symbol: str, config: dict) -> Optional[Dict]:
    """해외 지수 크롤링"""
    for attempt in range(2):
        try:
            logger.info(f"Fetching {symbol} (attempt {attempt + 1}/2)")
            
            response = requests.get(config['url'], headers=HEADERS, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 현재가 (해외 지수는 다른 셀렉터 사용)
            price_elem = soup.select_one('.spot .num')
            if not price_elem:
                logger.warning(f"{symbol}: price element not found")
                continue
            
            price = parse_value(price_elem.text)
            
            # 등락 정보
            change_elem = soup.select_one('.spot .change')
            change = 0.0
            change_rate = 0.0
            
            if change_elem:
                # "▲ 100.50 +0.25%" 형태
                text = change_elem.text.strip()
                is_down = '▼' in text or 'minus' in change_elem.get('class', [])
                
                # 등락액
                parts = text.split()
                if len(parts) >= 2:
                    change = parse_value(parts[1])
                    if is_down:
                        change = -abs(change)
                
                # 등락률
                for part in parts:
                    if '%' in part:
                        change_rate = parse_value(part)
                        if is_down:
                            change_rate = -abs(change_rate)
                        break
            
            result = {
                'symbol': symbol,
                'name': config['name'],
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


def fetch_from_naver_world() -> List[Dict[str, Any]]:
    """해외 지수 전체 조회 (캐시 적용)"""
    now = time.time()
    
    # 캐시 확인
    if 'us_data' in _cache and (now - _cache.get('us_timestamp', 0)) < _cache_ttl:
        logger.info("Returning cached US data")
        return _cache['us_data']
    
    # 크롤링
    items = []
    for symbol, config in INDICES.items():
        data = fetch_world_index(symbol, config)
        if data:
            # normalize_item을 사용하여 표준 포맷으로 변환
            normalized = normalize_item(data)
            if normalized.get('price') is not None:
                items.append(normalized)
        time.sleep(0.3)  # 네이버 서버 부담 감소
    
    # 캐시 저장
    _cache['us_data'] = items
    _cache['us_timestamp'] = now
    
    return items
