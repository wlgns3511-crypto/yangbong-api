'use client';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="max-w-6xl mx-auto p-6">
      <h2 className="text-2xl font-bold text-red-600 mb-4">오류 발생</h2>
      <p className="text-gray-700 mb-4">{error.message}</p>
      <button
        onClick={reset}
        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
      >
        다시 시도
      </button>
    </div>
  );
}

