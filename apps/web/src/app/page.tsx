'use client';

import { useEffect, useMemo, useState } from 'react';

/** ======================
 *  공통 타입 & 유틸
 *  ====================== */
type BaseItem = {
  code: string;         // or symbol
  name: string;
  price: number;
  change: number;
  change_pct: number;   // % (ex. -0.31)
};

type GenericResp = {
  updated_at?: string;
  items: any[];
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || '';
const CRYPTO_LIST = process.env.NEXT_PUBLIC_CRYPTO_LIST || 'BTC,ETH,XRP,SOL,BNB';

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
  return '#6b7280';            // 보합
}

/** 서버 응답 → 공통 BaseItem 으로 느슨하게 매핑 */
function mapToBaseItem(raw: any): BaseItem {
  return {
    code: raw.code ?? raw.symbol ?? '',
    name: raw.name ?? raw.symbol ?? raw.code ?? '',
    price: Number(raw.price ?? 0),
    change: Number(raw.change ?? 0),
    change_pct: Number(raw.change_pct ?? 0),
  };
}

/** ======================
 *  UI 조각
 *  ====================== */
function TickerCard({ item }: { item: BaseItem }) {
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

function SkeletonCard() {
  return (
    <div style={styles.card}>
      <div style={{ ...styles.skel, width: 110, height: 16 }} />
      <div style={{ ...styles.skel, width: 90, height: 28, marginTop: 10 }} />
      <div style={{ ...styles.skel, width: 120, height: 16, marginTop: 10 }} />
    </div>
  );
}

/** 공용 섹션: url만 바꿔서 재사용 */
function BoardSection({
  title,
  url,
  column = 3,
  skeletonCount = 6,
}: {
  title: string;
  url: string;
  column?: number;
  skeletonCount?: number;
}) {
  const [items, setItems] = useState<BaseItem[] | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [minSkeletonDone, setMinSkeletonDone] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setMinSkeletonDone(true), 1000);
    fetchWithRetry<GenericResp>(url, {}, 3)
      .then((json) => setItems((json.items ?? []).map(mapToBaseItem)))
      .catch((e) => setErr(String(e)));
    return () => clearTimeout(t);
  }, [url]);

  const showSkeleton = !items && !err && !minSkeletonDone;

  return (
    <section>
      <div style={styles.sectionTitle}>{title}</div>

      {showSkeleton && (
        <div style={{ ...styles.grid, gridTemplateColumns: `repeat(${column}, minmax(0,1fr))` }}>
          {Array.from({ length: skeletonCount }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      )}

      {!showSkeleton && err && (
        <div style={styles.error}>
          데이터를 불러오지 못했어요. 잠시 후 다시 시도해주세요. <small>({err})</small>
        </div>
      )}

      {!showSkeleton && items && (
        <div style={{ ...styles.grid, gridTemplateColumns: `repeat(${column}, minmax(0,1fr))` }}>
          {items.map((it) => (
            <TickerCard key={`${title}-${it.code}`} item={it} />
          ))}
        </div>
      )}
    </section>
  );
}

/** ======================
 *  페이지
 *  ====================== */
export default function Home() {
  const worldUrl = useMemo(() => `${API_BASE}/api/market/world`, []);
  const krUrl = useMemo(() => `${API_BASE}/api/market/kr`, []);
  const cryptoUrl = useMemo(
    () => `${API_BASE}/api/crypto/tickers?list=${encodeURIComponent(CRYPTO_LIST)}`,
    []
  );

  return (
    <main style={styles.wrap}>
      <header style={styles.header}>
        <h1 style={styles.title}>🐝 양봉클럽</h1>
        <div style={styles.subtitle}>세계/국내 지수 · 코인 시세 요약</div>
      </header>

      {/* 세계 지수 9칸 */}
      <BoardSection title="세계 지수" url={worldUrl} column={3} skeletonCount={9} />

      {/* 국내 지수 3칸 (KOSPI/KOSDAQ/K200) */}
      <BoardSection title="국내 지수" url={krUrl} column={3} skeletonCount={3} />

      {/* 코인 4~6칸 */}
      <BoardSection title="코인" url={cryptoUrl} column={3} skeletonCount={6} />
    </main>
  );
}

/** ======================
 *  스타일 (의존성 無)
 *  ====================== */
const styles: Record<string, React.CSSProperties> = {
  wrap: {
    maxWidth: 1080,
    margin: '0 auto',
    padding: '28px 20px 60px',
    fontFamily:
      '-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica Neue,Arial,Apple Color Emoji,Segoe UI Emoji,Segoe UI Symbol',
    background: '#fafafa',
  },
  header: { marginBottom: 18 },
  title: { fontSize: 24, fontWeight: 700, margin: 0 },
  subtitle: { color: '#6b7280', marginTop: 4 },
  sectionTitle: { fontSize: 18, fontWeight: 700, margin: '22px 0 12px' },
  grid: {
    display: 'grid',
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
