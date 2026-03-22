import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock fetch globally
const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

// Reset module between tests so NEXT_PUBLIC_API_URL can be controlled
beforeEach(() => {
  vi.resetModules();
  mockFetch.mockReset();
});

describe('fetchBuildingSummary', () => {
  it('fetches from the correct URL', async () => {
    process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000';
    const { fetchBuildingSummary } = await import('./api');

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ egid: 12345, gbauj: 1980, gkat: 1021, gastw: 3, ganzwhg: 6, lat: 47.376, lon: 8.541, strname: 'Bahnhofstrasse', deinr: '1', dplz4: 8001, dplzname: 'Zürich' }),
    });

    await fetchBuildingSummary(12345);

    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8000/registry/buildings/12345/summary'
    );
  });

  it('returns parsed JSON on success', async () => {
    process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000';
    const { fetchBuildingSummary } = await import('./api');

    const payload = { egid: 12345, gbauj: 1980, gkat: 1021, gastw: 3, ganzwhg: 6, lat: 47.376, lon: 8.541, strname: 'Bahnhofstrasse', deinr: '1', dplz4: 8001, dplzname: 'Zürich' };
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => payload });

    const result = await fetchBuildingSummary(12345);
    expect(result).toEqual(payload);
  });

  it('throws on non-ok response', async () => {
    process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000';
    const { fetchBuildingSummary } = await import('./api');

    mockFetch.mockResolvedValueOnce({ ok: false, status: 404 });

    await expect(fetchBuildingSummary(99999)).rejects.toThrow('404');
  });

  it('throws on invalid response shape', async () => {
    process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000';
    const { fetchBuildingSummary } = await import('./api');

    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ bad: 'data' }) });

    await expect(fetchBuildingSummary(1)).rejects.toThrow('Unexpected response shape');
  });

  it('uses empty string base URL when env var is not set', async () => {
    delete process.env.NEXT_PUBLIC_API_URL;
    const { fetchBuildingSummary } = await import('./api');

    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ egid: 1 }) });

    await fetchBuildingSummary(1);
    expect(mockFetch).toHaveBeenCalledWith('/registry/buildings/1/summary');
  });
});
