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
            
            # 현재가 추출 (네이버 금융 해외 지수 페이지 실제 구조)
            price = None
            price_selectors = [
                'p.no_today em',           # 우선: p.no_today 안의 em 태그
                'p.no_today em.blind',     # blind 클래스가 em에 직접 있는 경우
                'p.no_today .blind',       # blind 클래스
                '#now_value',              # 대안: id로 직접 접근
                'p.no_today',              # p.no_today 전체에서 추출
                '.no_today em',            # 대안: 클래스만
                '.no_today .num',          # 대안: num 클래스
            ]
            
            for selector in price_selectors:
                price_elem = soup.select_one(selector)
                if price_elem:
                    # blind 클래스를 가진 요소 찾기 (우선순위)
                    blind_elem = price_elem.find(class_='blind')
                    if blind_elem:
                        price_text = blind_elem.get_text(strip=True)
                    else:
                        price_text = price_elem.get_text(strip=True)
                    
                    if price_text:
                        price = parse_value(price_text)
                        if price > 0:
                            logger.info(f"{symbol}: Found price using selector '{selector}': {price}")
                            break
            
            if not price or price <= 0:
                # 디버깅을 위해 HTML 일부 출력
                no_today_elem = soup.select_one('p.no_today')
                if no_today_elem:
                    html_snippet = str(no_today_elem)[:1000]
                    logger.warning(f"{symbol}: price not found. p.no_today HTML: {html_snippet}")
                else:
                    # 전체 HTML 구조 확인을 위해 주요 요소 찾기
                    contentarea = soup.select_one('#contentarea')
                    if contentarea:
                        logger.warning(f"{symbol}: p.no_today not found. contentarea exists: {bool(contentarea)}")
                    else:
                        logger.warning(f"{symbol}: p.no_today and contentarea not found. Response length: {len(response.text)}")
                        # 첫 1000자만 출력
                        logger.warning(f"{symbol}: HTML preview: {response.text[:1000]}")
                
                if attempt < max_attempts - 1:
                    time.sleep(1 + attempt)  # 점진적 대기
                    continue
                return None
            
            # 변동폭 추출 (네이버 금융 해외 지수 페이지 실제 구조)
            change = 0.0
            change_selectors = [
                'p.no_exday em',           # 우선: p.no_exday 안의 em 태그
                'p.no_exday em.blind',     # blind 클래스가 em에 직접 있는 경우
                'p.no_exday .blind',       # 대안: blind 클래스
                '#change_value',           # 대안: id로 직접 접근
                'p.no_exday',              # p.no_exday 전체에서 추출
                '.no_exday em',            # 대안: 클래스만
            ]
            
            change_elem = None
            change_text = ""
            for selector in change_selectors:
                change_elem = soup.select_one(selector)
                if change_elem:
                    # blind 클래스를 가진 요소 찾기 (우선순위)
                    blind_elem = change_elem.find(class_='blind')
                    if blind_elem:
                        change_text = blind_elem.get_text(strip=True)
                    else:
                        change_text = change_elem.get_text(strip=True)
                    
                    if change_text:
                        logger.info(f"{symbol}: Found change using selector '{selector}': {change_text}")
                        break
            
            if change_text:
                # "상승 100.50" 또는 "하락 100.50" 형태 파싱
                if '하락' in change_text or '▼' in change_text:
                    # 하락인 경우
                    change_val = parse_value(change_text)
                    change = -abs(change_val) if change_val > 0 else change_val
                elif '상승' in change_text or '▲' in change_text:
                    # 상승인 경우
                    change_val = parse_value(change_text)
                    change = abs(change_val)
                else:
                    # 숫자만 있는 경우 (부호 포함 가능)
                    # 정규식으로 숫자 추출
                    change_matches = re.findall(r'([+-]?\d{1,3}(?:,\d{3})*(?:\.\d+)?)', change_text)
                    if change_matches:
                        change_val = parse_value(change_matches[0])
                        change = change_val
                    else:
                        change_val = parse_value(change_text)
                        change = change_val
            
            # 등락률 추출 (네이버 금융 해외 지수 페이지 실제 구조)
            change_rate = 0.0
            rate_selectors = [
                'p.no_exday span',         # 우선: p.no_exday 안의 span 태그
                '#change_rate',            # 대안: id로 직접 접근
                'p.no_exday em span',      # 대안: em 안의 span
                '.no_exday span',          # 대안: 클래스만
            ]
            
            rate_elem = None
            rate_text = ""
            for selector in rate_selectors:
                rate_elem = soup.select_one(selector)
                if rate_elem:
                    rate_text = rate_elem.get_text(strip=True)
                    if rate_text:
                        logger.debug(f"{symbol}: Found rate using selector '{selector}': {rate_text}")
                        break
            
            # 등락률이 span에서 찾지 못했으면 no_exday 전체 텍스트에서 추출 시도
            if not rate_text:
                no_exday_elem = soup.select_one('p.no_exday')
                if no_exday_elem:
                    rate_text = no_exday_elem.get_text(strip=True)
                    logger.debug(f"{symbol}: Trying to extract rate from no_exday full text: {rate_text}")
            
            if rate_text:
                # 정규식으로 등락률 추출 (% 포함)
                rate_match = re.search(r'([+-]?\d+\.?\d*)%', rate_text)
                if rate_match:
                    change_rate = parse_value(rate_match.group(1))
                else:
                    # 등락률이 없으면 change 값으로 계산
                    if change != 0.0 and price > 0:
                        change_rate = (change / (price - change)) * 100
                        change_rate = round(change_rate, 2)
            else:
                # 등락률이 추출되지 않았고 change가 있으면 계산 시도
                if change != 0.0 and price > 0:
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
