import type { QuartierProfile } from '@/lib/api';
import { AMENITY_LABELS, fmtPct } from '@/lib/quartier-display';

interface ComparisonPanelProps {
  left: QuartierProfile;
  right: QuartierProfile;
  onClose: () => void;
}

const TREND_ARROWS: Record<string, string> = { growing: '↗', stable: '→', declining: '↘' };

/** [value A | centered label | value B] — the comparison panel's core row. */
function CompareRow({
  label,
  left,
  right,
}: {
  label: string;
  left: React.ReactNode;
  right: React.ReactNode;
}) {
  return (
    <div className="grid grid-cols-[1fr_auto_1fr] items-baseline gap-x-3 py-[3px]">
      <span className="strata-data text-right text-xs-11 text-strata-cream">{left}</span>
      <span className="min-w-[88px] text-center text-2xs text-strata-cream/45">{label}</span>
      <span className="strata-data text-left text-xs-11 text-strata-cream">{right}</span>
    </div>
  );
}

function PairedBars({ label, leftPct, rightPct }: { label: string; leftPct: number; rightPct: number }) {
  return (
    <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-x-3 py-[2px]">
      <div className="flex items-center justify-end gap-1.5">
        <span className="strata-data text-2xs text-strata-cream/55">{Number(leftPct.toFixed(1))}%</span>
        <div className="h-[5px] w-24 overflow-hidden rounded-full bg-strata-stone-700/35">
          <div
            className="float-right h-full rounded-full bg-strata-amber/90"
            style={{ width: `${Math.min(leftPct, 100)}%` }}
          />
        </div>
      </div>
      <span className="strata-data min-w-[88px] text-center text-2xs text-strata-cream/45">{label}</span>
      <div className="flex items-center gap-1.5">
        <div className="h-[5px] w-24 overflow-hidden rounded-full bg-strata-stone-700/35">
          <div
            className="h-full rounded-full bg-strata-slate-300/80"
            style={{ width: `${Math.min(rightPct, 100)}%` }}
          />
        </div>
        <span className="strata-data text-2xs text-strata-cream/55">{Number(rightPct.toFixed(1))}%</span>
      </div>
    </div>
  );
}

function num(value: number | null | undefined, format?: (v: number) => string): React.ReactNode {
  if (value == null) return <span className="text-strata-cream/30">—</span>;
  return format ? format(value) : value;
}

export function ComparisonPanel({ left, right, onClose }: ComparisonPanelProps) {
  const lp = left.population;
  const rp = right.population;

  const ageBuckets = left.age_distribution.map((bucket) => ({
    bucket: bucket.bucket,
    leftPct: bucket.pct,
    rightPct: right.age_distribution.find((b) => b.bucket === bucket.bucket)?.pct ?? 0,
  }));

  return (
    <div className="strata-panel w-[440px] p-4" data-testid="comparison-panel">
      {/* Header: two names flanking "vs" */}
      <div className="mb-3 grid grid-cols-[1fr_auto_1fr] items-start gap-x-3">
        <div className="text-right">
          <h3 className="text-base-13 font-semibold tracking-tight text-strata-cream">
            <span aria-hidden className="mr-1.5 inline-block h-1.5 w-1.5 rounded-full bg-strata-amber align-middle" />
            {left.quartier_name}
          </h3>
          <p className="mt-0.5 text-2xs uppercase tracking-[0.14em] text-strata-cream/40">
            Kreis {left.kreis}
          </p>
        </div>
        <div className="flex flex-col items-center">
          <span className="mt-0.5 text-2xs uppercase tracking-[0.18em] text-strata-cream/30">vs</span>
          <button
            onClick={onClose}
            data-testid="comparison-close"
            className="mt-1 rounded-md p-0.5 text-[14px] leading-none text-strata-cream/35 transition-colors hover:bg-strata-cream/5 hover:text-strata-cream"
            aria-label="Close comparison"
          >
            ×
          </button>
        </div>
        <div className="text-left">
          <h3 className="text-base-13 font-semibold tracking-tight text-strata-cream">
            {right.quartier_name}
            <span aria-hidden className="ml-1.5 inline-block h-1.5 w-1.5 rounded-full bg-strata-slate-300 align-middle" />
          </h3>
          <p className="mt-0.5 text-2xs uppercase tracking-[0.14em] text-strata-cream/40">
            Kreis {right.kreis}
          </p>
        </div>
      </div>

      <div className="divide-y divide-strata-cream/[0.06]">
        <CompareRow
          label="Population"
          left={num(lp?.total, (v) => v.toLocaleString())}
          right={num(rp?.total, (v) => v.toLocaleString())}
        />
        <CompareRow
          label="Density / km²"
          left={num(lp?.density_per_km2, (v) => Math.round(v).toLocaleString())}
          right={num(rp?.density_per_km2, (v) => Math.round(v).toLocaleString())}
        />
        <CompareRow label="Foreign" left={num(lp?.foreign_pct, fmtPct)} right={num(rp?.foreign_pct, fmtPct)} />
        <CompareRow label="Growth rate" left={num(lp?.growth_rate, fmtPct)} right={num(rp?.growth_rate, fmtPct)} />
        <CompareRow
          label="Trend"
          left={lp ? `${TREND_ARROWS[lp.trend]} ${lp.trend}` : '—'}
          right={rp ? `${TREND_ARROWS[rp.trend]} ${rp.trend}` : '—'}
        />
        {(left.commute_hb_min != null || right.commute_hb_min != null) && (
          <CompareRow
            label="To Zürich HB"
            left={num(left.commute_hb_min, (v) => `${v} min`)}
            right={num(right.commute_hb_min, (v) => `${v} min`)}
          />
        )}
      </div>

      {(left.amenities || right.amenities) && (
        <div className="strata-rule mt-3 pt-3" data-testid="comparison-amenities">
          <p className="strata-panel-title mb-1.5 text-center">Amenities</p>
          <div className="divide-y divide-strata-cream/[0.06]">
            {AMENITY_LABELS.map(({ key, label }) => (
              <CompareRow
                key={key}
                label={label}
                left={num(left.amenities?.[key] as number | undefined)}
                right={num(right.amenities?.[key] as number | undefined)}
              />
            ))}
            <CompareRow
              label="Per km²"
              left={num(left.amenities?.per_km2)}
              right={num(right.amenities?.per_km2)}
            />
          </div>
        </div>
      )}

      {ageBuckets.length > 0 && (
        <div className="strata-rule mt-3 pt-3" data-testid="comparison-ages">
          <p className="strata-panel-title mb-1.5 text-center">Age distribution</p>
          {ageBuckets.map(({ bucket, leftPct, rightPct }) => (
            <PairedBars key={bucket} label={bucket} leftPct={leftPct} rightPct={rightPct} />
          ))}
        </div>
      )}

      <p className="mt-3 text-center text-2xs text-strata-cream/30">
        Click a Quartier on the map to replace the right column
      </p>
    </div>
  );
}
