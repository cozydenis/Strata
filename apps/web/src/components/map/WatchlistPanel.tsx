'use client';

import { useCallback, useEffect, useState } from 'react';
import type { WatchEvent, WatchItem } from '@/lib/api';
import { fetchWatchEvents, fetchWatchlist, removeWatch } from '@/lib/api';
import { getAccessToken } from '@/lib/supabase';
import { relativeTime } from '@/lib/time';

interface WatchlistPanelProps {
  onClose: () => void;
}

function watchAddress(w: WatchItem): string {
  if (!w.strname) return `Building ${w.egid}`;
  const street = w.deinr ? `${w.strname} ${w.deinr}` : w.strname;
  return w.dplz4 ? `${street}, ${w.dplz4} ${w.dplzname ?? ''}`.trimEnd() : street;
}

function eventAddress(e: WatchEvent): string {
  if (!e.street) return `Building ${e.egid}`;
  return e.house_number ? `${e.street} ${e.house_number}` : e.street;
}

const EVENT_STYLES: Record<WatchEvent['type'], { label: string; dot: string }> = {
  new_listing: { label: 'New listing', dot: 'bg-strata-amber' },
  price_change: { label: 'Price change', dot: 'bg-strata-sage' },
  listing_gone: { label: 'Listing gone', dot: 'bg-strata-stone-600' },
};

function EventDetail({ event }: { event: WatchEvent }) {
  if (event.type === 'price_change' && event.old_value && event.new_value) {
    return (
      <span className="strata-data">
        CHF {Number(event.old_value).toLocaleString('de-CH')} → {Number(event.new_value).toLocaleString('de-CH')}
      </span>
    );
  }
  const parts = [
    event.rent_gross != null ? `CHF ${event.rent_gross.toLocaleString('de-CH')}` : null,
    event.rooms != null ? `${event.rooms} rooms` : null,
  ].filter(Boolean);
  return parts.length > 0 ? <span className="strata-data">{parts.join(' · ')}</span> : null;
}

function EventRow({ event }: { event: WatchEvent }) {
  const { label, dot } = EVENT_STYLES[event.type];
  const body = (
    <>
      <span aria-hidden className={`mt-[5px] h-1.5 w-1.5 flex-shrink-0 rounded-full ${dot}`} />
      <div className="min-w-0 flex-1">
        <p className="text-xs-11 text-strata-cream">
          <span className="font-medium">{label}</span>
          <span className="text-strata-cream/60"> · {eventAddress(event)}</span>
        </p>
        <p className="mt-0.5 text-2xs text-strata-cream/45">
          <EventDetail event={event} />
        </p>
      </div>
      <span className="strata-data flex-shrink-0 text-2xs text-strata-cream/35">
        {relativeTime(event.ts)}
      </span>
    </>
  );
  return (
    <li data-testid="watch-event">
      {event.source_url ? (
        <a
          href={event.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="-mx-1.5 flex items-start gap-2 rounded-md px-1.5 py-1.5 transition-colors hover:bg-strata-cream/[0.04]"
        >
          {body}
        </a>
      ) : (
        <div className="flex items-start gap-2 py-1.5">{body}</div>
      )}
    </li>
  );
}

export function WatchlistPanel({ onClose }: WatchlistPanelProps) {
  const [items, setItems] = useState<WatchItem[] | null>(null);
  const [events, setEvents] = useState<WatchEvent[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const token = await getAccessToken();
      if (!token) {
        setError('Sign in to see your watchlist.');
        return;
      }
      const [watches, activity] = await Promise.all([
        fetchWatchlist(token),
        fetchWatchEvents(token).catch(() => ({ total: 0, items: [] })),
      ]);
      setItems(watches.items);
      setEvents(activity.items);
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
        <ul className="strata-scroll max-h-[220px] divide-y divide-strata-cream/[0.06] overflow-y-auto pr-1">
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

      {/* Activity feed — events in watched buildings */}
      {!error && events.length > 0 && (
        <div className="strata-rule mt-3 pt-3" data-testid="watchlist-activity">
          <p className="strata-panel-title mb-1.5">Activity</p>
          <ul className="strata-scroll max-h-[240px] divide-y divide-strata-cream/[0.05] overflow-y-auto pr-1">
            {events.map((e) => (
              <EventRow key={`${e.type}-${e.listing_id}-${e.ts}`} event={e} />
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
