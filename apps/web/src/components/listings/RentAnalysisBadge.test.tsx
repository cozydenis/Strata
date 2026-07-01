import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { RentAnalysisBadge } from './RentAnalysisBadge';
import type { RentAnalysis } from '@/lib/api';

vi.mock('@/lib/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/api')>();
  return {
    ...actual,
    fetchRentAnalysis: vi.fn(),
    generateHerabsetzung: vi.fn(),
  };
});

import { fetchRentAnalysis } from '@/lib/api';

const mockFetchRentAnalysis = vi.mocked(fetchRentAnalysis);

const REDUCTION: RentAnalysis = {
  listing_id: 42,
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
  mockFetchRentAnalysis.mockReset();
});

describe('RentAnalysisBadge', () => {
  it('renders a reduction badge with the formatted monthly saving', async () => {
    mockFetchRentAnalysis.mockResolvedValueOnce(REDUCTION);
    render(<RentAnalysisBadge listingId={42} />);

    const badge = await screen.findByTestId('rent-analysis-badge');
    expect(badge.textContent).toContain('Mietsenkung');
    expect(badge.textContent).toMatch(/114[.,]80/);
  });

  it('shows the assumed-basis hint when basis is assumed_from_first_seen', async () => {
    mockFetchRentAnalysis.mockResolvedValueOnce({ ...REDUCTION, basis: 'assumed_from_first_seen' });
    render(<RentAnalysisBadge listingId={42} />);

    await screen.findByTestId('rent-analysis-badge');
    expect(screen.getByTestId('rent-analysis-hint').textContent).toContain('geschätzt');
  });

  it('does not show the hint when basis is known', async () => {
    mockFetchRentAnalysis.mockResolvedValueOnce(REDUCTION);
    render(<RentAnalysisBadge listingId={42} />);

    await screen.findByTestId('rent-analysis-badge');
    expect(screen.queryByTestId('rent-analysis-hint')).toBeNull();
  });

  it('renders nothing for basis unknown', async () => {
    mockFetchRentAnalysis.mockResolvedValueOnce({ ...REDUCTION, basis: 'unknown', direction: null });
    const { container } = render(<RentAnalysisBadge listingId={42} />);

    await waitFor(() => expect(mockFetchRentAnalysis).toHaveBeenCalled());
    expect(container.querySelector('[data-testid="rent-analysis-badge"]')).toBeNull();
  });

  it('renders nothing when direction is increase', async () => {
    mockFetchRentAnalysis.mockResolvedValueOnce({ ...REDUCTION, direction: 'increase' });
    const { container } = render(<RentAnalysisBadge listingId={42} />);

    await waitFor(() => expect(mockFetchRentAnalysis).toHaveBeenCalled());
    expect(container.querySelector('[data-testid="rent-analysis-badge"]')).toBeNull();
  });

  it('renders nothing when direction is none', async () => {
    mockFetchRentAnalysis.mockResolvedValueOnce({ ...REDUCTION, direction: 'none' });
    const { container } = render(<RentAnalysisBadge listingId={42} />);

    await waitFor(() => expect(mockFetchRentAnalysis).toHaveBeenCalled());
    expect(container.querySelector('[data-testid="rent-analysis-badge"]')).toBeNull();
  });

  it('renders nothing on fetch error', async () => {
    mockFetchRentAnalysis.mockRejectedValueOnce(new Error('boom'));
    const { container } = render(<RentAnalysisBadge listingId={42} />);

    await waitFor(() => expect(mockFetchRentAnalysis).toHaveBeenCalled());
    expect(container.querySelector('[data-testid="rent-analysis-badge"]')).toBeNull();
  });

  it('opens the letter dialog when the badge is clicked', async () => {
    mockFetchRentAnalysis.mockResolvedValueOnce(REDUCTION);
    render(<RentAnalysisBadge listingId={42} />);

    const badge = await screen.findByTestId('rent-analysis-badge');
    expect(screen.queryByTestId('herabsetzung-dialog')).toBeNull();
    fireEvent.click(badge);
    expect(screen.getByTestId('herabsetzung-dialog')).toBeTruthy();
  });
});
