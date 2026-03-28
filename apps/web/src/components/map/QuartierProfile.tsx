import { BarChart } from './BarChart';
import type { AgeBucket, QuartierPopulation, QuartierProfile as QuartierProfileData } from '@/lib/api';

interface QuartierProfileProps {
  profile: QuartierProfileData;
  onClose?: () => void;
}

function TrendBadge({ trend }: { trend: QuartierPopulation['trend'] }) {
  const colors: Record<QuartierPopulation['trend'], string> = {
    growing: 'text-green-400',
    stable: 'text-strata-cream/60',
    declining: 'text-red-400',
  };
  return <span className={`text-xs-11 font-medium ${colors[trend]}`}>{trend}</span>;
}

export function QuartierProfile({ profile, onClose }: QuartierProfileProps) {
  const { quartier_name, kreis, population, age_distribution, commute_hb_min } = profile;

  return (
    <div className="bg-strata-slate-800 backdrop-blur-sm border border-strata-cream/20 rounded-lg shadow-lg p-4 w-64">
      <div className="flex items-start justify-between mb-1">
        <h3 className="text-base-13 font-semibold text-strata-cream">{quartier_name}</h3>
        {onClose && (
          <button
            onClick={onClose}
            data-testid="quartier-close"
            className="text-strata-cream/40 hover:text-strata-cream text-[14px] leading-none ml-2"
            aria-label="Close"
          >
            ×
          </button>
        )}
      </div>
      <p className="text-2xs text-strata-cream/70 mb-3">Kreis {kreis}</p>

      {population === null ? (
        <p className="text-xs-11 text-strata-cream/40 italic">No data</p>
      ) : (
        <>
          <dl className="space-y-1 mb-3">
            <div className="flex justify-between">
              <dt className="text-2xs text-strata-cream/70">Population</dt>
              <dd className="text-xs-11 text-strata-cream">
                {population.total.toLocaleString()}
              </dd>
            </div>
            {population.density_per_km2 !== null && (
              <div className="flex justify-between">
                <dt className="text-2xs text-strata-cream/70">Density / km²</dt>
                <dd className="text-xs-11 text-strata-cream">
                  {population.density_per_km2.toLocaleString()}
                </dd>
              </div>
            )}
            {population.swiss_pct !== null && (
              <div className="flex justify-between">
                <dt className="text-2xs text-strata-cream/70">Swiss</dt>
                <dd className="text-xs-11 text-strata-cream">{population.swiss_pct}%</dd>
              </div>
            )}
            {population.foreign_pct !== null && (
              <div className="flex justify-between">
                <dt className="text-2xs text-strata-cream/70">Foreign</dt>
                <dd className="text-xs-11 text-strata-cream">{population.foreign_pct}%</dd>
              </div>
            )}
            {population.growth_rate !== null && (
              <div className="flex justify-between">
                <dt className="text-2xs text-strata-cream/70">Growth rate</dt>
                <dd className="text-xs-11 text-strata-cream">{population.growth_rate}%</dd>
              </div>
            )}
            <div className="flex justify-between items-center">
              <dt className="text-2xs text-strata-cream/70">Trend</dt>
              <dd>
                <TrendBadge trend={population.trend} />
              </dd>
            </div>
          </dl>

          {commute_hb_min != null && (
            <div
              className="flex justify-between mt-2 pt-2 border-t border-strata-cream/10"
              data-testid="commute-hb-row"
            >
              <dt className="text-2xs text-strata-cream/70">To Zürich HB</dt>
              <dd className="text-xs-11 text-strata-cream">{commute_hb_min} min</dd>
            </div>
          )}

          {age_distribution.length > 0 && (
            <BarChart buckets={age_distribution} title="Age distribution" />
          )}
        </>
      )}
    </div>
  );
}
