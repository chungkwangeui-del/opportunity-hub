"use client";

import { useEffect, useState, useCallback } from "react";
import { supabase } from "@/lib/supabase";
import { Opportunity } from "@/lib/types";
import { getBookmarks } from "@/lib/bookmarks";
import OpportunityCard from "@/components/OpportunityCard";
import LoadingSkeleton from "@/components/LoadingSkeleton";

export default function SavedContent() {
  const [opps, setOpps] = useState<Opportunity[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchAll = useCallback(async () => {
    const ids = getBookmarks();
    if (ids.length === 0) {
      setOpps([]);
      setLoading(false);
      return;
    }
    const { data } = await supabase
      .from("opportunities")
      .select("*")
      .in("id", ids)
      .eq("is_active", true);
    setOpps((data ?? []) as Opportunity[]);
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchAll();

    const handler = () => {
      const currentIds = new Set(getBookmarks());
      setOpps((prev) => {
        const filtered = prev.filter((o) => currentIds.has(o.id));
        if (filtered.length < prev.length) return filtered;
        fetchAll();
        return prev;
      });
    };
    window.addEventListener("bookmarks-changed", handler);
    return () => window.removeEventListener("bookmarks-changed", handler);
  }, [fetchAll]);

  return (
    <div className="mx-auto max-w-7xl px-6 py-10">
      <h1 className="mb-2 text-3xl font-bold text-gray-900">Saved Opportunities</h1>
      <p className="mb-8 text-sm text-gray-500">
        Your bookmarked opportunities are stored locally in this browser.
      </p>

      {loading && <LoadingSkeleton />}

      {!loading && opps.length === 0 && (
        <div className="rounded-xl border border-gray-200 bg-white p-12 text-center">
          <p className="text-lg text-gray-500">No saved opportunities yet.</p>
          <p className="mt-2 text-sm text-gray-400">
            Click the bookmark icon on any opportunity card to save it here.
          </p>
        </div>
      )}

      {!loading && opps.length > 0 && (
        <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
          {opps.map((o) => (
            <OpportunityCard key={o.id} opp={o} />
          ))}
        </div>
      )}
    </div>
  );
}
