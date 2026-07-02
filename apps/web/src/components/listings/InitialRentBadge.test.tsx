import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { InitialRentBadge } from './InitialRentBadge';
import * as api from '@/lib/api';

vi.mock('@/lib/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/api')>();
  return { ...actual, fetchInitialRentCheck: vi.fn() };
});

const mockFetch = vi.mocked(api.fetchInitialRentCheck);

const OR270 = {
  article: 'OR Art. 270 (Anfechtung des Anfangsmietzinses)',
  deadline_days: 30,
  deadline_note: 'within 30 days of taking over the flat',
  conditions: ['personal or family hardship', 'local housing shortage'],
  assessment_method: 'Quartierüblichkeit',
  schlichtungsbehoerde: 'Schlichtungsbehörde in Mietsachen',
  disclaimer: 'Indicative analysis, not legal advice.',
};

function check(verdict: api.InitialRentVerdict): api.InitialRentCheck {
  return {
    listing_id: 42,
    verdict,
    target_chf_m2: 32.4,
    median_chf_m2: 26.1,
    p25: 24.0,
    p75: 30.0,
    comparable_count: 14,
    explanation: 'Asking CHF 32.40/m² vs. quartier median CHF 26.10/m² across 14 comparable listings.',
    or270: OR270,
  };
}

beforeEach(() => {
  mockFetch.mockReset();
});

describe('InitialRentBadge', () => {
  it('renders nothing for within_range', async () => {
    mockFetch.mockResolvedValueOnce(check('within_range'));
    const { container } = render(<InitialRentBadge listingId={42} />);
    await waitFor(() => expect(mockFetch).toHaveBeenCalled());
    expect(container.innerHTML).toBe('');
  });

  it('renders nothing for insufficient_data', async () => {
    mockFetch.mockResolvedValueOnce(check('insufficient_data'));
    const { container } = render(<InitialRentBadge listingId={42} />);
    await waitFor(() => expect(mockFetch).toHaveBeenCalled());
    expect(container.innerHTML).toBe('');
  });

  it('renders nothing on fetch error', async () => {
    mockFetch.mockRejectedValueOnce(new Error('500'));
    const { container } = render(<InitialRentBadge listingId={42} />);
    await waitFor(() => expect(mockFetch).toHaveBeenCalled());
    expect(container.innerHTML).toBe('');
  });

  it('renders the badge for above_market with CHF/m² figures', async () => {
    mockFetch.mockResolvedValueOnce(check('above_market'));
    render(<InitialRentBadge listingId={42} />);
    const badge = await screen.findByTestId('initial-rent-badge');
    expect(badge.textContent).toContain('Über Quartier-Niveau');
    expect(badge.textContent).toContain('32.40');
    expect(badge.textContent).toContain('26.10');
  });

  it('marks clearly_above_market with the strong variant', async () => {
    mockFetch.mockResolvedValueOnce(check('clearly_above_market'));
    render(<InitialRentBadge listingId={42} />);
    const badge = await screen.findByTestId('initial-rent-badge');
    expect(badge.textContent).toContain('Deutlich über Quartier-Niveau');
  });

  it('expands inline with explanation and OR 270 info on click', async () => {
    mockFetch.mockResolvedValueOnce(check('above_market'));
    render(<InitialRentBadge listingId={42} />);
    const badge = await screen.findByTestId('initial-rent-badge');

    expect(screen.queryByTestId('initial-rent-details')).toBeNull();
    fireEvent.click(badge);

    const details = screen.getByTestId('initial-rent-details');
    expect(details.textContent).toContain('14 comparable listings');
    expect(details.textContent).toContain('30');            // deadline days
    expect(details.textContent).toContain('Schlichtungsbehörde');
    expect(details.textContent).toContain('not legal advice');

    fireEvent.click(badge);
    expect(screen.queryByTestId('initial-rent-details')).toBeNull();
  });
});
