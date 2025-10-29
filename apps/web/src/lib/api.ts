// lib/api.ts
const BASE = process.env.NEXT_PUBLIC_API_BASE || "";

function sleep(ms: number) { return new Promise(r => setTimeout(r, ms)); }

export async function fetchJson<T>(path: string, init?: RequestInit, tries = 3, timeoutMs = 8000): Promise<T> {
  const url = path.startsWith("http") ? path : `${BASE}${path}`;
  let lastErr: any;
  for (let i = 0; i < tries; i++) {
    const c = new AbortController();
    const t = setTimeout(() => c.abort(), timeoutMs);
    try {
      const res = await fetch(url, { ...init, cache: "no-store", signal: c.signal });
      clearTimeout(t);
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      return (await res.json()) as T;
    } catch (e) {
      clearTimeout(t);
      lastErr = e;
      if (i < tries - 1) await sleep(400 * (i + 1)); // 0.4s, 0.8s, 1.2s
    }
  }
  throw lastErr;
}

// 최소 표시 시간(스켈레톤 1초 보장)
export async function withMinDelay<T>(p: Promise<T>, minMs = 1000): Promise<T> {
  const [res] = await Promise.all([p, sleep(minMs)]);
  return res;
}

