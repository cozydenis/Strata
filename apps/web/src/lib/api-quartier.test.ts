import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock fetch globally
const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

beforeEach(() => {
  vi.resetModules();
  mockFetch.mockReset();
});

const sampleProfile = {
  quartier_id: 11,
  quartier_name: 'Rathaus',
  kreis: 1,
  population: {
    total: 4200,
    density_per_km2: 8400,
    swiss_pct: 65.5,
    foreign_pct: 34.5,
    growth_rate: 1.2,
    trend: 'growing',
  },
  age_distribution: [
    { bucket: '0-17', pct: 12 },
    { bucket: '18-29', pct: 22 },
    { bucket: '30-44', pct: 35 },
    { bucket: '45-64', pct: 21 },
    { bucket: '65+', pct: 10 },
  ],
};

describe('fetchQuartierProfile', () => {
  it('fetches from the correct URL', async () => {
    process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000';
    const { fetchQuartierProfile } = await import('./api');

    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => sampleProfile });

    await fetchQuartierProfile(11);
    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8000/neighborhoods/11/profile',
    );
  });

  it('returns parsed profile on success', async () => {
    process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000';
    const { fetchQuartierProfile } = await import('./api');

    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => sampleProfile });

    const result = await fetchQuartierProfile(11);
    expect(result).toEqual(sampleProfile);
  });

  it('throws on non-ok response', async () => {
    process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000';
    const { fetchQuartierProfile } = await import('./api');

    mockFetch.mockResolvedValueOnce({ ok: false, status: 404 });

    await expect(fetchQuartierProfile(99)).rejects.toThrow('404');
  });

  it('throws on invalid response shape (missing quartier_id)', async () => {
    process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000';
    const { fetchQuartierProfile } = await import('./api');

    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ bad: 'data' }) });

    await expect(fetchQuartierProfile(11)).rejects.toThrow('Unexpected response shape');
  });

  it('uses empty string base URL when env var not set', async () => {
    delete process.env.NEXT_PUBLIC_API_URL;
    const { fetchQuartierProfile } = await import('./api');

    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => sampleProfile });

    await fetchQuartierProfile(11);
    expect(mockFetch).toHaveBeenCalledWith('/neighborhoods/11/profile');
  });

  it('handles null population in response', async () => {
    process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000';
    const { fetchQuartierProfile } = await import('./api');

    const nullPopProfile = { ...sampleProfile, population: null, age_distribution: [] };
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => nullPopProfile });

    const result = await fetchQuartierProfile(12);
    expect(result.population).toBeNull();
  });
});

describe('QuartierProfile interface', () => {
  it('exports QuartierProfile type', async () => {
    const mod = await import('./api');
    // The type exists if we can import the function that uses it
    expect(mod.fetchQuartierProfile).toBeDefined();
  });
});
