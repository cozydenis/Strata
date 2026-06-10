'use client';

import { useState } from 'react';
import { addWatch } from '@/lib/api';
import { getAccessToken, isAuthConfigured } from '@/lib/supabase';

type WatchState = 'idle' | 'busy' | 'watched' | 'signin' | 'error';

interface WatchButtonProps {
  egid: number;
  ewid?: number;
  /** Compact star-only rendering for unit rows. */
  compact?: boolean;
}

const LABELS: Record<WatchState, string> = {
  idle: '☆ Watch',
  busy: '…',
  watched: '★ Watching',
  signin: 'Sign in to watch',
  error: 'Failed — retry',
};

export function WatchButton({ egid, ewid, compact = false }: WatchButtonProps) {
  const [state, setState] = useState<WatchState>('idle');

  if (!isAuthConfigured()) return null;

  async function handleClick() {
    if (state === 'busy' || state === 'watched') return;
    setState('busy');
    const token = await getAccessToken();
    if (!token) {
      setState('signin');
      return;
    }
    try {
      await addWatch(token, egid, ewid);
      setState('watched');
    } catch {
      setState('error');
    }
  }

  if (compact) {
    return (
      <button
        onClick={handleClick}
        data-testid={`watch-unit-${ewid}`}
        aria-label="Watch this unit"
        title={LABELS[state]}
        className={`flex-shrink-0 px-1 text-[13px] leading-none transition-colors ${
          state === 'watched'
            ? 'text-strata-amber'
            : 'text-strata-cream/30 hover:text-strata-amber/80'
        }`}
      >
        {state === 'watched' ? '★' : '☆'}
      </button>
    );
  }

  return (
    <button
      onClick={handleClick}
      data-testid="watch-building"
      className={`rounded-full border px-2.5 py-1 text-2xs transition-colors ${
        state === 'watched'
          ? 'border-strata-amber/60 bg-strata-amber/10 text-strata-amber'
          : 'border-strata-cream/15 text-strata-cream/70 hover:border-strata-amber/60 hover:text-strata-amber'
      }`}
    >
      {LABELS[state]}
    </button>
  );
}
