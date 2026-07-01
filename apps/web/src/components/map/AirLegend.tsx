import { AIR_LEVELS } from '@/lib/map/air-colors';

interface AirLegendProps {
  visible: boolean;
}

export function AirLegend({ visible }: AirLegendProps) {
  if (!visible) return null;

  return (
    <div className="strata-panel p-3.5 w-44">
      <p className="strata-panel-title mb-2.5">Air quality</p>
      <ul className="space-y-1.5">
        {AIR_LEVELS.map((level) => (
          <li key={level.level} className="flex items-center gap-2.5" data-testid="air-legend-item">
            <span
              data-testid="air-legend-swatch"
              className="inline-block h-2.5 w-2.5 flex-shrink-0 rounded-full"
              style={{ backgroundColor: level.color }}
            />
            <span className="text-xs-11 text-strata-cream/85">{level.label}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
