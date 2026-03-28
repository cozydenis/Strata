import type { CommuteDestination } from '@/lib/api';
import { COMMUTE_DESTINATIONS } from '@/lib/api';

interface LayerPanelProps {
  buildingsVisible: boolean;
  listingsVisible: boolean;
  quartiereVisible: boolean;
  noiseVisible: boolean;
  activeMetric: string;
  onToggle: (layer: string) => void;
  onMetricChange: (metric: string) => void;
  // Commute props
  commuteVisible: boolean;
  activeDestination: CommuteDestination;
  onCommuteToggle: () => void;
  onDestinationChange: (dest: CommuteDestination) => void;
}

const LAYERS: { key: string; label: string }[] = [
  { key: 'buildings', label: 'Buildings' },
  { key: 'listings', label: 'Active listings' },
  { key: 'quartiere', label: 'Quartiere' },
  { key: 'noise', label: 'Noise' },
];

const METRICS: { value: string; label: string }[] = [
  { value: 'population_density', label: 'Population density' },
  { value: 'foreign_pct', label: 'Foreign residents %' },
  { value: 'age_avg', label: 'Average age' },
  { value: 'growth_rate', label: 'Growth rate' },
];

function isVisible(
  key: string,
  props: Pick<
    LayerPanelProps,
    'buildingsVisible' | 'listingsVisible' | 'quartiereVisible' | 'noiseVisible'
  >,
): boolean {
  switch (key) {
    case 'buildings':
      return props.buildingsVisible;
    case 'listings':
      return props.listingsVisible;
    case 'quartiere':
      return props.quartiereVisible;
    case 'noise':
      return props.noiseVisible;
    default:
      return false;
  }
}

export function LayerPanel({
  buildingsVisible,
  listingsVisible,
  quartiereVisible,
  noiseVisible,
  activeMetric,
  onToggle,
  onMetricChange,
  commuteVisible,
  activeDestination,
  onCommuteToggle,
  onDestinationChange,
}: LayerPanelProps) {
  return (
    <div className="bg-strata-slate-800 backdrop-blur-sm border border-strata-cream/20 rounded-lg shadow-lg p-3 w-52">
      <p className="mb-2 text-2xs font-semibold uppercase tracking-widest text-strata-cream/70">
        Layers
      </p>
      <ul className="space-y-2">
        {LAYERS.map(({ key, label }) => (
          <li key={key}>
            <label
              className="flex cursor-pointer items-center gap-2"
              data-testid={`toggle-${key}`}
            >
              <div className="relative">
                <input
                  type="checkbox"
                  className="sr-only peer"
                  checked={isVisible(key, {
                    buildingsVisible,
                    listingsVisible,
                    quartiereVisible,
                    noiseVisible,
                  })}
                  onChange={() => onToggle(key)}
                />
                <div className="w-7 h-4 rounded-full bg-strata-stone-700 peer-checked:bg-strata-amber transition-colors" />
                <div className="absolute top-0.5 left-0.5 w-3 h-3 rounded-full bg-strata-cream transition-transform peer-checked:translate-x-3" />
              </div>
              <span className="text-xs-11 text-strata-cream">{label}</span>
            </label>
          </li>
        ))}

        {/* Commute isochrones toggle */}
        <li>
          <label
            className="flex cursor-pointer items-center gap-2"
            data-testid="toggle-commute"
          >
            <div className="relative">
              <input
                type="checkbox"
                className="sr-only peer"
                checked={commuteVisible}
                onChange={onCommuteToggle}
              />
              <div className="w-7 h-4 rounded-full bg-strata-stone-700 peer-checked:bg-strata-amber transition-colors" />
              <div className="absolute top-0.5 left-0.5 w-3 h-3 rounded-full bg-strata-cream transition-transform peer-checked:translate-x-3" />
            </div>
            <span className="text-xs-11 text-strata-cream">Commute</span>
          </label>
        </li>
      </ul>

      {/* Destination selector — shown only when commute is enabled */}
      {commuteVisible && (
        <>
          <div className="border-t border-strata-cream/20 my-2" />
          <p className="text-2xs font-semibold uppercase tracking-widest text-strata-cream/70 mb-1">
            Destination
          </p>
          <div className="flex flex-wrap gap-1" data-testid="commute-destinations">
            {(Object.keys(COMMUTE_DESTINATIONS) as CommuteDestination[]).map((key) => (
              <button
                key={key}
                data-testid={`destination-${key}`}
                onClick={() => onDestinationChange(key)}
                className={`text-2xs px-2 py-1 rounded border transition-colors ${
                  activeDestination === key
                    ? 'bg-strata-amber text-strata-slate-900 border-strata-amber font-semibold'
                    : 'bg-transparent text-strata-cream border-strata-cream/30 hover:border-strata-cream/60'
                }`}
              >
                {COMMUTE_DESTINATIONS[key]}
              </button>
            ))}
          </div>
        </>
      )}

      {quartiereVisible && (
        <>
          <div className="border-t border-strata-cream/20 my-2" />
          <label className="block text-2xs font-semibold uppercase tracking-widest text-strata-cream/70 mb-1">
            Metric
          </label>
          <div className="relative">
            <select
              data-testid="metric-select"
              value={activeMetric}
              onChange={(e) => onMetricChange(e.target.value)}
              className="w-full appearance-none bg-strata-slate-700 border border-strata-cream/20 rounded text-xs-11 text-strata-cream px-2 py-1 pr-6 cursor-pointer"
            >
              {METRICS.map(({ value, label }) => (
                <option key={value} value={value} className="bg-strata-slate-700 text-strata-cream">
                  {label}
                </option>
              ))}
            </select>
            <span className="pointer-events-none absolute right-1.5 top-1/2 -translate-y-1/2 text-strata-cream/60 text-2xs">
              ▾
            </span>
          </div>
        </>
      )}
    </div>
  );
}
