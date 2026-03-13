import { notFound } from "next/navigation";
import Link from "next/link";
import type { Metadata } from "next";
import { createClient } from "@supabase/supabase-js";
import type { Opportunity } from "@/lib/types";
import { TYPE_COLOR, YEAR_COLOR, COUNTRY_FLAG, FIELD_EMOJI } from "@/lib/types";
import { formatUpdatedDateFull } from "@/lib/format";
import BookmarkButton from "./BookmarkButton";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL ?? "";
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "";

function getServerClient() {
  return createClient(supabaseUrl, supabaseKey);
}

function deadlineBadge(deadline: string) {
  if (!deadline || deadline === "Unknown")
    return { text: "TBD", cls: "bg-gray-100 text-gray-500" };
  if (deadline === "Rolling")
    return { text: "Rolling", cls: "bg-emerald-100 text-emerald-700" };
  const d = new Date(deadline + "T23:59:59");
  const diff = Math.ceil((d.getTime() - Date.now()) / 86_400_000);
  if (diff < 0) return { text: "Expired", cls: "bg-red-100 text-red-700" };
  if (diff <= 14) return { text: `D-${diff}`, cls: "bg-orange-100 text-orange-700" };
  if (diff <= 30) return { text: `D-${diff}`, cls: "bg-yellow-100 text-yellow-700" };
  return { text: deadline, cls: "bg-gray-100 text-gray-500" };
}

interface PageProps {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { id } = await params;
  const sb = getServerClient();
  const { data } = await sb.from("opportunities").select("title, organization, description").eq("id", id).single();
  if (!data) return { title: "Opportunity Not Found" };
  return {
    title: `${data.title} at ${data.organization} — OpportunityHub`,
    description: data.description?.slice(0, 160) ?? `${data.title} at ${data.organization}`,
  };
}

export default async function OpportunityDetailPage({ params }: PageProps) {
  const { id } = await params;
  const sb = getServerClient();
  const { data, error } = await sb.from("opportunities").select("*").eq("id", id).single();

  if (error || !data) notFound();

  const opp = data as Opportunity;
  const dl = deadlineBadge(opp.deadline);
  const flag = COUNTRY_FLAG[opp.country] ?? "🌍";
  const loc = [opp.city, opp.state, opp.country].filter(Boolean).join(", ");
  const emoji = FIELD_EMOJI[opp.field] ?? "⚡";

  const { data: related } = await sb
    .from("opportunities")
    .select("id, title, organization, field, opportunity_type, deadline, country")
    .eq("is_active", true)
    .neq("id", opp.id)
    .or(`field.eq.${opp.field},organization.eq.${opp.organization}`)
    .limit(6);

  return (
    <div className="mx-auto max-w-4xl px-6 py-10">
      <Link
        href="/opportunities"
        className="mb-6 inline-flex items-center gap-1 text-sm font-medium text-gray-500 transition-colors hover:text-blue-600"
      >
        <svg className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
        Back to Opportunities
      </Link>

      <article className="rounded-2xl border border-gray-200 bg-white p-8 shadow-sm">
        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0 flex-1">
            <p className="text-sm font-bold text-gray-500">{opp.organization}</p>
            <h1 className="mt-1 text-2xl font-bold text-gray-900 sm:text-3xl">{opp.title}</h1>
          </div>
          <BookmarkButton oppId={opp.id} title={opp.title} />
        </div>

        {/* Tags */}
        <div className="mt-4 flex flex-wrap gap-2">
          <span className={`rounded-full px-3 py-1 text-xs font-medium ${TYPE_COLOR[opp.opportunity_type] ?? "bg-gray-100 text-gray-600"}`}>
            {opp.opportunity_type}
          </span>
          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
            {emoji} {opp.field}
          </span>
          {opp.year_level?.map((y) => (
            <span key={y} className={`rounded-full px-3 py-1 text-xs font-medium ${YEAR_COLOR[y] ?? "bg-gray-100 text-gray-600"}`}>
              {y}
            </span>
          ))}
        </div>

        {/* Info grid */}
        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          <div className="rounded-lg bg-gray-50 p-4">
            <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">Location</p>
            <p className="mt-1 text-sm font-medium text-gray-700">
              {flag} {loc}
              {opp.is_remote && <span className="ml-2 text-blue-500">🌐 Remote</span>}
            </p>
          </div>
          <div className="rounded-lg bg-gray-50 p-4">
            <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">Deadline</p>
            <div className="mt-1 flex items-center gap-2">
              <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${dl.cls}`}>{dl.text}</span>
              {opp.deadline !== "Unknown" && opp.deadline !== "Rolling" && (
                <span className="text-sm text-gray-500">{opp.deadline}</span>
              )}
            </div>
          </div>
          {opp.is_paid && opp.compensation && (
            <div className="rounded-lg bg-gray-50 p-4 sm:col-span-2">
              <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">Compensation</p>
              <p className="mt-1 text-sm font-medium text-emerald-600">💰 {opp.compensation}</p>
            </div>
          )}
          {opp.updated_at && (
            <div className="rounded-lg bg-gray-50 p-4">
              <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">Last updated</p>
              <p className="mt-1 text-sm font-medium text-gray-700">{formatUpdatedDateFull(opp.updated_at)}</p>
            </div>
          )}
        </div>

        {/* Description */}
        {opp.description && (
          <div className="mt-6">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-400">Description</h2>
            <p className="mt-2 whitespace-pre-line text-base leading-relaxed text-gray-700">{opp.description}</p>
          </div>
        )}

        {/* Apply CTA */}
        <div className="mt-8 flex flex-wrap items-center gap-4">
          <a
            href={opp.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-full bg-blue-600 px-8 py-3 text-sm font-semibold text-white shadow-md transition-all hover:bg-blue-700 hover:shadow-lg"
          >
            Apply Now
            <svg className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M14 5l7 7m0 0l-7 7m7-7H3" />
            </svg>
          </a>
          <span className="text-xs text-gray-400">Source: {opp.source || "curated"}</span>
        </div>
      </article>

      {/* Related opportunities */}
      {related && related.length > 0 && (
        <section className="mt-12">
          <h2 className="mb-4 text-lg font-bold text-gray-900">Related Opportunities</h2>
          <div className="grid gap-3 sm:grid-cols-2">
            {related.map((r) => {
              const rDl = deadlineBadge(r.deadline);
              return (
                <Link
                  key={r.id}
                  href={`/opportunities/${r.id}`}
                  className="rounded-xl border border-gray-200 bg-white p-4 transition-all hover:-translate-y-0.5 hover:shadow-md"
                >
                  <p className="text-xs font-bold text-gray-500">{r.organization}</p>
                  <p className="mt-0.5 text-sm font-semibold text-blue-600">{r.title}</p>
                  <div className="mt-2 flex flex-wrap items-center gap-2">
                    <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${TYPE_COLOR[r.opportunity_type] ?? "bg-gray-100 text-gray-600"}`}>
                      {r.opportunity_type}
                    </span>
                    <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${rDl.cls}`}>
                      {rDl.text}
                    </span>
                  </div>
                </Link>
              );
            })}
          </div>
        </section>
      )}
    </div>
  );
}
