import { ERA_COLORS } from '@/lib/map/era-colors';

export function Legend() {
  return (
    <div className="absolute bottom-8 left-4 z-10 rounded-lg bg-white/90 px-4 py-3 shadow-md backdrop-blur-sm">
      <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
        Construction era
      </p>
      <ul className="space-y-1">
        {ERA_COLORS.map((era) => (
          <li key={era.label} className="flex items-center gap-2">
            <span
              data-testid="era-swatch"
              className="inline-block h-3 w-3 flex-shrink-0 rounded-sm"
              style={{ backgroundColor: era.color }}
            />
            <span className="text-xs text-gray-700">{era.label}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
