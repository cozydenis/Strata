import { BarChart } from './BarChart';

interface AgeBucket {
  bucket: string;
  pct: number;
}

interface Population {
  total: number;
  density_per_km2: number | null;
  swiss_pct: number | null;
  foreign_pct: number | null;
  growth_rate: number | null;
  trend: 'growing' | 'stable' | 'declining';
}

interface QuartierProfileData {
  quartier_id: number;
  quartier_name: string;
  kreis: number;
  population: Population | null;
  age_distribution: AgeBucket[];
}

interface QuartierProfileProps {
  profile: QuartierProfileData;
  onClose?: () => void;
}

function TrendBadge({ trend }: { trend: Population['trend'] }) {
  const colors: Record<Population['trend'], string> = {
    growing: 'text-green-400',
    stable: 'text-strata-cream/60',
    declining: 'text-red-400',
  };
  return <span className={`text-xs-11 font-medium ${colors[trend]}`}>{trend}</span>;
}

export function QuartierProfile({ profile, onClose }: QuartierProfileProps) {
  const { quartier_name, kreis, population, age_distribution } = profile;

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

          {age_distribution.length > 0 && (
            <BarChart buckets={age_distribution} title="Age distribution" />
          )}
        </>
      )}
    </div>
  );
}
