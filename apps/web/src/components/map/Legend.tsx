import { ERA_COLORS } from '@/lib/map/era-colors';

interface Props {
  listingsVisible?: boolean;
  onToggleListings?: () => void;
}

export function Legend({ listingsVisible, onToggleListings }: Props = {}) {
  return (
    <div className="absolute bottom-8 left-4 z-10 animate-fadeSlideUp">
      <div className="bg-strata-slate-900/85 backdrop-blur-md border border-strata-cream/10 rounded-lg shadow-md p-3">
        <p className="mb-2 text-[10px] font-semibold uppercase tracking-widest text-strata-cream/50">
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
              <span className="text-[11px] text-strata-cream/80">{era.label}</span>
            </li>
          ))}
        </ul>
        {onToggleListings && (
          <>
            <div className="border-t border-strata-cream/10 my-2" />
            <label
              className="flex cursor-pointer items-center gap-2"
              data-testid="listings-toggle"
            >
              <div className="relative">
                <input
                  type="checkbox"
                  className="sr-only peer"
                  checked={listingsVisible ?? true}
                  onChange={onToggleListings}
                />
                <div className="w-7 h-4 rounded-full bg-strata-stone-700 peer-checked:bg-strata-amber transition-colors" />
                <div className="absolute top-0.5 left-0.5 w-3 h-3 rounded-full bg-strata-cream transition-transform peer-checked:translate-x-3" />
              </div>
              <span className="text-[11px] text-strata-cream/80">Active listings</span>
            </label>
          </>
        )}
      </div>
    </div>
  );
}
