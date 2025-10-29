// lib/ui.ts
export function deltaColor(v: number) {
  if (v > 0) return "text-red-600";   // 상승 빨강
  if (v < 0) return "text-blue-600";  // 하락 파랑
  return "text-gray-500";
}
export function fmt(n: number, digits = 2) {
  const a = Math.abs(n) >= 1000 ? 0 : digits;
  return n.toLocaleString(undefined, { maximumFractionDigits: a });
}
export function pct(n: number, digits = 2) {
  return `${n > 0 ? "+" : ""}${n.toFixed(digits)}%`;
}

