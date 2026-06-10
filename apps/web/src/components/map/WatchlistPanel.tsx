'use client';

import { useCallback, useEffect, useState } from 'react';
import type { WatchItem } from '@/lib/api';
import { fetchWatchlist, removeWatch } from '@/lib/api';
import { getAccessToken } from '@/lib/supabase';

interface WatchlistPanelProps {
  onClose: () => void;
}

function watchAddress(w: WatchItem): string {
  if (!w.strname) return `Building ${w.egid}`;
  const street = w.deinr ? `${w.strname} ${w.deinr}` : w.strname;
  return w.dplz4 ? `${street}, ${w.dplz4} ${w.dplzname ?? ''}`.trimEnd() : street;
}

export function WatchlistPanel({ onClose }: WatchlistPanelProps) {
  const [items, setItems] = useState<WatchItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const token = await getAccessToken();
      if (!token) {
        setError('Sign in to see your watchlist.');
        return;
      }
      const data = await fetchWatchlist(token);
      setItems(data.items);
      setError(null);
    } catch {
      setError('Could not load your watchlist. Is the API running?');
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function handleRemove(watchId: number) {
    try {
      const token = await getAccessToken();
      if (!token) return;
      await removeWatch(token, watchId);
      setItems((prev) => prev?.filter((w) => w.id !== watchId) ?? null);
    } catch {
      setError('Could not remove the watch.');
    }
  }

  return (
    <div className="strata-panel w-80 p-4" data-testid="watchlist-panel">
      <div className="mb-3 flex items-start justify-between">
        <p className="strata-panel-title">Watchlist</p>
        <button
          onClick={onClose}
          data-testid="watchlist-close"
          className="-mr-1 -mt-1 rounded-md p-1 text-[15px] leading-none text-strata-cream/35 transition-colors hover:bg-strata-cream/5 hover:text-strata-cream"
          aria-label="Close watchlist"
        >
          ×
        </button>
      </div>

      {error && (
        <p className="text-xs-11 text-strata-cream/50" data-testid="watchlist-error">
          {error}
        </p>
      )}

      {!error && items === null && <p className="text-xs-11 text-strata-cream/40">Loading…</p>}

      {!error && items !== null && items.length === 0 && (
        <p className="text-xs-11 text-strata-cream/50" data-testid="watchlist-empty">
          Nothing watched yet. Click a building on the map and watch it — Strata
          will keep an eye on it for you.
        </p>
      )}

      {!error && items !== null && items.length > 0 && (
        <ul className="strata-scroll max-h-[340px] divide-y divide-strata-cream/[0.06] overflow-y-auto pr-1">
          {items.map((w) => (
            <li key={w.id} className="flex items-center justify-between gap-2 py-2" data-testid="watchlist-item">
              <div className="min-w-0">
                <p className="truncate text-xs-11 text-strata-cream">{watchAddress(w)}</p>
                <p className="mt-0.5 text-2xs text-strata-cream/40">
                  {w.ewid != null ? `Unit ${w.ewid}` : 'Whole building'}
                </p>
              </div>
              <button
                onClick={() => handleRemove(w.id)}
                data-testid={`watch-remove-${w.id}`}
                className="flex-shrink-0 rounded-md p-1 text-[13px] leading-none text-strata-cream/30 transition-colors hover:bg-strata-cream/5 hover:text-strata-terracotta"
                aria-label="Remove watch"
              >
                ×
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
