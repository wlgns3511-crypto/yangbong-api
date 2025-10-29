// app/page.tsx
import { getWorld, getKorea, getCrypto, Ticker } from "@/lib/api";

function Chip({ t }: { t: Ticker }) {
  const up = t.change > 0;
  const color = up ? "text-red-600" : t.change < 0 ? "text-blue-600" : "text-gray-600";
  const sign = up ? "+" : "";
  return (
    <div className="rounded-xl border p-4 flex flex-col gap-1">
      <div className="text-sm text-gray-500">{t.name}</div>
      <div className={`text-lg font-semibold ${color}`}>
        {t.price.toLocaleString()} <span className="text-xs">({sign}{t.change.toFixed(1)}, {sign}{t.change_pct.toFixed(2)}%)</span>
      </div>
    </div>
  );
}

export default async function Page() {
  const API_BASE = process.env.NEXT_PUBLIC_API_BASE || '';
  const CRYPTO_LIST = process.env.NEXT_PUBLIC_CRYPTO_LIST || 'BTC,ETH,XRP,SOL,BNB';
  
  // 환경변수 확인
  if (!API_BASE) {
    return (
      <main className="max-w-6xl mx-auto p-6">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <h2 className="text-lg font-semibold text-yellow-800 mb-2">환경변수 설정 필요</h2>
          <p className="text-yellow-700">NEXT_PUBLIC_API_BASE 환경변수가 설정되지 않았습니다.</p>
          <pre className="mt-2 text-sm bg-yellow-100 p-2 rounded">{`
.env.local 또는 Vercel 환경변수에 추가:
NEXT_PUBLIC_API_BASE=https://yangbong.club
NEXT_PUBLIC_CRYPTO_LIST=BTC,ETH,XRP,SOL,BNB
          `}</pre>
        </div>
      </main>
    );
  }

  try {
    // 3개 API 병렬 호출 + 3회 재시도 로직은 lib/api에 있음
    const [world, kr, crypto] = await Promise.all([
      getWorld(), 
      getKorea(), 
      getCrypto(CRYPTO_LIST),
    ]);

    // 세계 9칸, 국내 3칸, 코인 4~6칸
    const world9 = world.items?.slice(0, 9) || [];
    const kr3 = kr.items?.slice(0, 3) || [];
    const cxs = crypto.items?.slice(0, 6) || [];

    return (
      <main className="max-w-6xl mx-auto p-6 space-y-8">
        <header className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">양봉클럽 · 마켓 보드</h1>
          <div className="text-sm text-gray-500">API: {API_BASE}</div>
        </header>

        {/* 국내 지수 (3칸) */}
        <section>
          <h2 className="mb-3 font-semibold">국내 지수</h2>
          {kr3.length > 0 ? (
            <div className="grid gap-3 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
              {kr3.map((t) => <Chip key={t.code} t={t} />)}
            </div>
          ) : (
            <div className="text-gray-500">데이터를 불러올 수 없습니다.</div>
          )}
        </section>

        {/* 세계 지수 (9칸) */}
        <section>
          <h2 className="mb-3 font-semibold">세계 지수</h2>
          {world9.length > 0 ? (
            <div className="grid gap-3 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
              {world9.map((t) => <Chip key={t.code} t={t} />)}
            </div>
          ) : (
            <div className="text-gray-500">데이터를 불러올 수 없습니다.</div>
          )}
        </section>

        {/* 코인 (4~6칸) */}
        <section>
          <h2 className="mb-3 font-semibold">코인</h2>
          {cxs.length > 0 ? (
            <div className="grid gap-3 grid-cols-2 sm:grid-cols-3 lg:grid-cols-6">
              {cxs.map((t) => <Chip key={t.code} t={t} />)}
            </div>
          ) : (
            <div className="text-gray-500">데이터를 불러올 수 없습니다.</div>
          )}
        </section>
      </main>
    );
  } catch (error: any) {
    return (
      <main className="max-w-6xl mx-auto p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h2 className="text-lg font-semibold text-red-800 mb-2">데이터 로드 실패</h2>
          <p className="text-red-700 mb-2">{error?.message || '알 수 없는 오류가 발생했습니다.'}</p>
          <details className="mt-2">
            <summary className="cursor-pointer text-sm text-red-600">상세 정보</summary>
            <pre className="mt-2 text-xs bg-red-100 p-2 rounded overflow-auto">
              {error?.stack || JSON.stringify(error, null, 2)}
            </pre>
          </details>
          <div className="mt-4 text-sm text-gray-600">
            <p>확인 사항:</p>
            <ul className="list-disc list-inside mt-2">
              <li>API 서버가 실행 중인지 확인: {API_BASE}</li>
              <li>환경변수 NEXT_PUBLIC_API_BASE가 설정되었는지 확인</li>
              <li>브라우저 콘솔에서 네트워크 오류 확인</li>
            </ul>
          </div>
        </div>
      </main>
    );
  }
}
