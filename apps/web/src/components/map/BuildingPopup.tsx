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
    <div className="w-[320px] p-4 animate-fadeSlideUp">
      {/* Address block */}
      <div data-testid="popup-address">
        {address ? (
          <>
            <p className="text-lg-15 font-semibold tracking-tight text-strata-cream">{address}</p>
            {locality && (
              <p className="mt-0.5 text-sm-12 text-strata-muted">{locality}</p>
            )}
          </>
        ) : (
          <p className="text-lg-15 text-strata-muted">—</p>
        )}
      </div>

      {/* Metadata row */}
      <div className="strata-rule my-3" />
      <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-sm-12 text-strata-cream/70">
        <span className="inline-flex items-center gap-1.5">
          <span
            aria-hidden
            className="inline-block h-2 w-2 rounded-[2px]"
            style={{ backgroundColor: era.color }}
          />
          {summary.gbauj != null ? (
            <span className="strata-data">{summary.gbauj}</span>
          ) : (
            <span className="text-strata-muted">Unknown</span>
          )}
        </span>
        {summary.gastw != null && (
          <>
            <span className="text-strata-cream/25">·</span>
            <span className="strata-data">{summary.gastw} fl.</span>
          </>
        )}
        {summary.ganzwhg != null && (
          <>
            <span className="text-strata-cream/25">·</span>
            <span className="strata-data">{summary.ganzwhg} dwg.</span>
          </>
        )}
      </div>

      {/* Listings section */}
      {hasListings && (
        <>
          <div className="strata-rule my-3" />
          {activeListings.length > 0 ? (
            <div className="strata-scroll max-h-[320px] overflow-y-auto pr-1">
              <ListingCards listings={activeListings} />
            </div>
          ) : (
            <p className="text-sm-12 text-strata-muted">No active listings</p>
          )}
        </>
      )}
    </div>
  );
}
