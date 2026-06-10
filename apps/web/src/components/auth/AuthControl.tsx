'use client';

import { useEffect, useState } from 'react';
import type { Session } from '@supabase/supabase-js';
import { getSupabase, isAuthConfigured } from '@/lib/supabase';

interface AuthControlProps {
  onToggleWatchlist: () => void;
}

/** Session state synced with Supabase Auth. Null client → permanently signed out. */
export function useSession(): Session | null {
  const [session, setSession] = useState<Session | null>(null);

  useEffect(() => {
    const supabase = getSupabase();
    if (!supabase) return;
    supabase.auth.getSession().then(({ data }) => setSession(data.session));
    const { data: sub } = supabase.auth.onAuthStateChange((_event, next) => setSession(next));
    return () => sub.subscription.unsubscribe();
  }, []);

  return session;
}

function SignInForm({ onDone }: { onDone: () => void }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(mode: 'signin' | 'signup') {
    const supabase = getSupabase();
    if (!supabase) return;
    setBusy(true);
    setError(null);
    const { error: err } =
      mode === 'signin'
        ? await supabase.auth.signInWithPassword({ email, password })
        : await supabase.auth.signUp({ email, password });
    setBusy(false);
    if (err) {
      setError(err.message);
      return;
    }
    onDone();
  }

  const inputClass =
    'w-full rounded-md border border-strata-cream/10 bg-strata-slate-800/80 px-2.5 py-1.5 text-xs-11 ' +
    'text-strata-cream placeholder:text-strata-cream/30 focus:border-strata-amber/60 focus:outline-none';

  return (
    <div className="w-60" data-testid="signin-form">
      <p className="strata-panel-title mb-2.5">Sign in</p>
      <div className="space-y-2">
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="email"
          className={inputClass}
          data-testid="auth-email"
        />
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="password"
          className={inputClass}
          data-testid="auth-password"
        />
      </div>
      {error && (
        <p className="mt-2 text-2xs text-strata-terracotta" data-testid="auth-error">
          {error}
        </p>
      )}
      <div className="mt-3 flex items-center gap-2">
        <button
          onClick={() => submit('signin')}
          disabled={busy}
          data-testid="auth-submit"
          className="rounded-full bg-strata-amber px-3 py-1 text-2xs font-medium text-strata-slate-900 transition-opacity hover:opacity-90 disabled:opacity-50"
        >
          Sign in
        </button>
        <button
          onClick={() => submit('signup')}
          disabled={busy}
          data-testid="auth-signup"
          className="rounded-full border border-strata-cream/15 px-3 py-1 text-2xs text-strata-cream/70 transition-colors hover:border-strata-cream/40 hover:text-strata-cream disabled:opacity-50"
        >
          Create account
        </button>
      </div>
    </div>
  );
}

export function AuthControl({ onToggleWatchlist }: AuthControlProps) {
  const session = useSession();
  const [open, setOpen] = useState(false);

  if (!isAuthConfigured()) return null;

  if (!session) {
    return (
      <div className="absolute top-4 right-14 z-20" data-testid="auth-control">
        {open ? (
          <div className="strata-panel p-3.5">
            <SignInForm onDone={() => setOpen(false)} />
            <button
              onClick={() => setOpen(false)}
              className="mt-2 text-2xs text-strata-cream/40 transition-colors hover:text-strata-cream"
            >
              Cancel
            </button>
          </div>
        ) : (
          <button
            onClick={() => setOpen(true)}
            data-testid="auth-signin-button"
            className="strata-panel px-3.5 py-2 text-xs-11 text-strata-cream/80 transition-colors hover:text-strata-cream"
          >
            Sign in
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="absolute top-4 right-14 z-20" data-testid="auth-control">
      <div className="strata-panel flex items-center gap-3 px-3.5 py-2">
        <span className="max-w-[140px] truncate text-xs-11 text-strata-cream/60" data-testid="auth-email-chip">
          {session.user.email}
        </span>
        <button
          onClick={onToggleWatchlist}
          data-testid="watchlist-toggle"
          className="text-xs-11 text-strata-amber/80 transition-colors hover:text-strata-amber"
        >
          Watchlist
        </button>
        <button
          onClick={() => getSupabase()?.auth.signOut()}
          data-testid="auth-signout"
          className="text-2xs text-strata-cream/40 transition-colors hover:text-strata-cream"
        >
          Sign out
        </button>
      </div>
    </div>
  );
}
