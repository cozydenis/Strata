import { ERA_COLORS } from '@/lib/map/era-colors';

export function Legend() {
  return (
    <div className="strata-panel p-3.5 w-44">
      <p className="strata-panel-title mb-2.5">Construction era</p>
      <ul className="space-y-1.5">
        {ERA_COLORS.map((era) => (
          <li key={era.label} className="flex items-center gap-2.5">
            <span
              data-testid="era-swatch"
              className="inline-block h-2.5 w-2.5 flex-shrink-0 rounded-[2px]"
              style={{ backgroundColor: era.color }}
            />
            <span className="text-xs-11 text-strata-cream/85">{era.label}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
