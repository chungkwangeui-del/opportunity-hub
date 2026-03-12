import { createClient, SupabaseClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL ?? "";
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "";

function buildClient(): SupabaseClient {
  if (!supabaseUrl || !supabaseUrl.startsWith("http")) {
    // Return a dummy client during build / when env vars are missing.
    // At runtime in the browser the real env vars will be injected.
    return createClient("https://placeholder.supabase.co", "placeholder");
  }
  return createClient(supabaseUrl, supabaseAnonKey);
}

export const supabase = buildClient();
