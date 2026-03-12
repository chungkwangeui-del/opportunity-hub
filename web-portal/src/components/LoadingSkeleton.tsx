export default function LoadingSkeleton({ count = 6 }: { count?: number }) {
  return (
    <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="animate-pulse rounded-xl border border-gray-200 bg-white p-6">
          <div className="mb-2 flex items-center justify-between">
            <div className="h-4 w-1/2 rounded bg-gray-200" />
            <div className="h-5 w-16 rounded-full bg-gray-200" />
          </div>
          <div className="mb-4 h-5 w-3/4 rounded bg-gray-200" />
          <div className="mb-3 flex gap-2">
            <div className="h-5 w-14 rounded-full bg-gray-100" />
            <div className="h-5 w-14 rounded-full bg-gray-100" />
          </div>
          <div className="mb-1 h-3 w-full rounded bg-gray-100" />
          <div className="mb-1 h-3 w-full rounded bg-gray-100" />
          <div className="mb-4 h-3 w-2/3 rounded bg-gray-100" />
          <div className="h-4 w-20 rounded bg-gray-200" />
        </div>
      ))}
    </div>
  );
}
