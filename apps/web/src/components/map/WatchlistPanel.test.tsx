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
    removeWatch: vi.fn(),
  };
});

import { getAccessToken } from '@/lib/supabase';
import { fetchWatchlist, removeWatch } from '@/lib/api';

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
    vi.mocked(getAccessToken).mockResolvedValue('token-123');
    vi.mocked(fetchWatchlist).mockResolvedValue({ total: 2, items: ITEMS });
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
