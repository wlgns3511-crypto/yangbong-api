"use client";

import { useEffect, useState } from "react";

export default function Home() {
  const [apiBase] = useState(process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000");
  const [health, setHealth] = useState<string>("(loading)");
  const [pong, setPong] = useState<string>("(loading)");

  useEffect(() => {
    fetch(`${apiBase}/health`).then(r=>r.json()).then(d=>setHealth(JSON.stringify(d))).catch(()=>setHealth("(error)"));
    fetch(`${apiBase}/ping`).then(r=>r.json()).then(d=>setPong(JSON.stringify(d))).catch(()=>setPong("(error)"));
  }, [apiBase]);

  return (
    <main style={{padding:24, fontFamily:"ui-sans-serif"}}>
      <h1 style={{fontSize:28, fontWeight:800, marginBottom:8}}>양봉클럽 Web</h1>
      <p style={{opacity:0.7, marginBottom:24}}>API Base: <code>{apiBase}</code></p>

      <div style={{display:"grid", gap:12, maxWidth:680}}>
        <div style={{padding:16, border:"1px solid #ddd", borderRadius:12}}>
          <h2 style={{margin:0, fontSize:18}}>GET /health</h2>
          <pre style={{marginTop:8, background:"#fafafa", padding:12, borderRadius:8}}>{health}</pre>
        </div>
        <div style={{padding:16, border:"1px solid #ddd", borderRadius:12}}>
          <h2 style={{margin:0, fontSize:18}}>GET /ping</h2>
          <pre style={{marginTop:8, background:"#fafafa", padding:12, borderRadius:8}}>{pong}</pre>
        </div>
      </div>
    </main>
  );
}

