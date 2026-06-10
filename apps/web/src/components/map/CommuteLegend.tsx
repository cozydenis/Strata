import { COMMUTE_COLORS } from '@/lib/map/commute-colors';

interface CommuteLegendProps {
  visible: boolean;
}

const BANDS: { key: string; label: string }[] = [
  { key: '0-10', label: '0-10 min' },
  { key: '10-20', label: '10-20 min' },
  { key: '20-30', label: '20-30 min' },
  { key: '30-45', label: '30-45 min' },
  { key: '45+', label: '45+ min' },
];

export function CommuteLegend({ visible }: CommuteLegendProps) {
  if (!visible) return null;

  return (
    <div className="strata-panel p-3.5 w-44">
      <p className="strata-panel-title mb-2.5">Commute to HB</p>
      <ul className="space-y-1.5">
        {BANDS.map(({ key, label }) => (
          <li key={key} className="flex items-center gap-2.5" data-testid="commute-legend-item">
            <span
              data-testid="commute-legend-swatch"
              className="inline-block h-2.5 w-2.5 flex-shrink-0 rounded-[2px]"
              style={{ backgroundColor: COMMUTE_COLORS[key] }}
            />
            <span className="strata-data text-2xs text-strata-cream/85">{label}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
