"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabase";
import {
  OPPORTUNITY_TYPES,
  TYPE_EMOJI,
  TYPE_DESC,
  FIELDS,
  FIELD_EMOJI,
} from "@/lib/types";
import OpportunityCard from "@/components/OpportunityCard";
import type { Opportunity } from "@/lib/types";

export default function Home() {
  const [totalCount, setTotalCount] = useState(0);
  const [countryCount, setCountryCount] = useState(0);
  const [fieldCount, setFieldCount] = useState(0);
  const [typeCounts, setTypeCounts] = useState<Record<string, number>>({});
  const [fieldCounts, setFieldCounts] = useState<Record<string, number>>({});
  const [latest, setLatest] = useState<Opportunity[]>([]);

  useEffect(() => {
    async function load() {
      const { data: rows } = await supabase
        .from("opportunities")
        .select("country, field, opportunity_type")
        .eq("is_active", true);

      if (rows) {
        setTotalCount(rows.length);
        setCountryCount(new Set(rows.map((r) => r.country).filter(Boolean)).size);
        setFieldCount(new Set(rows.map((r) => r.field).filter(Boolean)).size);

        const tc: Record<string, number> = {};
        const fc: Record<string, number> = {};
        for (const r of rows) {
          tc[r.opportunity_type] = (tc[r.opportunity_type] || 0) + 1;
          fc[r.field] = (fc[r.field] || 0) + 1;
        }
        setTypeCounts(tc);
        setFieldCounts(fc);
      }

      const { data: recent } = await supabase
        .from("opportunities")
        .select("*")
        .eq("is_active", true)
        .order("created_at", { ascending: false })
        .limit(6);
      if (recent) setLatest(recent as Opportunity[]);
    }
    load();
  }, []);

  return (
    <>
      {/* Hero */}
      <section className="bg-gradient-to-b from-slate-50 to-white px-6 pb-20 pt-24 text-center">
        <h1 className="mx-auto max-w-3xl text-4xl font-bold leading-tight text-gray-900 sm:text-5xl">
          Every STEM Opportunity.{" "}
          <span className="text-blue-600">One Place.</span>
        </h1>
        <p className="mx-auto mt-5 max-w-2xl text-lg text-gray-600">
          Research positions, internships, fellowships, and more — updated daily
          from hundreds of sources worldwide.
        </p>
        <Link
          href="/opportunities"
          className="mt-8 inline-flex items-center gap-2 rounded-full bg-amber-500 px-8 py-3.5 text-sm font-semibold text-white shadow-md transition-all hover:bg-amber-600 hover:shadow-lg"
        >
          Find Opportunities <span>→</span>
        </Link>
      </section>

      {/* Opportunity Types (8 cards) */}
      <section className="mx-auto max-w-6xl px-6 py-16">
        <h2 className="mb-8 text-center text-2xl font-bold text-gray-900">
          Explore by Type
        </h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {OPPORTUNITY_TYPES.map((t) => (
            <Link
              key={t}
              href={`/opportunities?type=${encodeURIComponent(t)}`}
              className="flex items-start gap-3 rounded-xl border border-gray-200 bg-white p-5 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md"
            >
              <span className="text-2xl">{TYPE_EMOJI[t]}</span>
              <div>
                <p className="font-semibold text-gray-900">{t}</p>
                <p className="mt-0.5 text-xs text-gray-500">{TYPE_DESC[t]}</p>
                <p className="mt-1 text-xs font-medium text-blue-600">
                  {typeCounts[t] ?? 0} available
                </p>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* STEM Fields */}
      <section className="bg-gray-50 px-6 py-16">
        <h2 className="mb-8 text-center text-2xl font-bold text-gray-900">
          Browse by Field
        </h2>
        <div className="mx-auto flex max-w-5xl flex-wrap justify-center gap-3">
          {FIELDS.map((f) => (
            <Link
              key={f}
              href={`/opportunities?field=${encodeURIComponent(f)}`}
              className="flex items-center gap-2 rounded-full border border-gray-200 bg-white px-4 py-2.5 text-sm font-medium text-gray-700 shadow-sm transition-all hover:border-blue-300 hover:text-blue-600 hover:shadow"
            >
              <span>{FIELD_EMOJI[f]}</span>
              {f}
              <span className="ml-1 rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500">
                {fieldCounts[f] ?? 0}
              </span>
            </Link>
          ))}
        </div>
      </section>

      {/* Stats bar */}
      <section className="border-y border-gray-200 bg-white px-6 py-10">
        <div className="mx-auto grid max-w-4xl grid-cols-2 gap-6 sm:grid-cols-4">
          {[
            { val: totalCount, label: "Opportunities" },
            { val: countryCount, label: "Countries" },
            { val: fieldCount, label: "STEM Fields" },
            { val: "Daily", label: "Updated" },
          ].map((s, i) => (
            <div key={i} className="text-center">
              <p className="text-3xl font-bold text-blue-600">{s.val}</p>
              <p className="mt-1 text-sm text-gray-500">{s.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Latest opportunities */}
      {latest.length > 0 && (
        <section className="mx-auto max-w-6xl px-6 py-16">
          <div className="mb-8 flex items-center justify-between">
            <h2 className="text-2xl font-bold text-gray-900">Latest Opportunities</h2>
            <Link href="/opportunities" className="text-sm font-medium text-blue-600 hover:text-blue-800">
              Browse all →
            </Link>
          </div>
          <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
            {latest.map((opp) => (
              <OpportunityCard key={opp.id} opp={opp} />
            ))}
          </div>
        </section>
      )}
    </>
  );
}
