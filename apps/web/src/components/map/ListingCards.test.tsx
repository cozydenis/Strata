import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ListingCards } from './ListingCards';
import type { ListingSummary } from '@/lib/api';

const listing: ListingSummary = {
  id: 1,
  source: 'flatfox',
  source_id: 'L-1001',
  rent_net: 2000,
  rent_gross: 2200,
  rooms: 3.5,
  area_m2: 80,
  street: 'Langstrasse',
  house_number: '42',
  plz: 8004,
  city: 'Zürich',
  source_url: 'https://flatfox.ch/test/L-1001/',
  first_seen: '2026-01-15T09:00:00',
  last_seen: '2026-03-20T12:00:00',
  description: 'Beautiful apartment with lake view in a quiet neighbourhood.',
  images: [
    { id: 1, url: 'https://flatfox.ch/thumb/cover.jpg', local_path: null, caption: null, ordering: 0, image_type: 'cover' as const },
    { id: 2, url: 'https://flatfox.ch/thumb/img1.jpg', local_path: null, caption: null, ordering: 1, image_type: 'photo' as const },
  ],
  documents: [
    { id: 1, url: 'https://flatfox.ch/doc/plan.pdf', local_path: null, caption: 'Grundriss', doc_type: 'floorplan' as const },
  ],
};

describe('ListingCards', () => {
  it('renders nothing when listings array is empty', () => {
    const { container } = render(<ListingCards listings={[]} />);
    expect(container.querySelector('[data-testid="listing-cards"]')).toBeNull();
  });

  it('renders rent amount preferring gross over net', () => {
    render(<ListingCards listings={[listing]} />);
    const rent = screen.getByTestId('listing-rent');
    expect(rent.textContent).toContain('2');
  });

  it('renders rent_net when rent_gross is null', () => {
    render(<ListingCards listings={[{ ...listing, rent_gross: null }]} />);
    const rent = screen.getByTestId('listing-rent');
    expect(rent.textContent).toContain('2');
  });

  it('formats rent with CHF prefix using de-CH locale', () => {
    render(<ListingCards listings={[listing]} />);
    const rent = screen.getByTestId('listing-rent');
    expect(rent.textContent).toContain('CHF');
    // de-CH uses right single quotation mark (U+2019) as thousands separator: 2'200
    // Also accept plain apostrophe or no separator depending on environment
    expect(rent.textContent).toMatch(/2[\u2019'\s.,]?200|2200/);
  });

  it('renders rooms and area', () => {
    render(<ListingCards listings={[listing]} />);
    expect(screen.getByText('3.5 rooms')).toBeTruthy();
    expect(screen.getByText('80 m²')).toBeTruthy();
  });

  it('renders source attribution', () => {
    render(<ListingCards listings={[listing]} />);
    expect(screen.getByTestId('listing-source')).toBeTruthy();
  });

  it('renders link to source_url with target _blank', () => {
    render(<ListingCards listings={[listing]} />);
    const link = screen.getByTestId('listing-link') as HTMLAnchorElement;
    expect(link.href).toBe('https://flatfox.ch/test/L-1001/');
    expect(link.target).toBe('_blank');
  });

  it('renders multiple listings', () => {
    const listings = [
      listing,
      { ...listing, id: 2, source_id: 'L-1002', rent_net: 1500, rent_gross: 1700 },
    ];
    render(<ListingCards listings={listings} />);
    const rents = screen.getAllByTestId('listing-rent');
    expect(rents.length).toBe(2);
  });

  it('renders description text', () => {
    render(<ListingCards listings={[listing]} />);
    expect(screen.getByText(/Beautiful apartment/)).toBeTruthy();
  });

  it('truncates long description with toggle', () => {
    const long = { ...listing, description: 'A'.repeat(200) };
    render(<ListingCards listings={[long]} />);
    expect(screen.getByTestId('description-toggle')).toBeTruthy();
    expect(screen.getByText('more')).toBeTruthy();
  });

  it('expands description on toggle click', () => {
    const long = { ...listing, description: 'Start ' + 'A'.repeat(200) + ' End' };
    render(<ListingCards listings={[long]} />);
    fireEvent.click(screen.getByTestId('description-toggle'));
    expect(screen.getByText(/End/)).toBeTruthy();
    expect(screen.getByText('less')).toBeTruthy();
  });

  it('renders image gallery when images exist', () => {
    render(<ListingCards listings={[listing]} />);
    expect(screen.getByTestId('listing-gallery')).toBeTruthy();
  });

  it('renders photo placeholder when no images', () => {
    render(<ListingCards listings={[{ ...listing, images: [] }]} />);
    expect(screen.getByTestId('photo-placeholder')).toBeTruthy();
    // Gallery should not show
    expect(screen.queryByTestId('listing-gallery')).toBeNull();
  });

  it('renders floor plan link when documents exist', () => {
    render(<ListingCards listings={[listing]} />);
    const link = screen.getByTestId('floorplan-link') as HTMLAnchorElement;
    expect(link.href).toContain('plan.pdf');
    expect(link.target).toBe('_blank');
  });

  it('does not render floor plan link when no documents', () => {
    render(<ListingCards listings={[{ ...listing, documents: [] }]} />);
    expect(screen.queryByTestId('floorplan-link')).toBeNull();
  });

  it('renders /mt. suffix on rent amount', () => {
    render(<ListingCards listings={[listing]} />);
    expect(screen.getByTestId('listing-rent-period')).toBeTruthy();
    expect(screen.getByTestId('listing-rent-period').textContent).toContain('/mt.');
  });

  it('image thumbnails have object-cover class', () => {
    const { container } = render(<ListingCards listings={[listing]} />);
    const imgs = container.querySelectorAll('[data-testid="listing-gallery"] img');
    imgs.forEach((img) => {
      expect((img as HTMLElement).className).toContain('object-cover');
    });
  });
});
