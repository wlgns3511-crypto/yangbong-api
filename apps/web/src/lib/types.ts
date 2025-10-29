// lib/types.ts
export type WorldItem = { code: string; name: string; price: number; change: number; change_pct: number; };
export type WorldRes = { updated_at: string; items: WorldItem[]; };

export type KrItem = { code: string; name: string; price: number; change: number; change_pct: number; };
export type KrRes = { updated_at: string; items: KrItem[]; };

export type CryptoItem = {
  symbol: string; price_krw: number; price_usdt: number; krw_usd: number; kimchi_pct: number;
};
export type CryptoRes = { updated_at: string; items: CryptoItem[]; };

