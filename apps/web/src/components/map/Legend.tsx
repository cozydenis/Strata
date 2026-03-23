import { ERA_COLORS } from '@/lib/map/era-colors';

const LISTING_COLOR = '#E53935';

interface Props {
  listingsVisible?: boolean;
  onToggleListings?: () => void;
}

export function Legend({ listingsVisible, onToggleListings }: Props = {}) {
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
      {onToggleListings && (
        <div className="mt-3 border-t border-gray-200 pt-2">
          <label className="flex cursor-pointer items-center gap-2" data-testid="listings-toggle">
            <input
              type="checkbox"
              checked={listingsVisible ?? true}
              onChange={onToggleListings}
              className="h-3 w-3 rounded border-gray-300 text-red-600 focus:ring-red-500"
            />
            <span
              className="inline-block h-3 w-3 flex-shrink-0 rounded-full"
              style={{ backgroundColor: LISTING_COLOR }}
              data-testid="listings-swatch"
            />
            <span className="text-xs text-gray-700">Active listings</span>
          </label>
        </div>
      )}
    </div>
  );
}
