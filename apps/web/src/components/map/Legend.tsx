import { ERA_COLORS } from '@/lib/map/era-colors';

export function Legend() {
  return (
    <div className="bg-strata-slate-800 border border-strata-cream/20 rounded-lg shadow-lg p-3">
      <p className="mb-2 text-2xs font-semibold uppercase tracking-widest text-strata-cream/70">
        Construction era
      </p>
      <ul className="space-y-1.5">
        {ERA_COLORS.map((era) => (
          <li key={era.label} className="flex items-center gap-2">
            <span
              data-testid="era-swatch"
              className="inline-block w-2.5 h-2.5 flex-shrink-0 rounded-full"
              style={{ backgroundColor: era.color }}
            />
            <span className="text-xs-11 text-strata-cream">{era.label}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
