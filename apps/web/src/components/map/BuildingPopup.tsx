'use client';

import { useState } from 'react';
import type { BuildingSummary, ListingSummary, UnitSummary } from '@/lib/api';
import { eraForYear } from '@/lib/map/era-colors';
import { ListingCards } from './ListingCards';
import { WatchButton } from './WatchButton';

interface Props {
  summary: BuildingSummary;
  listings?: ListingSummary[];
  units?: { total: number; items: UnitSummary[] } | null;
}

const UNITS_PREVIEW_COUNT = 5;

function UnitRow({ unit }: { unit: UnitSummary }) {
  const parts = [
    unit.wstwklang ?? undefined,
    unit.wazim != null ? `${unit.wazim} rooms` : undefined,
    unit.warea != null ? `${unit.warea} m²` : undefined,
  ].filter(Boolean);
  return (
    <li className="flex items-center justify-between gap-2 py-[3px]" data-testid="unit-row">
      <span className="strata-data truncate text-xs-11 text-strata-cream/75">
        {parts.length > 0 ? parts.join(' · ') : `Unit ${unit.ewid}`}
      </span>
      <WatchButton egid={unit.egid} ewid={unit.ewid} compact />
    </li>
  );
}

function UnitsSection({ units }: { units: { total: number; items: UnitSummary[] } }) {
  const [expanded, setExpanded] = useState(false);
  if (units.items.length === 0) return null;

  const visible = expanded ? units.items : units.items.slice(0, UNITS_PREVIEW_COUNT);
  const hidden = units.items.length - UNITS_PREVIEW_COUNT;

  return (
    <div data-testid="units-section">
      <p className="strata-panel-title mb-1.5">Units ({units.total})</p>
      <ul className="divide-y divide-strata-cream/[0.05]">
        {visible.map((u) => (
          <UnitRow key={u.ewid} unit={u} />
        ))}
      </ul>
      {hidden > 0 && (
        <button
          onClick={() => setExpanded(!expanded)}
          data-testid="units-toggle"
          className="mt-1 text-2xs text-strata-cream/40 transition-colors hover:text-strata-cream"
        >
          {expanded ? 'Show fewer' : `Show all ${units.items.length}`}
        </button>
      )}
    </div>
  );
}

export function BuildingPopup({ summary, listings, units }: Props) {
  const era = eraForYear(summary.gbauj ?? undefined);

  const address =
    summary.strname && summary.deinr
      ? `${summary.strname} ${summary.deinr}`
      : null;

  const locality =
    summary.dplz4 && summary.dplzname
      ? `${summary.dplz4} ${summary.dplzname}`
      : null;

  const hasListings = listings !== undefined;
  const activeListings = listings ?? [];

  return (
    <div className="w-[320px] p-4 animate-fadeSlideUp">
      {/* Address block */}
      <div className="flex items-start justify-between gap-2">
        <div data-testid="popup-address">
          {address ? (
            <>
              <p className="text-lg-15 font-semibold tracking-tight text-strata-cream">{address}</p>
              {locality && (
                <p className="mt-0.5 text-sm-12 text-strata-muted">{locality}</p>
              )}
            </>
          ) : (
            <p className="text-lg-15 text-strata-muted">—</p>
          )}
        </div>
        <WatchButton egid={summary.egid} />
      </div>

      {/* Metadata row */}
      <div className="strata-rule my-3" />
      <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-sm-12 text-strata-cream/70">
        <span className="inline-flex items-center gap-1.5">
          <span
            aria-hidden
            className="inline-block h-2 w-2 rounded-[2px]"
            style={{ backgroundColor: era.color }}
          />
          {summary.gbauj != null ? (
            <span className="strata-data">{summary.gbauj}</span>
          ) : (
            <span className="text-strata-muted">Unknown</span>
          )}
        </span>
        {summary.gastw != null && (
          <>
            <span className="text-strata-cream/25">·</span>
            <span className="strata-data">{summary.gastw} fl.</span>
          </>
        )}
        {summary.ganzwhg != null && (
          <>
            <span className="text-strata-cream/25">·</span>
            <span className="strata-data">{summary.ganzwhg} dwg.</span>
          </>
        )}
      </div>

      {/* Units section — the registry made visible */}
      {units && units.items.length > 0 && (
        <>
          <div className="strata-rule my-3" />
          <UnitsSection units={units} />
        </>
      )}

      {/* Listings section */}
      {hasListings && (
        <>
          <div className="strata-rule my-3" />
          {activeListings.length > 0 ? (
            <div className="strata-scroll max-h-[320px] overflow-y-auto pr-1">
              <ListingCards listings={activeListings} />
            </div>
          ) : (
            <p className="text-sm-12 text-strata-muted">No active listings</p>
          )}
        </>
      )}
    </div>
  );
}
