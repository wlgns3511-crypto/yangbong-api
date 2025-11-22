# 양봉클럽 백엔드 API

양봉클럽 백엔드 FastAPI 프로젝트입니다.

## 기술 스택

- Python 3.11+
- FastAPI 0.104.1
- Uvicorn 0.24.0
- Pydantic 2.5.0
- Supabase 2.0.0
- OpenAI 1.3.0

## 프로젝트 구조

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 애플리케이션 진입점
│   ├── api/                    # API 라우터
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── market.py       # 마켓 API
│   │       ├── stocks.py       # 주식 API
│   │       ├── ai.py           # AI API
│   │       └── news.py         # 뉴스 API
│   ├── core/                   # 핵심 설정
│   │   ├── __init__.py
│   │   └── config.py           # 환경변수 설정
│   ├── models/                 # 데이터 모델
│   │   ├── __init__.py
│   │   ├── schemas.py          # 공통 스키마 (APIResponse)
│   │   ├── market.py           # 마켓 모델
│   │   ├── stocks.py           # 주식 모델
│   │   ├── news.py             # 뉴스 모델
│   │   └── ai.py               # AI 모델
│   └── services/               # 비즈니스 로직
│       ├── __init__.py
│       ├── supabase_client.py  # Supabase 클라이언트
│       ├── market_service.py   # 마켓 서비스
│       ├── stocks_service.py   # 주식 서비스
│       ├── ai_service.py       # AI 서비스
│       └── news_service.py     # 뉴스 서비스
├── requirements.txt            # Python 의존성
├── .env.example               # 환경변수 예시
├── .gitignore                 # Git 무시 파일
└── README.md                  # 프로젝트 설명서
```

## 설치 및 실행

### 1. 가상환경 생성 및 활성화

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 환경변수 설정

`.env.example` 파일을 참고하여 `.env` 파일을 생성하고 필요한 환경변수를 설정합니다.

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집하여 실제 값 입력
```

### 4. 서버 실행

```bash
# 개발 모드 (자동 리로드)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 또는 Python으로 직접 실행
python app/main.py
```

서버가 실행되면 다음 URL에서 API 문서를 확인할 수 있습니다:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 엔드포인트 (Phase 1 - P0)

### 마켓 API

- `GET /api/v1/market/summary?seg={KR|US|CRYPTO|COMMO}` - 마켓 요약 조회
- `GET /api/v1/market/sectors?seg={KR|US|CRYPTO|COMMO}` - 마켓 섹터 조회
- `GET /api/v1/market/flow?seg={KR|US|CRYPTO|COMMO}` - 마켓 자금 흐름 조회

### 주식 API

- `GET /api/v1/stocks/popular?market={KR|US}&limit=6` - 인기 주식 조회
- `GET /api/v1/stocks/surging?limit=6&mix=true` - 급등 주식 조회

### AI API

- `GET /api/v1/ai/market-briefing` - 마켓 브리핑 생성

### 뉴스 API

- `GET /api/v1/news/list?category=전체&page=1&limit=20` - 뉴스 리스트 조회
- `GET /api/v1/news/breaking?limit=5` - 속보 뉴스 조회
- `GET /api/v1/news/{id}` - 뉴스 상세 조회

## 응답 포맷

모든 API는 공통 응답 포맷을 사용합니다:

### 성공 응답

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "meta": {
    "timestamp": "2024-01-01T00:00:00Z",
    "version": "v1"
  }
}
```

### 실패 응답

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "ERROR_CODE",
    "message": "에러 메시지",
    "details": {}
  },
  "meta": {
    "timestamp": "2024-01-01T00:00:00Z",
    "version": "v1"
  }
}
```

## 개발 노트

현재 모든 서비스는 Mock 데이터로 구현되어 있습니다. 실제 외부 API 연동은 각 서비스 파일의 `TODO` 주석이 있는 부분에서 구현하면 됩니다.

- `app/services/market_service.py` - 마켓 데이터 API 연동
- `app/services/stocks_service.py` - 주식 데이터 API 연동
- `app/services/ai_service.py` - OpenAI API 연동
- `app/services/news_service.py` - Supabase 또는 뉴스 API 연동

## 라이선스

이 프로젝트는 양봉클럽 전용입니다.

