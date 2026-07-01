import { BarChart } from './BarChart';
import type {
  QuartierAmenities,
  QuartierConstruction,
  QuartierPopulation,
  QuartierProfile as QuartierProfileData,
  QuartierVibe,
} from '@/lib/api';

function ConstructionSection({ construction }: { construction: QuartierConstruction }) {
  if (construction.approved_projects === 0 && construction.started_projects === 0) return null;
  return (
    <div className="strata-rule mt-3 pt-3" data-testid="construction-section">
      <p className="strata-panel-title mb-1.5">New construction · {construction.year}</p>
      <dl className="divide-y divide-strata-cream/[0.06]">
        <div className="flex items-baseline justify-between py-[3px]">
          <dt className="text-2xs text-strata-cream/50">Approved</dt>
          <dd className="strata-data text-xs-11 text-strata-cream">{construction.approved_projects}</dd>
        </div>
        <div className="flex items-baseline justify-between py-[3px]">
          <dt className="text-2xs text-strata-cream/50">Under construction</dt>
          <dd className="strata-data text-xs-11 text-strata-cream">{construction.started_projects}</dd>
        </div>
        {construction.cost_mchf !== null && (
          <div className="flex items-baseline justify-between py-[3px]">
            <dt className="text-2xs text-strata-cream/50">Investment</dt>
            <dd className="strata-data text-xs-11 text-strata-cream">
              CHF {construction.cost_mchf.toLocaleString('de-CH')} M
            </dd>
          </div>
        )}
      </dl>
    </div>
  );
}
import { AMENITY_LABELS, fmtPct } from '@/lib/quartier-display';

function VibeSection({ vibe }: { vibe: QuartierVibe }) {
  return (
    <div className="mb-3" data-testid="vibe-section">
      <div className="flex flex-wrap gap-1.5">
        {vibe.tags.map(({ tag, evidence }) => (
          <span
            key={tag}
            title={evidence}
            data-testid="vibe-tag"
            className="cursor-help rounded-full border border-strata-cream/12 px-2 py-0.5 text-2xs text-strata-cream/75"
          >
            {tag}
          </span>
        ))}
      </div>
      <p className="mt-1.5 text-2xs leading-relaxed text-strata-cream/45" data-testid="vibe-summary">
        {vibe.summary}
      </p>
    </div>
  );
}

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

export interface QuartierMatch {
  score: number | null;
  strong: string[];
  weak: string[];
}

interface QuartierProfileProps {
  profile: QuartierProfileData;
  onClose?: () => void;
  onCompare?: () => void;
  match?: QuartierMatch | null;
}

function MatchSection({ match }: { match: QuartierMatch }) {
  return (
    <div className="strata-rule mt-3 pt-3" data-testid="match-score">
      <div className="flex items-baseline justify-between">
        <p className="strata-panel-title">Your match</p>
        <span className="strata-data text-lg-15 font-semibold text-strata-amber">{match.score}%</span>
      </div>
      {(match.strong.length > 0 || match.weak.length > 0) && (
        <div className="mt-1.5 flex flex-wrap gap-1.5">
          {match.strong.map((label) => (
            <span
              key={`strong-${label}`}
              className="rounded-full border border-strata-sage/30 px-2 py-0.5 text-2xs text-strata-sage"
            >
              strong on {label}
            </span>
          ))}
          {match.weak.map((label) => (
            <span
              key={`weak-${label}`}
              className="rounded-full border border-strata-cream/12 px-2 py-0.5 text-2xs text-strata-cream/45"
            >
              weak on {label}
            </span>
          ))}
        </div>
      )}
    </div>
  );
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

export function QuartierProfile({ profile, onClose, onCompare, match }: QuartierProfileProps) {
  const {
    quartier_name,
    kreis,
    population,
    age_distribution,
    commute_hb_min,
    amenities,
    vibe,
    construction,
  } = profile;

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

      {vibe && <VibeSection vibe={vibe} />}

      {match && match.score !== null && <MatchSection match={match} />}

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

          {construction && <ConstructionSection construction={construction} />}

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
