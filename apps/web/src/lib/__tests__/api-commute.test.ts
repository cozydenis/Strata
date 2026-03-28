import { describe, it, expect, vi, beforeEach } from 'vitest';

const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

beforeEach(() => {
  vi.resetModules();
  mockFetch.mockReset();
});

describe('COMMUTE_DESTINATIONS', () => {
  it('has exactly four keys', async () => {
    const { COMMUTE_DESTINATIONS } = await import('../api');
    expect(Object.keys(COMMUTE_DESTINATIONS)).toHaveLength(4);
  });

  it('contains hb, eth, airport, technopark keys', async () => {
    const { COMMUTE_DESTINATIONS } = await import('../api');
    expect(COMMUTE_DESTINATIONS).toHaveProperty('hb');
    expect(COMMUTE_DESTINATIONS).toHaveProperty('eth');
    expect(COMMUTE_DESTINATIONS).toHaveProperty('airport');
    expect(COMMUTE_DESTINATIONS).toHaveProperty('technopark');
  });

  it('each destination has a non-empty label string', async () => {
    const { COMMUTE_DESTINATIONS } = await import('../api');
    for (const [key, label] of Object.entries(COMMUTE_DESTINATIONS)) {
      expect(typeof label, `Label for "${key}" must be a string`).toBe('string');
      expect((label as string).length, `Label for "${key}" must not be empty`).toBeGreaterThan(0);
    }
  });
});

describe('fetchCommuteIsochrone', () => {
  it('fetches the correct GeoJSON URL for a destination key', async () => {
    const { fetchCommuteIsochrone } = await import('../api');

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ type: 'FeatureCollection', features: [] }),
    });

    await fetchCommuteIsochrone('hb');
    expect(mockFetch).toHaveBeenCalledWith('/data/commutes/hb.geojson');
  });

  it('fetches correct URL for eth destination', async () => {
    const { fetchCommuteIsochrone } = await import('../api');

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ type: 'FeatureCollection', features: [] }),
    });

    await fetchCommuteIsochrone('eth');
    expect(mockFetch).toHaveBeenCalledWith('/data/commutes/eth.geojson');
  });

  it('returns a FeatureCollection on success', async () => {
    const { fetchCommuteIsochrone } = await import('../api');

    const payload = { type: 'FeatureCollection', features: [{ type: 'Feature', geometry: null, properties: { contour_minutes: 10 } }] };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => payload,
    });

    const result = await fetchCommuteIsochrone('hb');
    expect(result.type).toBe('FeatureCollection');
    expect(Array.isArray(result.features)).toBe(true);
  });

  it('returns null on 404 response', async () => {
    const { fetchCommuteIsochrone } = await import('../api');

    mockFetch.mockResolvedValueOnce({ ok: false, status: 404 });

    const result = await fetchCommuteIsochrone('hb');
    expect(result).toBeNull();
  });

  it('throws on non-404 error response', async () => {
    const { fetchCommuteIsochrone } = await import('../api');

    mockFetch.mockResolvedValueOnce({ ok: false, status: 500 });

    await expect(fetchCommuteIsochrone('hb')).rejects.toThrow('500');
  });
});

describe('QuartierProfile type includes commute_hb_min', () => {
  it('fetchQuartierProfile returns object with commute_hb_min field', async () => {
    process.env.NEXT_PUBLIC_API_URL = '';
    const { fetchQuartierProfile } = await import('../api');

    const payload = {
      quartier_id: 1,
      quartier_name: 'Rathaus',
      kreis: 1,
      population: null,
      age_distribution: [],
      commute_hb_min: 12,
    };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => payload,
    });

    const result = await fetchQuartierProfile(1);
    expect(result).toHaveProperty('commute_hb_min');
    expect(result.commute_hb_min).toBe(12);
  });

  it('fetchQuartierProfile handles null commute_hb_min', async () => {
    process.env.NEXT_PUBLIC_API_URL = '';
    const { fetchQuartierProfile } = await import('../api');

    const payload = {
      quartier_id: 2,
      quartier_name: 'Hochschulen',
      kreis: 1,
      population: null,
      age_distribution: [],
      commute_hb_min: null,
    };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => payload,
    });

    const result = await fetchQuartierProfile(2);
    expect(result.commute_hb_min).toBeNull();
  });
});
