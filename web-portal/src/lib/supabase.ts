import { createClient, SupabaseClient } from "@supabase/supabase-js";
import type { Opportunity } from "./types";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL ?? "";
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "";

function buildClient(): SupabaseClient {
  if (!supabaseUrl || !supabaseUrl.startsWith("http")) {
    return createClient("https://placeholder.supabase.co", "placeholder");
  }
  return createClient(supabaseUrl, supabaseAnonKey);
}

export const supabase = buildClient();

export async function fetchOpportunities(
  query?: {
    active?: boolean;
    orderBy?: string;
    ascending?: boolean;
    limit?: number;
    select?: string;
  },
): Promise<{ data: Opportunity[]; error: string | null }> {
  const { active = true, orderBy = "created_at", ascending = false, limit, select = "*" } = query ?? {};

  let q = supabase.from("opportunities").select(select);
  if (active) q = q.eq("is_active", true);
  q = q.order(orderBy, { ascending });
  if (limit) q = q.limit(limit);

  const { data, error } = await q;
  if (error) return { data: [], error: error.message };
  return { data: (data ?? []) as unknown as Opportunity[], error: null };
}
