"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { fetchOpportunities } from "@/lib/supabase";
import { Opportunity, LOCATION_GROUPS, FilterState } from "@/lib/types";
import FilterSidebar from "@/components/FilterSidebar";
import OpportunityCard from "@/components/OpportunityCard";
import LoadingSkeleton from "@/components/LoadingSkeleton";

const PAGE_SIZE = 24;

const EMPTY: FilterState = {
  q: "",
  fields: [],
  types: [],
  years: [],
  locations: [],
  paidOnly: false,
  sort: "newest",
};

function parseArray(v: string | null): string[] {
  return v ? v.split(",").filter(Boolean) : [];
}

export default function OpportunitiesContent() {
  const router = useRouter();
  const sp = useSearchParams();

  const [opps, setOpps] = useState<Opportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE);

  const [filters, setFilters] = useState<FilterState>({
    q: sp.get("q") ?? "",
    fields: parseArray(sp.get("field")),
    types: parseArray(sp.get("type")),
    years: parseArray(sp.get("year")),
    locations: parseArray(sp.get("loc")),
    paidOnly: sp.get("paid") === "true",
    sort: (sp.get("sort") as "newest" | "deadline") ?? "newest",
  });

  useEffect(() => {
    setFilters({
      q: sp.get("q") ?? "",
      fields: parseArray(sp.get("field")),
      types: parseArray(sp.get("type")),
      years: parseArray(sp.get("year")),
      locations: parseArray(sp.get("loc")),
      paidOnly: sp.get("paid") === "true",
      sort: (sp.get("sort") as "newest" | "deadline") ?? "newest",
    });
    setVisibleCount(PAGE_SIZE);
  }, [sp]);

  const loadOpportunities = useCallback(async () => {
    setLoading(true);
    const { data, error: err } = await fetchOpportunities();
    if (err) {
      setError("Failed to load opportunities.");
    } else {
      setError(null);
      setOpps(data);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    loadOpportunities();
  }, [loadOpportunities]);

  const syncUrl = useCallback(
    (f: FilterState) => {
      const p = new URLSearchParams();
      if (f.q) p.set("q", f.q);
      if (f.fields.length) p.set("field", f.fields.join(","));
      if (f.types.length) p.set("type", f.types.join(","));
      if (f.years.length) p.set("year", f.years.join(","));
      if (f.locations.length) p.set("loc", f.locations.join(","));
      if (f.paidOnly) p.set("paid", "true");
      if (f.sort !== "newest") p.set("sort", f.sort);
      const qs = p.toString();
      router.replace(qs ? `/opportunities?${qs}` : "/opportunities", { scroll: false });
    },
    [router]
  );

  const handleChange = useCallback((f: FilterState) => {
    setFilters(f);
    setVisibleCount(PAGE_SIZE);
    syncUrl(f);
  }, [syncUrl]);

  const handleReset = useCallback(() => {
    setFilters(EMPTY);
    setVisibleCount(PAGE_SIZE);
    router.replace("/opportunities", { scroll: false });
  }, [router]);

  const filtered = useMemo(() => {
    let r = opps;

    if (filters.q) {
      const q = filters.q.toLowerCase();
      r = r.filter(
        (o) =>
          o.organization.toLowerCase().includes(q) ||
          o.title.toLowerCase().includes(q) ||
          (o.description && o.description.toLowerCase().includes(q))
      );
    }

    if (filters.fields.length)
      r = r.filter((o) => filters.fields.includes(o.field));

    if (filters.types.length)
      r = r.filter((o) => filters.types.includes(o.opportunity_type));

    if (filters.years.length)
      r = r.filter((o) =>
        o.year_level?.some(
          (y) => filters.years.includes(y) || y === "Any"
        )
      );

    if (filters.locations.length) {
      r = r.filter((o) => {
        for (const loc of filters.locations) {
          if (loc === "Remote" && o.is_remote) return true;
          if (loc === "USA" && LOCATION_GROUPS.USA.includes(o.country)) return true;
          if (loc === "South Korea" && LOCATION_GROUPS["South Korea"].includes(o.country)) return true;
        }
        return false;
      });
    }

    if (filters.paidOnly) r = r.filter((o) => o.is_paid === true);

    if (filters.sort === "deadline") {
      r = [...r].sort((a, b) => {
        const parse = (d: string) =>
          d && d !== "Unknown" && d !== "Rolling"
            ? new Date(d).getTime()
            : Infinity;
        return parse(a.deadline) - parse(b.deadline);
      });
    }

    return r;
  }, [opps, filters]);

  const activeChips = useMemo(() => {
    const chips: { label: string; remove: () => void }[] = [];
    if (filters.q) chips.push({ label: `"${filters.q}"`, remove: () => handleChange({ ...filters, q: "" }) });
    for (const f of filters.fields) chips.push({ label: f, remove: () => handleChange({ ...filters, fields: filters.fields.filter((x) => x !== f) }) });
    for (const t of filters.types) chips.push({ label: t, remove: () => handleChange({ ...filters, types: filters.types.filter((x) => x !== t) }) });
    for (const y of filters.years) chips.push({ label: y, remove: () => handleChange({ ...filters, years: filters.years.filter((x) => x !== y) }) });
    for (const l of filters.locations) chips.push({ label: l, remove: () => handleChange({ ...filters, locations: filters.locations.filter((x) => x !== l) }) });
    if (filters.paidOnly) chips.push({ label: "Paid only", remove: () => handleChange({ ...filters, paidOnly: false }) });
    return chips;
  }, [filters, handleChange]);

  return (
    <div className="mx-auto max-w-7xl px-6 py-10">
      <h1 className="mb-6 text-3xl font-bold text-gray-900">Opportunities</h1>

      <div className="flex gap-8">
        <FilterSidebar
          filters={filters}
          onChange={handleChange}
          onReset={handleReset}
          resultCount={filtered.length}
          mobileOpen={mobileOpen}
          onToggleMobile={() => setMobileOpen(!mobileOpen)}
        />

        <div className="min-w-0 flex-1">
          {activeChips.length > 0 && (
            <div className="mb-4 flex flex-wrap items-center gap-2">
              {activeChips.map((chip, i) => (
                <span
                  key={i}
                  className="inline-flex items-center gap-1 rounded-full bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700"
                >
                  {chip.label}
                  <button
                    onClick={chip.remove}
                    className="ml-0.5 rounded-full p-0.5 hover:bg-blue-100"
                    aria-label={`Remove filter: ${chip.label}`}
                    type="button"
                  >
                    <svg className="h-3 w-3" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </span>
              ))}
              <button
                onClick={handleReset}
                className="text-xs font-medium text-gray-500 hover:text-gray-700"
                type="button"
              >
                Clear all
              </button>
            </div>
          )}

          {loading && <LoadingSkeleton />}

          {error && (
            <div className="rounded-xl border border-red-200 bg-red-50 p-8 text-center">
              <p className="text-red-600">{error}</p>
              <button
                onClick={loadOpportunities}
                className="mt-4 rounded-full bg-red-600 px-6 py-2 text-sm font-medium text-white transition-colors hover:bg-red-700"
              >
                Try again
              </button>
            </div>
          )}

          {!loading && !error && filtered.length === 0 && (
            <div className="rounded-xl border border-gray-200 bg-white p-12 text-center">
              {opps.length === 0 ? (
                <p className="text-lg text-gray-500">No opportunities in the database yet. Check back after the next scraper run.</p>
              ) : (
                <>
                  <p className="text-lg text-gray-500">No opportunities match your filters.</p>
                  <button
                    onClick={handleReset}
                    className="mt-4 rounded-full bg-blue-600 px-6 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700"
                  >
                    Clear all filters
                  </button>
                </>
              )}
            </div>
          )}

          {!loading && !error && filtered.length > 0 && (
            <>
              <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
                {filtered.slice(0, visibleCount).map((o) => (
                  <OpportunityCard key={o.id} opp={o} />
                ))}
              </div>

              {visibleCount < filtered.length && (
                <div className="mt-8 text-center">
                  <button
                    onClick={() => setVisibleCount((v) => v + PAGE_SIZE)}
                    className="rounded-full border border-blue-600 px-8 py-2.5 text-sm font-semibold text-blue-600 transition-colors hover:bg-blue-600 hover:text-white"
                  >
                    Load more ({filtered.length - visibleCount} remaining)
                  </button>
                </div>
              )}

              <p className="mt-4 text-center text-sm text-gray-400">
                Showing {Math.min(visibleCount, filtered.length)} of {filtered.length}
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
