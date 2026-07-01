import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock fetch globally
const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

beforeEach(() => {
  vi.resetModules();
  mockFetch.mockReset();
});

const REDUCTION = {
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

describe('fetchRentAnalysis', () => {
  it('fetches from the correct URL', async () => {
    process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000';
    const { fetchRentAnalysis } = await import('./api');

    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => REDUCTION });

    await fetchRentAnalysis(42);
    expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/legal/listings/42/rent-analysis');
  });

  it('appends base_rate query param when provided', async () => {
    process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000';
    const { fetchRentAnalysis } = await import('./api');

    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => REDUCTION });

    await fetchRentAnalysis(42, 1.75);
    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8000/legal/listings/42/rent-analysis?base_rate=1.75'
    );
  });

  it('returns parsed analysis on success', async () => {
    process.env.NEXT_PUBLIC_API_URL = '';
    const { fetchRentAnalysis } = await import('./api');

    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => REDUCTION });

    const result = await fetchRentAnalysis(42);
    expect(result).toEqual(REDUCTION);
  });

  it('uses empty string base URL when env var is not set', async () => {
    delete process.env.NEXT_PUBLIC_API_URL;
    const { fetchRentAnalysis } = await import('./api');

    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => REDUCTION });

    await fetchRentAnalysis(42);
    expect(mockFetch).toHaveBeenCalledWith('/legal/listings/42/rent-analysis');
  });

  it('throws on non-ok response', async () => {
    process.env.NEXT_PUBLIC_API_URL = '';
    const { fetchRentAnalysis } = await import('./api');

    mockFetch.mockResolvedValueOnce({ ok: false, status: 500 });

    await expect(fetchRentAnalysis(42)).rejects.toThrow('500');
  });

  it('throws on malformed response shape', async () => {
    process.env.NEXT_PUBLIC_API_URL = '';
    const { fetchRentAnalysis } = await import('./api');

    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ bad: 'data' }) });

    await expect(fetchRentAnalysis(42)).rejects.toThrow('Unexpected response shape');
  });

  it('propagates network errors', async () => {
    process.env.NEXT_PUBLIC_API_URL = '';
    const { fetchRentAnalysis } = await import('./api');

    mockFetch.mockRejectedValueOnce(new Error('network down'));

    await expect(fetchRentAnalysis(42)).rejects.toThrow('network down');
  });
});

describe('generateHerabsetzung', () => {
  const payload = {
    tenant_name: 'Anna Muster',
    tenant_address: 'Langstrasse 1, 8004 Zürich',
    landlord_name: 'Immo AG',
    landlord_address: 'Bahnhofstrasse 1, 8001 Zürich',
  };

  it('POSTs to the correct URL with JSON body', async () => {
    process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000';
    const { generateHerabsetzung } = await import('./api');

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ listing_id: 42, basis: 'known', letter: 'Sehr geehrte Damen…' }),
    });

    await generateHerabsetzung(42, payload);

    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8000/legal/listings/42/herabsetzungsbegehren',
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
    );
  });

  it('returns ok result with the letter on success', async () => {
    process.env.NEXT_PUBLIC_API_URL = '';
    const { generateHerabsetzung } = await import('./api');

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ listing_id: 42, basis: 'known', letter: 'BODY' }),
    });

    const result = await generateHerabsetzung(42, payload);
    expect(result.status).toBe('ok');
    if (result.status === 'ok') {
      expect(result.data.letter).toBe('BODY');
      expect(result.data.listing_id).toBe(42);
    }
  });

  it('returns a distinguishable no_reduction result on 409', async () => {
    process.env.NEXT_PUBLIC_API_URL = '';
    const { generateHerabsetzung } = await import('./api');

    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 409,
      json: async () => ({ detail: 'no reduction applies' }),
    });

    const result = await generateHerabsetzung(42, payload);
    expect(result.status).toBe('no_reduction');
  });

  it('throws with the detail message on 422 validation error', async () => {
    process.env.NEXT_PUBLIC_API_URL = '';
    const { generateHerabsetzung } = await import('./api');

    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 422,
      json: async () => ({ detail: 'tenant_name is required' }),
    });

    await expect(generateHerabsetzung(42, payload)).rejects.toThrow('tenant_name is required');
  });

  it('throws on other non-ok responses', async () => {
    process.env.NEXT_PUBLIC_API_URL = '';
    const { generateHerabsetzung } = await import('./api');

    mockFetch.mockResolvedValueOnce({ ok: false, status: 500, json: async () => ({}) });

    await expect(generateHerabsetzung(42, payload)).rejects.toThrow('500');
  });

  it('propagates network errors', async () => {
    process.env.NEXT_PUBLIC_API_URL = '';
    const { generateHerabsetzung } = await import('./api');

    mockFetch.mockRejectedValueOnce(new Error('offline'));

    await expect(generateHerabsetzung(42, payload)).rejects.toThrow('offline');
  });
});
