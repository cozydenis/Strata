'use client';

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
    return <p className="mt-1 text-[11px] text-strata-cream/60">{text}</p>;
  }

  return (
    <p className="mt-1 text-[11px] text-strata-cream/60">
      {expanded ? text : `${text.slice(0, MAX_LEN)}…`}
      <button
        onClick={() => setExpanded(!expanded)}
        className="ml-1 text-strata-amber/70 hover:text-strata-amber"
        data-testid="description-toggle"
      >
        {expanded ? 'less' : 'more'}
      </button>
    </p>
  );
}

function ImageGallery({ images }: { images: ListingSummary['images'] }) {
  if (images.length === 0) return null;

  const thumbs = images.slice(0, 4);
  const remaining = images.length - 4;

  return (
    <div className="mb-2 flex gap-1.5 overflow-hidden" data-testid="listing-gallery">
      {thumbs.map((img) => (
        <a
          key={img.id}
          href={mediaUrl(img.url) ?? '#'}
          target="_blank"
          rel="noopener noreferrer"
          className="block h-14 w-[72px] flex-shrink-0 overflow-hidden rounded-md"
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
        <span className="flex h-14 w-[72px] flex-shrink-0 items-center justify-center rounded-md bg-strata-slate-800 text-[11px] text-strata-muted">
          +{remaining}
        </span>
      )}
    </div>
  );
}

function PhotoPlaceholder() {
  return (
    <div
      className="h-14 w-full rounded-md bg-strata-slate-800 flex items-center justify-center mb-2"
      data-testid="photo-placeholder"
    >
      {/* Camera-off icon */}
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="20"
        height="20"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="text-strata-cream/20"
      >
        <line x1="2" y1="2" x2="22" y2="22" />
        <path d="M7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16" />
        <path d="M9.5 4h5L17 7h3a2 2 0 0 1 2 2v7.5" />
        <path d="M14.121 15.121A3 3 0 1 1 9.88 10.88" />
      </svg>
    </div>
  );
}

function FloorplanIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="12"
      height="12"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="inline-block mr-1 align-middle"
    >
      <rect x="3" y="3" width="18" height="18" rx="1" />
      <path d="M3 9h18" />
      <path d="M3 15h18" />
      <path d="M9 3v18" />
      <path d="M15 3v18" />
    </svg>
  );
}

export function ListingCards({ listings }: Props) {
  if (listings.length === 0) return null;

  return (
    <div data-testid="listing-cards">
      <p className="text-[10px] uppercase tracking-[0.15em] text-strata-cream/50 mb-2">
        Active listings
      </p>
      <ul>
        {listings.map((l) => {
          const rent = l.rent_gross ?? l.rent_net;
          const floorPlans = l.documents.filter((d) => d.doc_type === 'floorplan');
          return (
            <li
              key={l.id}
              className="rounded-md bg-strata-slate-800/50 border border-strata-cream/5 p-3 mb-2"
            >
              {l.images.length > 0 ? (
                <ImageGallery images={l.images} />
              ) : (
                <PhotoPlaceholder />
              )}

              <div className="flex items-baseline justify-between gap-2">
                {rent != null && (
                  <span
                    className="text-lg font-semibold text-strata-amber"
                    data-testid="listing-rent"
                  >
                    CHF {rent.toLocaleString('de-CH')}
                    <span
                      className="text-[11px] text-strata-muted ml-1"
                      data-testid="listing-rent-period"
                    >
                      /mt.
                    </span>
                  </span>
                )}
              </div>

              <div className="mt-0.5 flex gap-3 text-[12px] text-strata-cream/70">
                {l.rooms != null && <span>{l.rooms} rooms</span>}
                {l.area_m2 != null && <span>{l.area_m2} m²</span>}
              </div>

              {l.description && <TruncatedDescription text={l.description} />}

              <div className="mt-2 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {floorPlans.length > 0 && (
                    <a
                      href={mediaUrl(floorPlans[0].url) ?? '#'}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[11px] text-strata-cream/60 hover:text-strata-cream"
                      data-testid="floorplan-link"
                    >
                      <FloorplanIcon />
                      Floor plan
                    </a>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  {l.source_url && (
                    <a
                      href={l.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[10px] text-strata-cream/50 hover:text-strata-cream underline-offset-2 hover:underline"
                      data-testid="listing-link"
                    >
                      View on {l.source}
                    </a>
                  )}
                  <span
                    className="text-[10px] text-strata-cream/30"
                    data-testid="listing-source"
                  >
                    {l.source}
                  </span>
                </div>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
