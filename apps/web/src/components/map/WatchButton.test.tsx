import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { WatchButton } from './WatchButton';

vi.mock('@/lib/supabase', () => ({
  getAccessToken: vi.fn(),
  isAuthConfigured: vi.fn(() => true),
}));

vi.mock('@/lib/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/api')>();
  return { ...actual, addWatch: vi.fn() };
});

import { getAccessToken, isAuthConfigured } from '@/lib/supabase';
import { addWatch } from '@/lib/api';

describe('WatchButton', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(isAuthConfigured).mockReturnValue(true);
    vi.mocked(getAccessToken).mockResolvedValue('token-123');
    vi.mocked(addWatch).mockResolvedValue({
      id: 1, egid: 10001, ewid: null, created_at: '', strname: null, deinr: null, dplz4: null, dplzname: null,
    });
  });

  it('adds a building watch on click', async () => {
    render(<WatchButton egid={10001} />);
    fireEvent.click(screen.getByTestId('watch-building'));
    await waitFor(() => expect(screen.getByText('★ Watching')).toBeTruthy());
    expect(addWatch).toHaveBeenCalledWith('token-123', 10001, undefined);
  });

  it('adds a unit watch in compact mode', async () => {
    render(<WatchButton egid={10001} ewid={4} compact />);
    fireEvent.click(screen.getByTestId('watch-unit-4'));
    await waitFor(() => expect(addWatch).toHaveBeenCalledWith('token-123', 10001, 4));
  });

  it('prompts sign-in when there is no session', async () => {
    vi.mocked(getAccessToken).mockResolvedValue(null);
    render(<WatchButton egid={10001} />);
    fireEvent.click(screen.getByTestId('watch-building'));
    await waitFor(() => expect(screen.getByText('Sign in to watch')).toBeTruthy());
    expect(addWatch).not.toHaveBeenCalled();
  });

  it('shows retry state on API failure', async () => {
    vi.mocked(addWatch).mockRejectedValue(new Error('500'));
    render(<WatchButton egid={10001} />);
    fireEvent.click(screen.getByTestId('watch-building'));
    await waitFor(() => expect(screen.getByText('Failed — retry')).toBeTruthy());
  });

  it('renders nothing when auth is not configured', () => {
    vi.mocked(isAuthConfigured).mockReturnValue(false);
    render(<WatchButton egid={10001} />);
    expect(screen.queryByTestId('watch-building')).toBeNull();
  });
});
