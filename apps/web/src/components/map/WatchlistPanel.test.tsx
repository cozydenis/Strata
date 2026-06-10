import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { WatchlistPanel } from './WatchlistPanel';

vi.mock('@/lib/supabase', () => ({
  getAccessToken: vi.fn(),
  isAuthConfigured: () => true,
}));

vi.mock('@/lib/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/api')>();
  return {
    ...actual,
    fetchWatchlist: vi.fn(),
    fetchWatchEvents: vi.fn(),
    removeWatch: vi.fn(),
  };
});

import { getAccessToken } from '@/lib/supabase';
import { fetchWatchEvents, fetchWatchlist, removeWatch } from '@/lib/api';

const ITEMS = [
  {
    id: 1,
    egid: 10001,
    ewid: null,
    created_at: '2026-06-10T10:00:00',
    strname: 'Langstrasse',
    deinr: '42',
    dplz4: 8004,
    dplzname: 'Zürich',
  },
  {
    id: 2,
    egid: 10001,
    ewid: 3,
    created_at: '2026-06-10T10:01:00',
    strname: 'Langstrasse',
    deinr: '42',
    dplz4: 8004,
    dplzname: 'Zürich',
  },
];

describe('WatchlistPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getAccessToken).mockResolvedValue('token-123');
    vi.mocked(fetchWatchlist).mockResolvedValue({ total: 2, items: ITEMS });
    vi.mocked(fetchWatchEvents).mockResolvedValue({ total: 0, items: [] });
    vi.mocked(removeWatch).mockResolvedValue(undefined);
  });

  it('renders watch items with addresses', async () => {
    render(<WatchlistPanel onClose={() => {}} />);
    await waitFor(() => expect(screen.getAllByTestId('watchlist-item')).toHaveLength(2));
    expect(screen.getAllByText(/Langstrasse 42, 8004 Zürich/)).toHaveLength(2);
    expect(screen.getByText('Whole building')).toBeTruthy();
    expect(screen.getByText('Unit 3')).toBeTruthy();
  });

  it('shows empty state when nothing watched', async () => {
    vi.mocked(fetchWatchlist).mockResolvedValue({ total: 0, items: [] });
    render(<WatchlistPanel onClose={() => {}} />);
    await waitFor(() => expect(screen.getByTestId('watchlist-empty')).toBeTruthy());
  });

  it('prompts sign-in when no token', async () => {
    vi.mocked(getAccessToken).mockResolvedValue(null);
    render(<WatchlistPanel onClose={() => {}} />);
    await waitFor(() => expect(screen.getByTestId('watchlist-error').textContent).toContain('Sign in'));
  });

  it('removes an item', async () => {
    render(<WatchlistPanel onClose={() => {}} />);
    await waitFor(() => expect(screen.getAllByTestId('watchlist-item')).toHaveLength(2));
    fireEvent.click(screen.getByTestId('watch-remove-1'));
    await waitFor(() => expect(screen.getAllByTestId('watchlist-item')).toHaveLength(1));
    expect(removeWatch).toHaveBeenCalledWith('token-123', 1);
  });

  it('calls onClose', async () => {
    const onClose = vi.fn();
    render(<WatchlistPanel onClose={onClose} />);
    await waitFor(() => expect(screen.getAllByTestId('watchlist-item')).toHaveLength(2));
    fireEvent.click(screen.getByTestId('watchlist-close'));
    expect(onClose).toHaveBeenCalledOnce();
  });

  it('shows an error when the API fails', async () => {
    vi.mocked(fetchWatchlist).mockRejectedValue(new Error('500'));
    render(<WatchlistPanel onClose={() => {}} />);
    await waitFor(() => expect(screen.getByTestId('watchlist-error')).toBeTruthy());
  });
});

describe('WatchlistPanel activity feed', () => {
  const baseEvent = {
    listing_id: 7,
    egid: 10001,
    street: 'Langstrasse',
    house_number: '42',
    plz: 8004,
    city: 'Zürich',
    rent_gross: 2400,
    rooms: 3.5,
    area_m2: 80,
    source_url: 'https://flatfox.ch/x/7',
    old_value: null,
    new_value: null,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getAccessToken).mockResolvedValue('token-123');
    vi.mocked(fetchWatchlist).mockResolvedValue({ total: 1, items: [ITEMS[0]] });
    vi.mocked(removeWatch).mockResolvedValue(undefined);
  });

  it('renders new listing and gone events', async () => {
    vi.mocked(fetchWatchEvents).mockResolvedValue({
      total: 2,
      items: [
        { ...baseEvent, type: 'new_listing', ts: '2026-06-08T10:00:00' },
        { ...baseEvent, type: 'listing_gone', ts: '2026-06-01T10:00:00', listing_id: 8 },
      ],
    });
    render(<WatchlistPanel onClose={() => {}} />);
    await waitFor(() => expect(screen.getByTestId('watchlist-activity')).toBeTruthy());
    expect(screen.getAllByTestId('watch-event')).toHaveLength(2);
    expect(screen.getByText('New listing')).toBeTruthy();
    expect(screen.getByText('Listing gone')).toBeTruthy();
    // 2 events + the watch item itself all carry the address
    expect(screen.getAllByText(/Langstrasse 42/)).toHaveLength(3);
  });

  it('renders price changes as old → new', async () => {
    vi.mocked(fetchWatchEvents).mockResolvedValue({
      total: 1,
      items: [
        { ...baseEvent, type: 'price_change', ts: '2026-06-05T10:00:00', old_value: '2200', new_value: '2400' },
      ],
    });
    render(<WatchlistPanel onClose={() => {}} />);
    await waitFor(() => expect(screen.getByText('Price change')).toBeTruthy());
    expect(screen.getByText(/CHF 2[’']?200 → 2[’']?400/)).toBeTruthy();
  });

  it('omits activity section when there are no events', async () => {
    vi.mocked(fetchWatchEvents).mockResolvedValue({ total: 0, items: [] });
    render(<WatchlistPanel onClose={() => {}} />);
    await waitFor(() => expect(screen.getAllByTestId('watchlist-item')).toHaveLength(1));
    expect(screen.queryByTestId('watchlist-activity')).toBeNull();
  });
});
