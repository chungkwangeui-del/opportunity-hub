"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { supabase } from "@/lib/supabase";
import { Opportunity, LOCATION_GROUPS } from "@/lib/types";
import FilterSidebar from "@/components/FilterSidebar";
import OpportunityCard from "@/components/OpportunityCard";
import LoadingSkeleton from "@/components/LoadingSkeleton";

interface FilterState {
  q: string;
  fields: string[];
  types: string[];
  years: string[];
  locations: string[];
  paidOnly: boolean;
  sort: "newest" | "deadline";
}

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
    async function load() {
      setLoading(true);
      const { data, error: err } = await supabase
        .from("opportunities")
        .select("*")
        .eq("is_active", true)
        .order("created_at", { ascending: false });
      if (err) setError("Failed to load opportunities.");
      else setOpps((data ?? []) as Opportunity[]);
      setLoading(false);
    }
    load();
  }, []);

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

  const handleChange = (f: FilterState) => {
    setFilters(f);
    syncUrl(f);
  };

  const handleReset = () => {
    setFilters(EMPTY);
    router.replace("/opportunities", { scroll: false });
  };

  const filtered = useMemo(() => {
    let r = opps;

    if (filters.q) {
      const q = filters.q.toLowerCase();
      r = r.filter(
        (o) =>
          o.organization.toLowerCase().includes(q) ||
          o.title.toLowerCase().includes(q)
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
          {loading && <LoadingSkeleton />}

          {error && (
            <div className="rounded-xl border border-red-200 bg-red-50 p-8 text-center">
              <p className="text-red-600">{error}</p>
            </div>
          )}

          {!loading && !error && filtered.length === 0 && (
            <div className="rounded-xl border border-gray-200 bg-white p-12 text-center">
              <p className="text-lg text-gray-500">No opportunities match your filters.</p>
              <button
                onClick={handleReset}
                className="mt-4 rounded-full bg-blue-600 px-6 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700"
              >
                Clear all filters
              </button>
            </div>
          )}

          {!loading && !error && filtered.length > 0 && (
            <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
              {filtered.map((o) => (
                <OpportunityCard key={o.id} opp={o} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
