# 양봉클럽 프로젝트 배포 및 운영 가이드

## 📋 전체 체크리스트

### 1. 로컬 도구 (Windows + PowerShell)

- [ ] Python 3.10+ (Windows 런처 py 포함)
- [ ] Node.js 20+ (npm 포함)
- [ ] Git
- [ ] VS Code / Cursor (확장: ESLint, Tailwind CSS, Prettier)
- [ ] PowerShell 실행 정책: RemoteSigned
  - 설정: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

### 2. 계정 & 접근

- [ ] GitHub 레포(Private 권장)
- [ ] Vercel (프론트 배포)
- [ ] Railway (백엔드/DB 배포) 또는 대체: Render/Fly.io
- [ ] 도메인: yangbong.club (DNS 수정 권한)
- [ ] 서브도메인 예약:
  - api.yangbong.club (백엔드)
  - staging.yangbong.club (스테이징)

### 3. Git & SSH

- [ ] SSH 키 생성/등록 (GitHub)
  ```bash
  ssh-keygen -t ed25519 -C "you@example.com"
  ```
  공개키를 GitHub → Settings → SSH and GPG keys에 등록

- [ ] 브랜치 전략: main(배포), dev(개발), feat/*
- [ ] 커밋 규칙(선택): Conventional Commits

### 4. 보안 & 환경변수 (.env)

절대 커밋 금지: .env, 시크릿
.env.example만 커밋

예상 변수 인벤토리:
```bash
# 공통
NODE_ENV=development

# 백엔드(API)
DATABASE_URL=postgresql://user:pass@host:5432/yangbong
REDIS_URL=redis://:pass@host:6379/0
ALLOWED_ORIGINS=https://yangbong.club,https://staging.yangbong.club

# 외부 데이터
NEWS_API_KEYS=...
RAPIDAPI_KEY=...
BYBIT_API_KEY=...
BYBIT_API_SECRET=...

# 프론트
NEXT_PUBLIC_API_BASE=https://api.yangbong.club
```

배포 환경(Vercel/Railway)의 Environment Variables에 동일하게 세팅

### 5. 데이터·크롤링 출처

- [ ] 사용 출처/약관 확인
- [ ] 가능하면 공식/합법 API 우선
- [ ] 레이트리밋/캐시 전략: Redis로 30~300초 캐시

### 6. 배포 경로 설계

- [ ] 프론트: Vercel에 GitHub 연결 → main 자동 배포
- [ ] 백엔드: Railway(Dockerfile or Build Command) → api.yangbong.club CNAME
- [ ] DNS:
  - yangbong.club → Vercel
  - api.yangbong.club → Railway Host에 CNAME
- [ ] 스테이징: staging.yangbong.club (선택)

### 7. 로그/모니터링/알림

- [ ] Railway Logs 확인 방법 숙지
- [ ] 프론트: Vercel Analytics(선택)
- [ ] 에러 추적: Sentry(선택)
- [ ] 가용성 체크: UptimeRobot(헬스엔드포인트 모니터)

### 8. 품질 규칙(자동화)

- [ ] Lint/Format: ESLint + Prettier
- [ ] pre-commit 훅: .env 커밋 방지 + 포맷 체크
- [ ] 빌드 확인: npm run build(프론트), python app.py --check(백엔드)

### 9. 롤백 전략

- [ ] Git 태그: 배포 전 SAFEPOINT-YYYYMMDD-HHMM 태그 찍기
- [ ] Vercel: 이전 배포로 "Promote" 가능
- [ ] Railway: 이전 이미지로 "Rollback" 버튼 확인

### 10. 커뮤니티 확장 대비

- [ ] DB: PostgreSQL
- [ ] 텍스트 검색: Meilisearch (또는 PG FTS로 시작)
- [ ] 업로드: Cloudflare R2 (선호) or S3
- [ ] 인증: Supabase Auth or 자체 JWT (나중 결정 가능)

---

## 🚀 배포 프로세스

### 1단계: 사전 점검

```powershell
.\preflight-check.ps1
```

모든 항목이 ✅ 확인되면 다음 단계로 진행

### 2단계: 프로젝트 생성

`QUICK-START.md` 참고하여 프로젝트 생성

### 3단계: GitHub 연결

```bash
git remote add origin git@github.com:username/yangbong-club.git
git push -u origin main
```

### 4단계: Vercel 배포 (프론트)

1. Vercel 로그인 (GitHub 연동)
2. New Project → yangbong-club 레포 선택
3. Root Directory: `apps/web/web-app`
4. Framework Preset: Next.js
5. Environment Variables 설정:
   - `NEXT_PUBLIC_API_BASE` = `https://api.yangbong.club`
6. Deploy

### 5단계: Railway 배포 (백엔드)

1. Railway 로그인 (GitHub 연동)
2. New Project → GitHub 레포 선택
3. Add Service → Deploy from GitHub repo
4. Root Directory: `apps/api`
5. Environment Variables 설정 (위 인벤토리 참고)
6. Custom Domain: api.yangbong.club
7. Deploy

### 6단계: DNS 설정

1. yangbong.club → Vercel 주소로 연결
2. api.yangbong.club → Railway 주소로 연결

### 7단계: 스테이징 (선택)

staging.yangbong.club으로 스테이징 환경 구축

---

## 🔧 운영 체크리스트

### 일일 확인
- [ ] Railway 로그 확인
- [ ] 헬스체크: https://api.yangbong.club/health
- [ ] Vercel Analytics 확인

### 주간 확인
- [ ] Redis 캐시 상태
- [ ] DB 크기 확인
- [ ] API 레이트리밋 준수 여부
- [ ] 에러 로그 검토

### 월간 확인
- [ ] 보안 업데이트 (npm audit, pip check)
- [ ] 도메인 갱신 일정
- [ ] 비용 모니터링 (Vercel/Railway)

---

## 🆘 트러블슈팅

### 로컬에서 실행 안됨
```powershell
# PowerShell 실행 정책 확인
Get-ExecutionPolicy

# 필요시
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### 포트 충돌
```powershell
# 사용 중인 포트 확인
Get-NetTCPConnection -LocalPort 3000,8000

# 프로세스 종료 (신중하게)
Stop-Process -Id <PID>
```

### 배포 실패
1. 로컬에서 빌드 테스트:
   ```powershell
   # 프론트
   cd apps/web/web-app
   npm run build
   
   # 백엔드
   cd apps/api
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   python app.py
   ```

2. 로그 확인:
   - Vercel: Deployments → Logs
   - Railway: Deployments → Logs

### 롤백
```bash
# Git 태그로 롤백
git tag SAFEPOINT-20240101-1200
git push origin SAFEPOINT-20240101-1200

# Vercel: Deployments → ⋯ → Promote to Production
# Railway: Deployments → ⋯ → Rollback
```

---

## 📞 지원

- Vercel Docs: https://vercel.com/docs
- Railway Docs: https://docs.railway.app
- Flask Docs: https://flask.palletsprojects.com
- Next.js Docs: https://nextjs.org/docs


