// app/page.tsx
"use client";

import { useEffect, useState } from "react";
import { fetchJson, withMinDelay } from "@/lib/api";
import { Card, Skeleton } from "@/components/Card";
import { deltaColor, fmt, pct } from "@/lib/ui";
import type { WorldRes, KrRes, CryptoRes } from "@/lib/types";

type LoadState<T> = { data?: T; loading: boolean; error?: string };

export default function Home() {
  const [world, setWorld] = useState<LoadState<WorldRes>>({ loading: true });
  const [kr, setKr] = useState<LoadState<KrRes>>({ loading: true });
  const [crypto, setCrypto] = useState<LoadState<CryptoRes>>({ loading: true });

  useEffect(() => {
    // 1) 세계 지수 9개
    withMinDelay(fetchJson<WorldRes>("/api/market/world"))
      .then((d) => setWorld({ loading: false, data: d }))
      .catch((e) => setWorld({ loading: false, error: String(e) }));

    // 2) 국내 지수 3개
    withMinDelay(fetchJson<KrRes>("/api/market/kr"))
      .then((d) => setKr({ loading: false, data: d }))
      .catch((e) => setKr({ loading: false, error: String(e) }));

    // 3) 코인(원하면 목록 바꿔도 됨)
    withMinDelay(fetchJson<CryptoRes>("/api/crypto/tickers?list=BTC,ETH,XRP,SOL"))
      .then((d) => setCrypto({ loading: false, data: d }))
      .catch((e) => setCrypto({ loading: false, error: String(e) }));
  }, []);

  return (
    <main className="mx-auto max-w-6xl p-4 space-y-8">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">양봉클럽</h1>
        <span className="text-sm text-gray-500">LIVE Market & News</span>
      </header>

      {/* 국내 지수 */}
      <section>
        <h2 className="mb-3 font-semibold">국내 지수</h2>
        {kr.loading ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <Card><Skeleton lines={3} /></Card>
            <Card><Skeleton lines={3} /></Card>
            <Card><Skeleton lines={3} /></Card>
          </div>
        ) : kr.error ? (
          <div className="text-sm text-red-600">에러: {kr.error}</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {kr.data!.items.map((x) => (
              <Card key={x.code}>
                <div className="flex items-center justify-between">
                  <div className="font-medium">{x.name}</div>
                  <div className="text-xs text-gray-500">{x.code}</div>
                </div>
                <div className="mt-2 text-xl font-semibold">{fmt(x.price, 2)}</div>
                <div className={`mt-1 text-sm ${deltaColor(x.change_pct)}`}>
                  {x.change > 0 ? "+" : ""}{fmt(x.change, 2)} ({pct(x.change_pct)})
                </div>
              </Card>
            ))}
          </div>
        )}
      </section>

      {/* 세계 지수 9개 */}
      <section>
        <h2 className="mb-3 font-semibold">세계 지수</h2>
        {world.loading ? (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {Array.from({ length: 9 }).map((_, i) => (
              <Card key={i}><Skeleton lines={3} /></Card>
            ))}
          </div>
        ) : world.error ? (
          <div className="text-sm text-red-600">에러: {world.error}</div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {world.data!.items.slice(0, 9).map((x) => (
              <Card key={x.code}>
                <div className="flex items-center justify-between">
                  <div className="font-medium">{x.name}</div>
                  <div className="text-xs text-gray-500">{x.code}</div>
                </div>
                <div className="mt-2 text-xl font-semibold">{fmt(x.price, 2)}</div>
                <div className={`mt-1 text-sm ${deltaColor(x.change_pct)}`}>
                  {x.change > 0 ? "+" : ""}{fmt(x.change, 2)} ({pct(x.change_pct)})
                </div>
              </Card>
            ))}
          </div>
        )}
      </section>

      {/* 코인 4~6개 */}
      <section>
        <h2 className="mb-3 font-semibold">코인</h2>
        {crypto.loading ? (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <Card key={i}><Skeleton lines={3} /></Card>
            ))}
          </div>
        ) : crypto.error ? (
          <div className="text-sm text-red-600">에러: {crypto.error}</div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {crypto.data!.items.slice(0, 6).map((x) => (
              <Card key={x.symbol}>
                <div className="flex items-center justify-between">
                  <div className="font-medium">{x.symbol}</div>
                  <div className="text-xs text-gray-500">USD {fmt(x.price_usdt, 2)}</div>
                </div>
                <div className="mt-2 text-xl font-semibold">₩ {fmt(x.price_krw, 0)}</div>
                <div className={`mt-1 text-sm ${deltaColor(x.kimchi_pct)}`}>
                  김프 {x.kimchi_pct > 0 ? "+" : ""}{x.kimchi_pct.toFixed(2)}%
                </div>
              </Card>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
