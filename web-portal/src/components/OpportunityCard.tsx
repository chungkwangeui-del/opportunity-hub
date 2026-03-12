import { Opportunity, TYPE_COLOR, YEAR_COLOR, COUNTRY_FLAG } from "@/lib/types";

function deadlineBadge(deadline: string) {
  if (!deadline || deadline === "Unknown")
    return { text: "TBD", cls: "bg-gray-100 text-gray-500" };
  if (deadline === "Rolling")
    return { text: "Rolling", cls: "bg-emerald-100 text-emerald-700" };

  const d = new Date(deadline);
  const diff = Math.ceil((d.getTime() - Date.now()) / 86_400_000);
  if (diff < 0) return { text: "Expired", cls: "bg-red-100 text-red-700" };
  if (diff <= 14) return { text: `D-${diff}`, cls: "bg-orange-100 text-orange-700" };
  if (diff <= 30) return { text: `D-${diff}`, cls: "bg-yellow-100 text-yellow-700" };
  return { text: deadline, cls: "bg-gray-100 text-gray-500" };
}

export default function OpportunityCard({ opp }: { opp: Opportunity }) {
  const dl = deadlineBadge(opp.deadline);
  const flag = COUNTRY_FLAG[opp.country] ?? "🌍";
  const loc = [opp.city, opp.state, opp.country].filter(Boolean).join(", ");

  return (
    <div className="group flex flex-col justify-between rounded-xl border border-gray-200 bg-white p-6 shadow-sm transition-all duration-200 hover:-translate-y-1 hover:shadow-md">
      <div>
        {/* Header row: org + type badge */}
        <div className="flex items-start justify-between gap-2">
          <p className="text-sm font-bold text-gray-900 leading-snug">{opp.organization}</p>
          <span className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs font-medium ${TYPE_COLOR[opp.opportunity_type] ?? "bg-gray-100 text-gray-600"}`}>
            {opp.opportunity_type}
          </span>
        </div>

        {/* Title */}
        <h3 className="mt-1 text-base font-semibold text-blue-600 leading-snug">{opp.title}</h3>

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

        {/* Description */}
        <p className="mt-2 line-clamp-2 text-sm leading-relaxed text-gray-600">{opp.description}</p>
      </div>

      {/* CTA */}
      <a
        href={opp.url}
        target="_blank"
        rel="noopener noreferrer"
        className="mt-4 inline-flex items-center gap-1 text-sm font-semibold text-blue-600 transition-colors hover:text-blue-800"
      >
        Apply <span className="transition-transform group-hover:translate-x-0.5">→</span>
      </a>
    </div>
  );
}
