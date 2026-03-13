"use client";

import { useState, useEffect } from "react";
import { isBookmarked, toggleBookmark } from "@/lib/bookmarks";

export default function BookmarkButton({ oppId, title }: { oppId: string; title: string }) {
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    setSaved(isBookmarked(oppId));
    const handler = () => setSaved(isBookmarked(oppId));
    window.addEventListener("bookmarks-changed", handler);
    return () => window.removeEventListener("bookmarks-changed", handler);
  }, [oppId]);

  return (
    <button
      onClick={() => toggleBookmark(oppId)}
      className={`shrink-0 rounded-full border px-4 py-2 text-sm font-medium transition-all ${
        saved
          ? "border-amber-300 bg-amber-50 text-amber-700 hover:bg-amber-100"
          : "border-gray-200 text-gray-500 hover:border-blue-300 hover:text-blue-600"
      }`}
      aria-label={saved ? `Remove ${title} from saved` : `Save ${title}`}
      type="button"
    >
      <svg className="mr-1.5 inline h-4 w-4" viewBox="0 0 24 24" fill={saved ? "currentColor" : "none"} stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
      </svg>
      {saved ? "Saved" : "Save"}
    </button>
  );
}
