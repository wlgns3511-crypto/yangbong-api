# apps/api/market_world.py
# 해외 지수 크롤링 (개선 버전, 스크래핑 방지 우회)

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
    'DJI': {
        'name': '다우 산업',
        'symbol_code': 'DJI@DJI',
        'url': 'https://finance.naver.com/world/sise.naver?symbol=DJI@DJI'
    },
    'IXIC': {
        'name': '나스닥 종합',
        'symbol_code': 'NAS@IXIC',
        'url': 'https://finance.naver.com/world/sise.naver?symbol=NAS@IXIC'
    },
    'GSPC': {
        'name': 'S&P 500',
        'symbol_code': 'SPI@SPX',
        'url': 'https://finance.naver.com/world/sise.naver?symbol=SPI@SPX'
    }
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


def fetch_world_index(symbol: str, config: dict) -> Optional[Dict]:
    """해외 지수 크롤링 (재시도 포함, 스크래핑 방지 우회)"""
    max_attempts = 3
    url = config['url']
    name = config['name']
    
    for attempt in range(max_attempts):
        try:
            logger.info(f"Fetching {symbol} ({name}) from {url} (attempt {attempt + 1}/{max_attempts})")
            
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
                '.spot .num',
                '.spot .num_s',
                '#contentarea .spot .num',
                '.today .num',
                '.today .num_s',
                '#now_value',
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
            
            # 등락 정보 추출 (여러 방법 시도)
            change = 0.0
            change_rate = 0.0
            change_selectors = [
                '.spot .change',
                '.spot .change .num',
                '.spot .change .num_s',
                '#contentarea .spot .change',
                '.today .change',
            ]
            
            change_text = ""
            change_elem = None
            for selector in change_selectors:
                change_elem = soup.select_one(selector)
                if change_elem:
                    change_text = change_elem.get_text(strip=True)
                    if change_text:
                        break
            
            if change_text:
                # "▲ 100.50 +0.25%" 또는 "▼ -100.50 -0.25%" 형태
                is_down = '▼' in change_text or 'down' in change_text.lower()
                is_up = '▲' in change_text or 'up' in change_text.lower()
                
                # 등락액 추출
                # 정규식으로 숫자 패턴 찾기 (부호 포함)
                change_matches = re.findall(r'([+-]?\d{1,3}(?:,\d{3})*(?:\.\d+)?)', change_text)
                if change_matches:
                    change_val = parse_value(change_matches[0])
                    if change_val != 0:
                        # 부호 확인
                        if is_down:
                            change = -abs(change_val)
                        elif is_up:
                            change = abs(change_val)
                        else:
                            # 부호가 없으면 숫자 앞의 +/- 확인
                            if change_val < 0:
                                change = change_val
                            else:
                                change = change_val
                
                # 등락률 추출 (정규식)
                rate_match = re.search(r'([+-]?\d+\.?\d*)%', change_text)
                if rate_match:
                    change_rate = parse_value(rate_match.group(1))
                else:
                    # 등락률이 없으면 계산 시도
                    if change != 0.0 and price > 0:
                        change_rate = (change / (price - change)) * 100
                        change_rate = round(change_rate, 2)
            
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


def fetch_from_naver_world() -> List[Dict[str, Any]]:
    """해외 지수 전체 조회 (캐시 적용, 스크래핑 방지 우회)"""
    now = time.time()
    
    # 캐시 확인
    if 'us_data' in _cache and (now - _cache.get('us_timestamp', 0)) < _cache_ttl:
        logger.info("Returning cached US data")
        return _cache['us_data']
    
    # 크롤링 (DJI, IXIC, GSPC 순서)
    items = []
    for symbol, config in INDICES.items():
        name = config['name']
        
        logger.info(f"Fetching {symbol} ({name}) from Naver Finance...")
        data = fetch_world_index(symbol, config)
        
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
        logger.error("Failed to fetch any US market data")
        # 캐시된 데이터가 있으면 반환
        if 'us_data' in _cache:
            logger.info("Returning stale cached data")
            return _cache['us_data']
    else:
        logger.info(f"Successfully fetched {len(items)} items: {[item.get('symbol') for item in items]}")
        # 캐시 저장
        _cache['us_data'] = items
        _cache['us_timestamp'] = now
    
    return items
