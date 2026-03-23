import { useState } from 'react';
import type { ListingSummary } from '@/lib/api';
import { mediaUrl } from '@/lib/api';

interface Props {
  listings: ListingSummary[];
}

function TruncatedDescription({ text }: { text: string }) {
  const [expanded, setExpanded] = useState(false);
  const MAX_LEN = 120;

  if (text.length <= MAX_LEN) {
    return <p className="mt-1 text-xs text-gray-600">{text}</p>;
  }

  return (
    <p className="mt-1 text-xs text-gray-600">
      {expanded ? text : `${text.slice(0, MAX_LEN)}…`}
      <button
        onClick={() => setExpanded(!expanded)}
        className="ml-1 text-blue-600 hover:underline"
        data-testid="description-toggle"
      >
        {expanded ? 'less' : 'more'}
      </button>
    </p>
  );
}

function ImageGallery({ images }: { images: ListingSummary['images'] }) {
  if (images.length === 0) return null;

  // Show up to 4 thumbnails
  const thumbs = images.slice(0, 4);
  const remaining = images.length - 4;

  return (
    <div className="mb-1.5 flex gap-1 overflow-hidden" data-testid="listing-gallery">
      {thumbs.map((img) => (
        <a
          key={img.id}
          href={mediaUrl(img.url) ?? '#'}
          target="_blank"
          rel="noopener noreferrer"
          className="block h-[48px] w-[64px] flex-shrink-0 overflow-hidden rounded"
        >
          <img
            src={mediaUrl(img.url) ?? ''}
            alt={img.caption ?? 'Listing photo'}
            className="h-full w-full object-cover"
            loading="lazy"
          />
        </a>
      ))}
      {remaining > 0 && (
        <span className="flex h-[48px] w-[64px] flex-shrink-0 items-center justify-center rounded bg-gray-200 text-xs text-gray-500">
          +{remaining}
        </span>
      )}
    </div>
  );
}

export function ListingCards({ listings }: Props) {
  if (listings.length === 0) return null;

  return (
    <div className="mt-2 border-t border-gray-200 pt-2" data-testid="listing-cards">
      <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-gray-500">
        Active listings
      </p>
      <ul className="space-y-2">
        {listings.map((l) => {
          const rent = l.rent_gross ?? l.rent_net;
          const floorPlans = l.documents.filter((d) => d.doc_type === 'floorplan');
          return (
            <li key={l.id} className="rounded border border-gray-100 bg-gray-50 p-2">
              <ImageGallery images={l.images} />
              <div className="flex items-baseline justify-between gap-2">
                {rent != null && (
                  <span className="text-sm font-semibold text-gray-900" data-testid="listing-rent">
                    CHF {rent.toLocaleString('de-CH')}/mo
                  </span>
                )}
                <span className="rounded bg-blue-100 px-1.5 py-0.5 text-[10px] font-medium text-blue-700" data-testid="listing-source">
                  {l.source}
                </span>
              </div>
              <div className="mt-0.5 flex gap-3 text-xs text-gray-500">
                {l.rooms != null && <span>{l.rooms} rooms</span>}
                {l.area_m2 != null && <span>{l.area_m2} m²</span>}
              </div>
              {l.description && <TruncatedDescription text={l.description} />}
              <div className="mt-1 flex items-center gap-3">
                {l.source_url && (
                  <a
                    href={l.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-blue-600 hover:underline"
                    data-testid="listing-link"
                  >
                    View on {l.source}
                  </a>
                )}
                {floorPlans.length > 0 && (
                  <a
                    href={mediaUrl(floorPlans[0].url) ?? '#'}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-green-700 hover:underline"
                    data-testid="floorplan-link"
                  >
                    Floor plan
                  </a>
                )}
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
