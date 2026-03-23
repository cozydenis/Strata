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

  return (
    <div className="min-w-[180px] space-y-2 text-sm">
      <div data-testid="popup-address">
        {address ? (
          <>
            <p className="font-semibold text-gray-900">{address}</p>
            {locality && <p className="text-gray-500">{locality}</p>}
          </>
        ) : (
          <p className="text-gray-400">—</p>
        )}
      </div>
      <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
        <dt className="text-gray-500">Built</dt>
        <dd className="font-medium" style={{ color: era.color }}>
          {summary.gbauj ?? 'Unknown'}
        </dd>
        <dt className="text-gray-500">Floors</dt>
        <dd className="font-medium">{summary.gastw ?? '—'}</dd>
        <dt className="text-gray-500">Dwellings</dt>
        <dd className="font-medium">{summary.ganzwhg ?? '—'}</dd>
      </dl>
      {listings && listings.length > 0 && <ListingCards listings={listings} />}
    </div>
  );
}
