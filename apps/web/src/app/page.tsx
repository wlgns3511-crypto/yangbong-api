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
  // 3개 API 병렬 호출 + 3회 재시도 로직은 lib/api에 있음
  const [world, kr, crypto] = await Promise.all([
    getWorld(), 
    getKorea(), 
    getCrypto(process.env.NEXT_PUBLIC_CRYPTO_LIST),
  ]);

  // 세계 9칸, 국내 3칸, 코인 4~6칸
  const world9 = world.items.slice(0, 9);
  const kr3 = kr.items.slice(0, 3);
  const cxs = crypto.items.slice(0, 6);

  return (
    <main className="max-w-6xl mx-auto p-6 space-y-8">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">양봉클럽 · 마켓 보드</h1>
        <div className="text-sm text-gray-500">API: {process.env.NEXT_PUBLIC_API_BASE}</div>
      </header>

      {/* 국내 지수 (3칸) */}
      <section>
        <h2 className="mb-3 font-semibold">국내 지수</h2>
        <div className="grid gap-3 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
          {kr3.map((t) => <Chip key={t.code} t={t} />)}
        </div>
      </section>

      {/* 세계 지수 (9칸) */}
      <section>
        <h2 className="mb-3 font-semibold">세계 지수</h2>
        <div className="grid gap-3 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
          {world9.map((t) => <Chip key={t.code} t={t} />)}
        </div>
      </section>

      {/* 코인 (4~6칸) */}
      <section>
        <h2 className="mb-3 font-semibold">코인</h2>
        <div className="grid gap-3 grid-cols-2 sm:grid-cols-3 lg:grid-cols-6">
          {cxs.map((t) => <Chip key={t.code} t={t} />)}
        </div>
      </section>
    </main>
  );
}
