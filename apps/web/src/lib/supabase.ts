import { createClient, type SupabaseClient } from '@supabase/supabase-js';

const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

let client: SupabaseClient | null = null;

/** True when real Supabase credentials are present (not the .env.example placeholders). */
export function isAuthConfigured(): boolean {
  return Boolean(url && anonKey && !url.includes('your-project') && !anonKey.startsWith('your-'));
}

/** Lazily-created Supabase client, or null when auth is not configured. */
export function getSupabase(): SupabaseClient | null {
  if (!isAuthConfigured()) return null;
  if (!client) client = createClient(url!, anonKey!);
  return client;
}

/** Current session's access token (JWT) for API calls, or null when signed out. */
export async function getAccessToken(): Promise<string | null> {
  const supabase = getSupabase();
  if (!supabase) return null;
  const { data } = await supabase.auth.getSession();
  return data.session?.access_token ?? null;
}
