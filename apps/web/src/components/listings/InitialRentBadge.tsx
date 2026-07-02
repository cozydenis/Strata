'use client';

import { useEffect, useState } from 'react';
import type { InitialRentCheck } from '@/lib/api';
import { fetchInitialRentCheck } from '@/lib/api';

interface InitialRentBadgeProps {
  listingId: number;
}

function formatChfM2(value: number | null): string {
  if (value === null) return '–';
  return value.toLocaleString('de-CH', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

/**
 * Quartierüblichkeit badge (OR Art. 270). Deliberately silent unless the asking
 * rent is above the quarter's comparable level — a conservative legal framing:
 * no badge is shown for within_range, insufficient data, loading, or errors.
 */
export function InitialRentBadge({ listingId }: InitialRentBadgeProps) {
  const [check, setCheck] = useState<InitialRentCheck | null>(null);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetchInitialRentCheck(listingId)
      .then((result) => {
        if (!cancelled) setCheck(result);
      })
      .catch(() => {
        // Silence is the conservative default — render nothing.
      });
    return () => {
      cancelled = true;
    };
  }, [listingId]);

  if (check === null || (check.verdict !== 'above_market' && check.verdict !== 'clearly_above_market')) {
    return null;
  }

  const clearly = check.verdict === 'clearly_above_market';
  const tone = clearly
    ? 'border-strata-terracotta/40 bg-strata-terracotta/15 hover:bg-strata-terracotta/25'
    : 'border-strata-amber/30 bg-strata-amber/10 hover:bg-strata-amber/20';
  const textTone = clearly ? 'text-strata-terracotta' : 'text-strata-amber';

  return (
    <div className="mt-2">
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        data-testid="initial-rent-badge"
        className={`flex w-full flex-col items-start gap-0.5 rounded-md border px-2.5 py-1.5 text-left transition-colors ${tone}`}
      >
        <span className={`strata-data text-xs-11 font-medium ${textTone}`}>
          {clearly ? 'Deutlich über Quartier-Niveau' : 'Über Quartier-Niveau'}: CHF{' '}
          {formatChfM2(check.target_chf_m2)}/m² vs. Median CHF {formatChfM2(check.median_chf_m2)}
        </span>
      </button>

      {expanded && (
        <div
          data-testid="initial-rent-details"
          className="mt-1.5 rounded-md border border-strata-cream/10 bg-strata-cream/[0.04] px-2.5 py-2 text-2xs leading-relaxed text-strata-cream/70"
        >
          <p>{check.explanation}</p>
          <p className="mt-1.5 text-strata-cream/55">
            {check.or270.article} — contestable {check.or270.deadline_note} ({check.or270.deadline_days}{' '}
            Tage) via {check.or270.schlichtungsbehoerde}.
          </p>
          <p className="mt-1.5 italic text-strata-cream/40">{check.or270.disclaimer}</p>
        </div>
      )}
    </div>
  );
}
