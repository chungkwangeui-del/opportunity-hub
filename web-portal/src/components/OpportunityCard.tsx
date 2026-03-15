"use client";

import Link from "next/link";
import { useState, useEffect } from "react";
import { Opportunity, TYPE_COLOR, YEAR_COLOR, COUNTRY_FLAG } from "@/lib/types";
import { formatUpdatedDate, deadlineBadge } from "@/lib/format";
import { isBookmarked, toggleBookmark } from "@/lib/bookmarks";

export default function OpportunityCard({ opp }: { opp: Opportunity }) {
  const dl = deadlineBadge(opp.deadline);
  const flag = COUNTRY_FLAG[opp.country] ?? "🌍";
  const loc = [opp.city, opp.state, opp.country].filter(Boolean).join(", ");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    setSaved(isBookmarked(opp.id));
    const handler = () => setSaved(isBookmarked(opp.id));
    window.addEventListener("bookmarks-changed", handler);
    return () => window.removeEventListener("bookmarks-changed", handler);
  }, [opp.id]);

  return (
    <div className="group flex flex-col justify-between rounded-xl border border-gray-200 bg-white p-6 shadow-sm transition-all duration-200 hover:-translate-y-1 hover:shadow-md">
      <div>
        <div className="flex items-start justify-between gap-2">
          <p className="text-sm font-bold text-gray-900 leading-snug">{opp.organization}</p>
          <div className="flex shrink-0 items-center gap-1.5">
            <button
              onClick={() => toggleBookmark(opp.id)}
              className="text-gray-300 transition-colors hover:text-amber-500"
              aria-label={saved ? `Remove ${opp.title} from saved` : `Save ${opp.title}`}
              type="button"
            >
              <svg className="h-4 w-4" viewBox="0 0 24 24" fill={saved ? "currentColor" : "none"} stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" className={saved ? "text-amber-500" : ""} />
              </svg>
            </button>
            <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${TYPE_COLOR[opp.opportunity_type] ?? "bg-gray-100 text-gray-600"}`}>
              {opp.opportunity_type}
            </span>
          </div>
        </div>

        <h3 className="mt-1 text-base font-semibold leading-snug">
          <Link
            href={`/opportunities/${opp.id}`}
            className="text-blue-600 hover:text-blue-800 hover:underline"
          >
            {opp.title}
          </Link>
        </h3>

        {/* Field tag */}
        <div className="mt-2">
          <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-600">
            {opp.field}
          </span>
        </div>

        {/* Year level badges */}
        {opp.year_level?.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {opp.year_level.map((y) => (
              <span key={y} className={`rounded-full px-2 py-0.5 text-xs font-medium ${YEAR_COLOR[y] ?? "bg-gray-100 text-gray-600"}`}>
                {y}
              </span>
            ))}
          </div>
        )}

        {/* Location */}
        <p className="mt-2.5 text-sm text-gray-500">
          {flag} {loc}
          {opp.is_remote && <span className="ml-1.5 text-blue-500">🌐 Remote</span>}
        </p>

        {/* Deadline */}
        <div className="mt-2">
          <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${dl.cls}`}>
            {dl.text}
          </span>
        </div>

        {/* Compensation */}
        {opp.is_paid && opp.compensation && (
          <p className="mt-2 text-xs text-emerald-600">💰 {opp.compensation}</p>
        )}

        {/* Updated date */}
        {opp.updated_at && (
          <p className="mt-1.5 text-[11px] text-gray-400">{formatUpdatedDate(opp.updated_at)}</p>
        )}

        {/* Description */}
        <p className="mt-2 line-clamp-2 text-sm leading-relaxed text-gray-600">{opp.description}</p>
      </div>

      {/* CTA */}
      <a
        href={opp.url}
        target="_blank"
        rel="noopener noreferrer"
        aria-label={`Apply to ${opp.title} at ${opp.organization}`}
        className="mt-4 inline-flex items-center gap-1 text-sm font-semibold text-blue-600 transition-colors hover:text-blue-800"
      >
        Apply <span className="transition-transform group-hover:translate-x-0.5">→</span>
      </a>
    </div>
  );
}
