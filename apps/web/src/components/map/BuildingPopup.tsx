import type { BuildingSummary, ListingSummary } from '@/lib/api';
import { eraForYear } from '@/lib/map/era-colors';
import { ListingCards } from './ListingCards';

interface Props {
  summary: BuildingSummary;
  listings?: ListingSummary[];
}

export function BuildingPopup({ summary, listings }: Props) {
  const era = eraForYear(summary.gbauj ?? undefined);

  const address =
    summary.strname && summary.deinr
      ? `${summary.strname} ${summary.deinr}`
      : null;

  const locality =
    summary.dplz4 && summary.dplzname
      ? `${summary.dplz4} ${summary.dplzname}`
      : null;

  const hasListings = listings !== undefined;
  const activeListings = listings ?? [];

  return (
    <div className="min-w-[260px] max-w-[320px] p-4 animate-fadeSlideUp">
      {/* Address block */}
      <div data-testid="popup-address">
        {address ? (
          <>
            <p className="text-[15px] font-semibold text-strata-cream">{address}</p>
            {locality && (
              <p className="text-[12px] text-strata-muted mt-0.5">{locality}</p>
            )}
          </>
        ) : (
          <p className="text-[15px] text-strata-muted">—</p>
        )}
      </div>

      {/* Metadata row */}
      <div className="border-t border-strata-cream/10 my-3" />
      <div className="flex items-center gap-2 text-[12px] text-strata-cream/70 flex-wrap">
        {summary.gbauj != null ? (
          <span style={{ color: era.color }}>{summary.gbauj}</span>
        ) : (
          <span className="text-strata-muted">Unknown</span>
        )}
        {summary.gastw != null && (
          <>
            <span className="text-strata-cream/30">·</span>
            <span>{summary.gastw} fl.</span>
          </>
        )}
        {summary.ganzwhg != null && (
          <>
            <span className="text-strata-cream/30">·</span>
            <span>{summary.ganzwhg} dwg.</span>
          </>
        )}
      </div>

      {/* Listings section */}
      {hasListings && (
        <>
          <div className="border-t border-strata-cream/10 my-3" />
          {activeListings.length > 0 ? (
            <ListingCards listings={activeListings} />
          ) : (
            <p className="text-[12px] text-strata-muted">No active listings</p>
          )}
        </>
      )}
    </div>
  );
}
