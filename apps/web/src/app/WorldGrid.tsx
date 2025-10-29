"use client";
import { useEffect, useState } from "react";

type WorldItem = { key:string; name:string; price:number; change:number; change_pct:number; };

export default function WorldGrid() {
  const apiBase = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
  const [items, setItems] = useState<WorldItem[]>([]);
  const [err, setErr] = useState<string|null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const r = await fetch(`${apiBase}/market/world`, { cache: "no-store" });
        const j = await r.json();
        if (!j?.ok) throw new Error("API error");
        const order = ["DOW","NASDAQ","SP500","NIKKEI","SSEC","HSI","FTSE","CAC40","DAX"];
        const arr = Object.values(j.data || {}) as any[];
        arr.sort((a,b)=> order.indexOf(a.key) - order.indexOf(b.key));
        setItems(arr.map((d:any)=>({ key:d.key, name:d.name, price:d.price, change:d.change, change_pct:d.change_pct })));
      } catch (e:any) { setErr(e?.message || "failed"); }
      finally { setLoading(false); }
    })();
  }, [apiBase]);

  if (loading) return <div style={{opacity:.7}}>세계지수 불러오는 중…</div>;
  if (err) return <div style={{color:"#c00"}}>에러: {err}</div>;

  return (
    <div style={{display:"grid", gridTemplateColumns:"repeat(3,minmax(0,1fr))", gap:12, maxWidth:900}}>
      {items.map(it=>{
        const up = it.change > 0;
        const color = up ? "#d00" : it.change < 0 ? "#06c" : "#555";
        return (
          <div key={it.key} style={{border:"1px solid #e5e7eb", borderRadius:14, padding:16}}>
            <div style={{display:"flex", justifyContent:"space-between", marginBottom:8}}>
              <strong>{it.name}</strong><span style={{fontSize:12, opacity:.6}}>{it.key}</span>
            </div>
            <div style={{fontSize:22, fontWeight:800, marginBottom:6}}>{it.price?.toLocaleString?.()}</div>
            <div style={{fontSize:14, color}}>
              {up ? "▲" : it.change < 0 ? "▼" : "•"} {it.change?.toLocaleString?.()} ({it.change_pct}%)
            </div>
          </div>
        );
      })}
    </div>
  );
}
