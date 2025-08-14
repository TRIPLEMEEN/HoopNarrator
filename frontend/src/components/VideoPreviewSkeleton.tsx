export default function VideoPreviewSkeleton() {
  return (
    <div className="animate-pulse">
      <div className="aspect-video bg-hoop-gray-100 rounded-lg flex items-center justify-center">
        <div className="text-hoop-gray-300">
          <svg
            className="w-12 h-12"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1}
              d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
            />
          </svg>
        </div>
      </div>
      <div className="mt-2 h-4 bg-hoop-gray-100 rounded w-3/4"></div>
    </div>
  );
}
