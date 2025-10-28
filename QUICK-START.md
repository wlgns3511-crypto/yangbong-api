# 양봉클럽 프로젝트 빠른 시작

## Windows에서 바로 실행 가능한 올인원 명령어

### 옵션 1: WSL 사용 (권장)

WSL이 설치되어 있다면, 다음을 Cursor 터미널에 붙여넣으세요:

```bash
bash -c "$(cat << 'EOF'
# 요구사항 점검
command -v git >/dev/null 2>&1 || { echo "❌ git 미설치"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "❌ node 미설치"; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "❌ npm 미설치"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "❌ python3 미설치"; exit 1; }

echo "✅ Versions:"
git --version; node -v; npm -v; python3 --version

cd ..
mkdir -p yangbong-club && cd yangbong-club

# Git 초기화
git init -b main
git config user.name "yangbong"
git config user.email "you@example.com"

# .gitignore
cat > .gitignore << 'IGNORE'
node_modules/
.next/
out/
.venv/
__pycache__/
*.pyc
.env
.env.*
.DS_Store
*.log
.vscode/
.idea/
dist/
build/
IGNORE

# 백엔드 생성
mkdir -p apps/api && cd apps/api
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip -q
pip install flask flask-cors gunicorn requests feedparser yfinance pandas numpy ccxt -q
pip freeze > requirements.txt

cat > app.py << 'PY'
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/health')
def health():
    return jsonify(ok=True)

@app.route('/hello')
def hello():
    return jsonify(message='Hello from Flask API')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
PY

echo "# NEWS_API_KEY=..." > .env.example

deactivate
cd ../..

# 프론트엔드 생성
mkdir -p apps/web && cd apps/web

npx --yes create-next-app@latest web-app --typescript --tailwind --eslint --app --src-dir --no-import-alias --use-npm

cd web-app
echo "# NEXT_PUBLIC_API_BASE=http://localhost:8000" > .env.example
cd ../..

# README 생성
cat > README.md << 'READMEEOF'
# 양봉클럽 v2

## 로컬 실행

### 백엔드
\`\`\`
cd apps/api
source .venv/bin/activate  # 또는 .venv\\Scripts\\activate
python app.py
\`\`\`
실행: http://localhost:8000
헬스체크: http://localhost:8000/health

### 프론트엔드
\`\`\`
cd apps/web/web-app
npm run dev
\`\`\`
실행: http://localhost:3000

## 환경파일
- apps/web/web-app/.env
- apps/api/.env
READMEEOF

# 첫 커밋
git add .
git commit -m "chore: bootstrap monorepo (Next.js + Flask)"

echo "✅ 완료!"
echo "1. 백엔드: cd apps/api && source .venv/bin/activate && python app.py"
echo "2. 프론트: cd apps/web/web-app && npm run dev"
EOF
)"
```

### 옵션 2: PowerShell 단계별 명령어

WSL이 없다면 다음을 하나씩 실행하세요:

```powershell
# 프로젝트 생성
cd ..
mkdir yangbong-club
cd yangbong-club

# Git 초기화
git init -b main
git config user.name "yangbong"
git config user.email "you@example.com"

# .gitignore
@"
node_modules/
.next/
out/
.venv/
__pycache__/
*.pyc
.env
.env.*
.DS_Store
*.log
.vscode/
.idea/
dist/
build/
"@ | Out-File -FilePath .gitignore -Encoding utf8

# 백엔드 생성
mkdir apps\api
cd apps\api
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install flask flask-cors gunicorn requests feedparser yfinance pandas numpy ccxt
pip freeze > requirements.txt

@"
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/health')
def health():
    return jsonify(ok=True)

@app.route('/hello')
def hello():
    return jsonify(message='Hello from Flask API')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
"@ | Out-File -FilePath app.py -Encoding utf8

"# NEWS_API_KEY=..." | Out-File -FilePath .env.example -Encoding utf8

deactivate
cd ..\..

# 프론트엔드 생성
mkdir apps\web
cd apps\web
npx create-next-app@latest web-app --typescript --tailwind --eslint --app --src-dir --no-import-alias --use-npm
cd web-app
"# NEXT_PUBLIC_API_BASE=http://localhost:8000" | Out-File -FilePath .env.example -Encoding utf8
cd ..\..

# README
@"
# 양봉클럽 v2

## 로컬 실행

### 백엔드
cd apps\api
.\.venv\Scripts\Activate.ps1
python app.py

### 프론트엔드
cd apps\web\web-app
npm run dev
"@ | Out-File -FilePath README.md -Encoding utf8

# 첫 커밋
git add .
git commit -m "chore: bootstrap monorepo (Next.js + Flask)"

Write-Host "완료!" -ForegroundColor Green
```

## 실행 테스트

### 백엔드
```powershell
cd apps\api
.\.venv\Scripts\Activate.ps1  # Windows
# 또는 source .venv/bin/activate  # Mac/Linux
python app.py
```
브라우저에서 http://localhost:8000/health 확인

### 프론트엔드
```powershell
cd apps\web\web-app
npm run dev
```
브라우저에서 http://localhost:3000 확인

