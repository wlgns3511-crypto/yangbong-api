// lib/api.ts
const BASE = process.env.NEXT_PUBLIC_API_BASE || "";

async function fetchWithRetry<T>(url: string, init?: RequestInit, retries = 3, delayMs = 500): Promise<T> {
  let last: any;
  for (let i = 0; i < retries; i++) {
    try {
      const res = await fetch(url, { ...init, cache: "no-store" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return (await res.json()) as T;
    } catch (e) {
      last = e;
      if (i < retries - 1) await new Promise(r => setTimeout(r, delayMs));
    }
  }
  throw last;
}

export type Ticker = { code: string; name: string; price: number; change: number; change_pct: number; };

export async function getWorld() {
  return fetchWithRetry<{ updated_at: string; items: Ticker[] }>(`${BASE}/api/market/world`);
}

export async function getKorea() {
  return fetchWithRetry<{ updated_at: string; items: Ticker[] }>(`${BASE}/api/market/kr`);
}

export async function getCrypto(list?: string) {
  const q = list ? `?list=${encodeURIComponent(list)}` : "";
  return fetchWithRetry<{ updated_at: string; items: Ticker[] }>(`${BASE}/api/crypto/tickers${q}`);
}

