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
    <div className="bg-strata-slate-800 backdrop-blur-sm border border-strata-cream/20 rounded-lg shadow-lg p-3 w-40">
      <p className="mb-2 text-2xs font-semibold uppercase tracking-widest text-strata-cream/70">
        Commute to HB
      </p>
      <ul className="space-y-1">
        {BANDS.map(({ key, label }) => (
          <li key={key} className="flex items-center gap-2" data-testid="commute-legend-item">
            <span
              data-testid="commute-legend-swatch"
              className="inline-block w-3 h-3 rounded-sm flex-shrink-0"
              style={{ backgroundColor: COMMUTE_COLORS[key] }}
            />
            <span className="text-2xs text-strata-cream">{label}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
