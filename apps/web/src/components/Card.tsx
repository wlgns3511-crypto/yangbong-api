// components/Card.tsx
import React from "react";

export function Card({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-gray-200 px-4 py-3 shadow-sm bg-white dark:bg-zinc-900 dark:border-zinc-800">
      {children}
    </div>
  );
}

export function Skeleton({ lines = 2 }: { lines?: number }) {
  return (
    <div className="animate-pulse space-y-2">
      {Array.from({ length: lines }).map((_, i) => (
        <div key={i} className="h-4 rounded bg-gray-200 dark:bg-zinc-800" />
      ))}
    </div>
  );
}

