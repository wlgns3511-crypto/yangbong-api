'use client';

import { useEffect, useMemo, useState } from 'react';

type WorldItem = {
  code: string;
  name: string;
  price: number;
  change: number;
  change_pct: number; // -0.31 처럼 %
};

type WorldResp = {
  updated_at: string;
  items: WorldItem[];
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || '';

/** 공용: 지연 + 재시도 fetch */
async function fetchWithRetry<T>(
  url: string,
  opts: RequestInit = {},
  attempts = 3,
  backoffMs = 700
): Promise<T> {
  let lastErr: unknown;
  for (let i = 0; i < attempts; i++) {
    try {
      const res = await fetch(url, { ...opts, cache: 'no-store' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return (await res.json()) as T;
    } catch (err) {
      lastErr = err;
      if (i < attempts - 1) {
        await new Promise((r) => setTimeout(r, backoffMs * Math.pow(1.4, i)));
      }
    }
  }
  throw lastErr;
}

/** 숫자 포맷 */
const nf0 = new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 });
const nf2 = new Intl.NumberFormat('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

/** 상승/하락 색상 */
function colorOf(v: number) {
  if (v > 0) return '#d32f2f'; // 빨강
  if (v < 0) return '#1976d2'; // 파랑
  return '#6b7280'; // 보합(회색)
}

/** 카드 컴포넌트 */
function TickerCard({ item }: { item: WorldItem }) {
  const upDown = item.change > 0 ? '▲' : item.change < 0 ? '▼' : '—';
  const changeColor = colorOf(item.change);

  return (
    <div style={styles.card}>
      <div style={styles.name}>{item.name}</div>
      <div style={styles.priceRow}>
        <span style={styles.price}>{nf0.format(item.price)}</span>
      </div>
      <div style={{ ...styles.changeRow, color: changeColor }}>
        <span style={{ marginRight: 6 }}>{upDown}</span>
        <span>{nf0.format(item.change)}</span>
        <span style={styles.dot}>·</span>
        <span>{nf2.format(item.change_pct)}%</span>
      </div>
    </div>
  );
}

/** 스켈레톤 */
function SkeletonCard() {
  return (
    <div style={styles.card}>
      <div style={{ ...styles.skel, width: 110, height: 16 }} />
      <div style={{ ...styles.skel, width: 90, height: 28, marginTop: 10 }} />
      <div style={{ ...styles.skel, width: 120, height: 16, marginTop: 10 }} />
    </div>
  );
}

export default function Home() {
  // 9칸: 다우, 나스닥, S&P500, 니케이, 상해종합, 항셍, FTSE, CAC, DAX
  const worldUrl = useMemo(() => `${API_BASE}/api/market/world`, []);
  const [world, setWorld] = useState<WorldItem[] | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [minSkeletonDone, setMinSkeletonDone] = useState(false); // 최소 1초 스켈레톤

  useEffect(() => {
    const t = setTimeout(() => setMinSkeletonDone(true), 1000);

    fetchWithRetry<WorldResp>(worldUrl, {}, 3)
      .then((json) => setWorld(json.items ?? []))
      .catch((e) => setErr(String(e)));

    return () => clearTimeout(t);
  }, [worldUrl]);

  const showSkeleton = !world && !err && !minSkeletonDone;

  return (
    <main style={styles.wrap}>
      <header style={styles.header}>
        <h1 style={styles.title}>🐝 양봉클럽</h1>
        <div style={styles.subtitle}>세계 지수 · 실시간 요약</div>
      </header>

      {/* 세계 지수 9칸 */}
      <section>
        <div style={styles.sectionTitle}>세계 지수</div>

        {showSkeleton && (
          <div style={styles.grid}>
            {Array.from({ length: 9 }).map((_, i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        )}

        {!showSkeleton && err && (
          <div style={styles.error}>
            데이터를 불러오지 못했어요. 새로고침 해주세요. <small>({err})</small>
          </div>
        )}

        {!showSkeleton && world && (
          <div style={styles.grid}>
            {world.map((it) => (
              <TickerCard key={it.code} item={it} />
            ))}
          </div>
        )}
      </section>

      {/* 국내 지수/코인 섹션은 동일 패턴으로 이어서 붙이면 됩니다. */}
    </main>
  );
}

/** 간단 스타일 (의존성 추가 없이) */
const styles: Record<string, React.CSSProperties> = {
  wrap: {
    maxWidth: 1080,
    margin: '0 auto',
    padding: '28px 20px 60px',
    fontFamily:
      '-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica Neue,Arial,Apple Color Emoji,Segoe UI Emoji,Segoe UI Symbol',
  },
  header: { marginBottom: 18 },
  title: { fontSize: 24, fontWeight: 700, margin: 0 },
  subtitle: { color: '#6b7280', marginTop: 4 },
  sectionTitle: { fontSize: 18, fontWeight: 700, margin: '18px 0 12px' },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, minmax(0, 1fr))',
    gap: 12,
  },
  card: {
    border: '1px solid #e5e7eb',
    borderRadius: 12,
    padding: 14,
    background: '#fff',
    boxShadow: '0 1px 2px rgba(0,0,0,0.03)',
  },
  name: { fontSize: 14, color: '#374151', fontWeight: 600 },
  priceRow: { marginTop: 8 },
  price: { fontSize: 22, fontWeight: 700, letterSpacing: 0.3 },
  changeRow: { marginTop: 6, display: 'flex', alignItems: 'center', fontWeight: 600 },
  dot: { margin: '0 6px', color: '#9ca3af' },
  error: {
    padding: 14,
    background: '#fff7ed',
    border: '1px solid #fed7aa',
    borderRadius: 10,
    color: '#9a3412',
  },
  skel: {
    background: 'linear-gradient(90deg,#f3f4f6 25%,#e5e7eb 37%,#f3f4f6 63%)',
    borderRadius: 8,
    animation: 'pulse 1.4s ease-in-out infinite',
  },
};
