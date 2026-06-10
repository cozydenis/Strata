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

const LAYERS: { key: string; label: string; glyph: string }[] = [
  { key: 'buildings', label: 'Buildings', glyph: '#7A9A6D' },
  { key: 'listings', label: 'Active listings', glyph: '#D4915A' },
  { key: 'quartiere', label: 'Quartiere', glyph: '#5A7D8A' },
  { key: 'noise', label: 'Noise', glyph: '#C4785B' },
];

const COMMUTE_GLYPH = '#C8C2BA';

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

function ToggleSwitch({ checked, onChange }: { checked: boolean; onChange: () => void }) {
  return (
    <div className="relative">
      <input type="checkbox" className="sr-only peer" checked={checked} onChange={onChange} />
      <div className="h-4 w-7 rounded-full bg-strata-stone-700/80 transition-colors duration-200 peer-checked:bg-strata-amber peer-focus-visible:ring-2 peer-focus-visible:ring-strata-amber/50" />
      <div className="absolute top-0.5 left-0.5 h-3 w-3 rounded-full bg-strata-cream shadow-sm transition-transform duration-200 peer-checked:translate-x-3" />
    </div>
  );
}

function LayerRow({
  label,
  glyph,
  checked,
  active,
  onChange,
  testId,
}: {
  label: string;
  glyph: string;
  checked: boolean;
  active: boolean;
  onChange: () => void;
  testId: string;
}) {
  return (
    <label
      className="group -mx-1.5 flex cursor-pointer items-center gap-2.5 rounded-md px-1.5 py-1 transition-colors hover:bg-strata-cream/[0.04]"
      data-testid={testId}
    >
      <span
        aria-hidden
        className="h-1.5 w-1.5 flex-shrink-0 rounded-full transition-opacity duration-200"
        style={{ backgroundColor: glyph, opacity: active ? 1 : 0.25 }}
      />
      <span
        className={`flex-1 text-xs-11 transition-colors ${
          active ? 'text-strata-cream' : 'text-strata-cream/55 group-hover:text-strata-cream/80'
        }`}
      >
        {label}
      </span>
      <ToggleSwitch checked={checked} onChange={onChange} />
    </label>
  );
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
    <div className="strata-panel w-56 p-3.5">
      <p className="strata-panel-title mb-2.5">Layers</p>
      <ul className="space-y-0.5">
        {LAYERS.map(({ key, label, glyph }) => {
          const visible = isVisible(key, {
            buildingsVisible,
            listingsVisible,
            quartiereVisible,
            noiseVisible,
          });
          return (
            <li key={key}>
              <LayerRow
                label={label}
                glyph={glyph}
                checked={visible}
                active={visible}
                onChange={() => onToggle(key)}
                testId={`toggle-${key}`}
              />
            </li>
          );
        })}
        <li>
          <LayerRow
            label="Commute"
            glyph={COMMUTE_GLYPH}
            checked={commuteVisible}
            active={commuteVisible}
            onChange={onCommuteToggle}
            testId="toggle-commute"
          />
        </li>
      </ul>

      {/* Destination selector — shown only when commute is enabled */}
      {commuteVisible && (
        <>
          <div className="strata-rule my-3" />
          <p className="strata-panel-title mb-2">Destination</p>
          <div className="flex flex-wrap gap-1.5" data-testid="commute-destinations">
            {(Object.keys(COMMUTE_DESTINATIONS) as CommuteDestination[]).map((key) => (
              <button
                key={key}
                data-testid={`destination-${key}`}
                onClick={() => onDestinationChange(key)}
                className={`rounded-full border px-2.5 py-1 text-2xs transition-colors duration-150 ${
                  activeDestination === key
                    ? 'border-strata-amber bg-strata-amber font-medium text-strata-slate-900'
                    : 'border-strata-cream/15 bg-transparent text-strata-cream/70 hover:border-strata-cream/40 hover:text-strata-cream'
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
          <div className="strata-rule my-3" />
          <label className="strata-panel-title mb-2 block">Metric</label>
          <div className="relative">
            <select
              data-testid="metric-select"
              value={activeMetric}
              onChange={(e) => onMetricChange(e.target.value)}
              className="w-full cursor-pointer appearance-none rounded-md border border-strata-cream/10 bg-strata-slate-800/80 px-2.5 py-1.5 pr-7 text-xs-11 text-strata-cream transition-colors hover:border-strata-cream/25 focus:border-strata-amber/60 focus:outline-none"
            >
              {METRICS.map(({ value, label }) => (
                <option key={value} value={value} className="bg-strata-slate-800 text-strata-cream">
                  {label}
                </option>
              ))}
            </select>
            <span className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 text-2xs text-strata-cream/40">
              ▾
            </span>
          </div>
        </>
      )}
    </div>
  );
}
