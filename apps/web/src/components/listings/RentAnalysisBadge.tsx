'use client';

import { useEffect, useState } from 'react';
import type { RentAnalysis } from '@/lib/api';
import { fetchRentAnalysis } from '@/lib/api';
import { HerabsetzungDialog } from './HerabsetzungDialog';

interface RentAnalysisBadgeProps {
  listingId: number;
}

function formatChf(amount: number): string {
  return Math.abs(amount).toLocaleString('de-CH', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

export function RentAnalysisBadge({ listingId }: RentAnalysisBadgeProps) {
  const [analysis, setAnalysis] = useState<RentAnalysis | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetchRentAnalysis(listingId)
      .then((result) => {
        if (!cancelled) setAnalysis(result);
      })
      .catch(() => {
        // A missing analysis is not an error worth surfacing — render nothing.
      });
    return () => {
      cancelled = true;
    };
  }, [listingId]);

  if (
    analysis === null ||
    analysis.basis === 'unknown' ||
    analysis.direction !== 'reduction' ||
    analysis.monthly_chf === null
  ) {
    return null;
  }

  const assumed = analysis.basis === 'assumed_from_first_seen';

  return (
    <>
      <button
        type="button"
        onClick={() => setDialogOpen(true)}
        data-testid="rent-analysis-badge"
        className="mt-2 flex w-full flex-col items-start gap-0.5 rounded-md border border-strata-terracotta/30 bg-strata-terracotta/10 px-2.5 py-1.5 text-left transition-colors hover:bg-strata-terracotta/20"
      >
        <span className="strata-data text-xs-11 font-medium text-strata-terracotta">
          Mietsenkung möglich: CHF {formatChf(analysis.monthly_chf)}/Mt.
        </span>
        {assumed && (
          <span className="text-2xs text-strata-terracotta/70" data-testid="rent-analysis-hint">
            geschätzt aus Inseratsdatum
          </span>
        )}
      </button>

      {dialogOpen && (
        <HerabsetzungDialog listingId={listingId} onClose={() => setDialogOpen(false)} />
      )}
    </>
  );
}
