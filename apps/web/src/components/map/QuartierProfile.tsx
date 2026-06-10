import { BarChart } from './BarChart';
import type {
  QuartierAmenities,
  QuartierPopulation,
  QuartierProfile as QuartierProfileData,
} from '@/lib/api';
import { AMENITY_LABELS, fmtPct } from '@/lib/quartier-display';

function AmenitiesSection({ amenities }: { amenities: QuartierAmenities }) {
  return (
    <div className="strata-rule mt-3 pt-3" data-testid="amenities-section">
      <p className="strata-panel-title mb-2">Amenities</p>
      <dl className="grid grid-cols-2 gap-x-4">
        {AMENITY_LABELS.map(({ key, label }) => (
          <div key={key} className="flex items-baseline justify-between py-[3px]">
            <dt className="text-2xs text-strata-cream/50">{label}</dt>
            <dd className="strata-data text-xs-11 text-strata-cream">{amenities[key]}</dd>
          </div>
        ))}
      </dl>
      {amenities.per_km2 !== null && (
        <p className="mt-1.5 text-2xs text-strata-cream/40" data-testid="amenity-density">
          <span className="strata-data text-strata-cream/60">{amenities.per_km2}</span> per km²
        </p>
      )}
    </div>
  );
}

interface QuartierProfileProps {
  profile: QuartierProfileData;
  onClose?: () => void;
  onCompare?: () => void;
}

const TREND_STYLES: Record<QuartierPopulation['trend'], { arrow: string; className: string }> = {
  growing: { arrow: '↗', className: 'text-strata-sage' },
  stable: { arrow: '→', className: 'text-strata-cream/55' },
  declining: { arrow: '↘', className: 'text-strata-terracotta' },
};

function TrendBadge({ trend }: { trend: QuartierPopulation['trend'] }) {
  const { arrow, className } = TREND_STYLES[trend];
  return (
    <span className={`text-xs-11 font-medium ${className}`}>
      <span aria-hidden className="mr-1">
        {arrow}
      </span>
      {trend}
    </span>
  );
}

function StatRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-baseline justify-between py-[3px]">
      <dt className="text-2xs text-strata-cream/50">{label}</dt>
      <dd className="strata-data text-xs-11 text-strata-cream">{children}</dd>
    </div>
  );
}

export function QuartierProfile({ profile, onClose, onCompare }: QuartierProfileProps) {
  const { quartier_name, kreis, population, age_distribution, commute_hb_min, amenities } = profile;

  return (
    <div className="strata-panel w-72 p-4">
      <div className="mb-3 flex items-start justify-between">
        <div>
          <h3 className="text-lg-15 font-semibold tracking-tight text-strata-cream">
            {quartier_name}
          </h3>
          <p className="mt-0.5 text-2xs uppercase tracking-[0.14em] text-strata-cream/40">
            Kreis {kreis}
          </p>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            data-testid="quartier-close"
            className="ml-2 -mr-1 -mt-1 rounded-md p-1 text-[15px] leading-none text-strata-cream/35 transition-colors hover:bg-strata-cream/5 hover:text-strata-cream"
            aria-label="Close"
          >
            ×
          </button>
        )}
      </div>

      {population === null ? (
        <p className="text-xs-11 italic text-strata-cream/40">No data</p>
      ) : (
        <>
          <dl className="divide-y divide-strata-cream/[0.06]">
            <StatRow label="Population">{population.total.toLocaleString()}</StatRow>
            {population.density_per_km2 !== null && (
              <StatRow label="Density / km²">
                {Math.round(population.density_per_km2).toLocaleString()}
              </StatRow>
            )}
            {population.swiss_pct !== null && (
              <StatRow label="Swiss">{fmtPct(population.swiss_pct)}</StatRow>
            )}
            {population.foreign_pct !== null && (
              <StatRow label="Foreign">{fmtPct(population.foreign_pct)}</StatRow>
            )}
            {population.growth_rate !== null && (
              <StatRow label="Growth rate">{fmtPct(population.growth_rate)}</StatRow>
            )}
            <div className="flex items-baseline justify-between py-[3px]">
              <dt className="text-2xs text-strata-cream/50">Trend</dt>
              <dd>
                <TrendBadge trend={population.trend} />
              </dd>
            </div>
            {commute_hb_min != null && (
              <div
                className="flex items-baseline justify-between py-[3px]"
                data-testid="commute-hb-row"
              >
                <dt className="text-2xs text-strata-cream/50">To Zürich HB</dt>
                <dd className="strata-data text-xs-11 text-strata-cream">{commute_hb_min} min</dd>
              </div>
            )}
          </dl>

          {amenities && <AmenitiesSection amenities={amenities} />}

          {age_distribution.length > 0 && (
            <div className="strata-rule mt-3 pt-3">
              <BarChart buckets={age_distribution} title="Age distribution" />
            </div>
          )}
        </>
      )}

      {onCompare && (
        <button
          onClick={onCompare}
          data-testid="compare-button"
          className="strata-rule mt-3 w-full pt-3 text-left text-2xs tracking-[0.04em] text-strata-amber/80 transition-colors hover:text-strata-amber"
        >
          Compare with another Quartier →
        </button>
      )}
    </div>
  );
}
