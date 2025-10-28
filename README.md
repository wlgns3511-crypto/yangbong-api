# 양봉클럽 v2 (단일 스택: FastAPI + Next.js)

## 1) 백엔드 (FastAPI)
```bash
cd apps/api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn apps.api.app:app --reload --host 0.0.0.0 --port 8000
```

실행: http://localhost:8000
헬스체크: http://localhost:8000/health
핑: http://localhost:8000/ping

## 2) 프론트엔드 (Next.js)
```bash
cd apps/web
npm install
npm run dev
```

접속: http://localhost:3000

## 3) 주의사항 (Windows PowerShell)

일시 환경변수: `$env:NEXT_PUBLIC_API_BASE="http://localhost:8000"`

영구 등록: `setx NEXT_PUBLIC_API_BASE "http://localhost:8000"`
(영구등록 후 새 터미널에서 반영)

## 프로젝트 구조
```
yangbong-api/
├─ apps/
│  ├─ api/                ← FastAPI
│  └─ web/                ← Next.js
├─ _archive/              ← Flask 프로젝트 보관
└─ ...
```

