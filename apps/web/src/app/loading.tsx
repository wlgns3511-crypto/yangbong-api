// app/loading.tsx
export default function Loading() {
  return (
    <div className="p-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: 9 }).map((_, i) => (
        <div key={i} className="animate-pulse rounded-xl border p-4">
          <div className="h-4 w-28 bg-gray-300/70 rounded mb-3" />
          <div className="h-6 w-20 bg-gray-300/70 rounded" />
        </div>
      ))}
    </div>
  );
}

