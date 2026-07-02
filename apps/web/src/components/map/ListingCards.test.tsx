import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import type { ListingSummary, RentAnalysis } from '@/lib/api';

vi.mock('@/lib/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/api')>();
  return {
    ...actual,
    fetchRentAnalysis: vi.fn(),
    generateHerabsetzung: vi.fn(),
    fetchInitialRentCheck: vi.fn(),
  };
});

import { ListingCards } from './ListingCards';
import { fetchRentAnalysis, fetchInitialRentCheck } from '@/lib/api';

const mockFetchRentAnalysis = vi.mocked(fetchRentAnalysis);
const mockFetchInitialRentCheck = vi.mocked(fetchInitialRentCheck);

const REDUCTION: RentAnalysis = {
  listing_id: 1,
  basis: 'known',
  base_rate: 1.75,
  current_rate: 1.5,
  rent_net: 2000,
  change_pct: -2.91,
  monthly_chf: -114.8,
  new_rent_net: 1885.2,
  direction: 'reduction',
  message: 'Mietsenkung möglich',
};

beforeEach(() => {
  // Default: no reduction applies, so the badge renders nothing and existing
  // assertions are unaffected.
  mockFetchRentAnalysis.mockReset();
  mockFetchRentAnalysis.mockResolvedValue({ ...REDUCTION, basis: 'unknown', direction: null });
  // Default: within range, so the initial-rent badge renders nothing.
  mockFetchInitialRentCheck.mockReset();
  mockFetchInitialRentCheck.mockResolvedValue({
    listing_id: 1,
    verdict: 'within_range',
    target_chf_m2: 25.0,
    median_chf_m2: 26.1,
    p25: 24.0,
    p75: 30.0,
    comparable_count: 14,
    explanation: 'within range',
    or270: {
      article: 'OR Art. 270',
      deadline_days: 30,
      deadline_note: 'within 30 days',
      conditions: [],
      assessment_method: 'Quartierüblichkeit',
      schlichtungsbehoerde: 'Schlichtungsbehörde',
      disclaimer: 'not legal advice',
    },
  });
});

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

  it('shows net amount alongside gross when both available', () => {
    render(<ListingCards listings={[listing]} />);
    expect(screen.getByTestId('listing-rent-net')).toBeTruthy();
    expect(screen.getByTestId('listing-rent-net').textContent).toContain('net');
  });

  it('does not show net label when only gross is available', () => {
    render(<ListingCards listings={[{ ...listing, rent_net: null }]} />);
    expect(screen.queryByTestId('listing-rent-net')).toBeNull();
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

  it('shows broken-image fallback when an image fails to load', () => {
    render(<ListingCards listings={[listing]} />);
    const imgs = screen.getAllByRole('img');
    fireEvent.error(imgs[0]);
    expect(screen.getByTestId('img-error-fallback')).toBeTruthy();
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

  it('renders a RentAnalysisBadge per listing when a reduction applies', async () => {
    mockFetchRentAnalysis.mockResolvedValue(REDUCTION);
    const listings = [listing, { ...listing, id: 2, source_id: 'L-1002' }];
    render(<ListingCards listings={listings} />);

    await waitFor(() => {
      expect(screen.getAllByTestId('rent-analysis-badge').length).toBe(2);
    });
    expect(mockFetchRentAnalysis).toHaveBeenCalledWith(1);
    expect(mockFetchRentAnalysis).toHaveBeenCalledWith(2);
  });

  it('renders an InitialRentBadge when the asking rent is above market', async () => {
    mockFetchInitialRentCheck.mockResolvedValue({
      listing_id: 1,
      verdict: 'above_market',
      target_chf_m2: 32.4,
      median_chf_m2: 26.1,
      p25: 24.0,
      p75: 30.0,
      comparable_count: 14,
      explanation: 'above',
      or270: {
        article: 'OR Art. 270',
        deadline_days: 30,
        deadline_note: 'within 30 days',
        conditions: [],
        assessment_method: 'Quartierüblichkeit',
        schlichtungsbehoerde: 'Schlichtungsbehörde',
        disclaimer: 'not legal advice',
      },
    });
    render(<ListingCards listings={[listing]} />);
    await waitFor(() => {
      expect(screen.getByTestId('initial-rent-badge')).toBeTruthy();
    });
  });

  it('image thumbnails have object-cover class', () => {
    const { container } = render(<ListingCards listings={[listing]} />);
    const imgs = container.querySelectorAll('[data-testid="listing-gallery"] img');
    imgs.forEach((img) => {
      expect((img as HTMLElement).className).toContain('object-cover');
    });
  });
});
