# 배포 체크리스트

## 현재 상태
페이지가 기본 Next.js 템플릿만 표시되는 경우, 다음을 확인하세요.

## 1. 환경변수 설정 확인

### 로컬 개발 (.env.local)
`apps/web/.env.local` 파일 생성:
```env
NEXT_PUBLIC_API_BASE=https://yangbong.club
NEXT_PUBLIC_CRYPTO_LIST=BTC,ETH,XRP,SOL,BNB
```

### Vercel 배포 환경변수
1. Vercel 대시보드 → 프로젝트 선택
2. Settings → Environment Variables
3. 다음 변수들 추가:
   - `NEXT_PUBLIC_API_BASE` = `https://yangbong.club` (또는 실제 API 도메인)
   - `NEXT_PUBLIC_CRYPTO_LIST` = `BTC,ETH,XRP,SOL,BNB`
4. **Redeploy** 클릭

## 2. 코드 배포 확인

### Git 커밋 & 푸시
```bash
git add .
git commit -m "feat: 마켓 보드 UI 완성"
git push origin main
```

### Vercel 자동 배포 확인
- Vercel 대시보드 → Deployments 탭에서 최신 배포 상태 확인
- 빌드 로그에서 오류 확인

## 3. 빌드 테스트

### 로컬 빌드 테스트
```bash
cd apps/web
npm run build
npm run start
```

빌드 성공 후 `http://localhost:3000` 접속하여 확인

## 4. API 연결 확인

### API 서버 상태 확인
```bash
curl https://yangbong.club/api/market/world
curl https://yangbong.club/api/market/kr
curl "https://yangbong.club/api/crypto/tickers?list=BTC,ETH"
```

모두 정상 응답해야 함 (200 OK)

## 5. 브라우저 개발자 도구 확인

### 네트워크 탭
- `/api/market/world` 요청이 있는지 확인
- CORS 오류가 있는지 확인
- 응답 상태 코드 확인

### 콘솔 탭
- JavaScript 오류 확인
- 환경변수 값 확인 (공개된 것만)

## 6. 현재 코드 상태

✅ `page.tsx` - Server Component로 구현 완료
✅ `lib/api.ts` - 재시도 로직 포함
✅ `error.tsx` - 에러 핸들링 추가
✅ `loading.tsx` - 로딩 UI 추가

## 문제 해결 단계

1. 환경변수 설정 확인 (가장 중요!)
2. Git 푸시 후 Vercel 재배포
3. 브라우저 캐시 클리어 (Ctrl+Shift+R 또는 Cmd+Shift+R)
4. API 서버가 정상 동작하는지 확인

