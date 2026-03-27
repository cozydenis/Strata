import { describe, it, expect } from 'vitest';

describe('noiseLineColor', () => {
  it('is importable', async () => {
    const { noiseLineColor } = await import('./noise-colors');
    expect(noiseLineColor).toBeDefined();
  });

  it('returns a MapLibre expression array', async () => {
    const { noiseLineColor } = await import('./noise-colors');
    const expr = noiseLineColor();
    expect(Array.isArray(expr)).toBe(true);
    expect(expr.length).toBeGreaterThan(0);
  });

  it('includes the quiet color #4ade80 (< 50 dB)', async () => {
    const { noiseLineColor } = await import('./noise-colors');
    const expr = noiseLineColor();
    const str = JSON.stringify(expr);
    expect(str).toContain('#4ade80');
  });

  it('includes the moderate color #facc15 (50-60 dB)', async () => {
    const { noiseLineColor } = await import('./noise-colors');
    const expr = noiseLineColor();
    const str = JSON.stringify(expr);
    expect(str).toContain('#facc15');
  });

  it('includes the loud color #fb923c (60-70 dB)', async () => {
    const { noiseLineColor } = await import('./noise-colors');
    const expr = noiseLineColor();
    const str = JSON.stringify(expr);
    expect(str).toContain('#fb923c');
  });

  it('includes the very_loud color #ef4444 (> 70 dB)', async () => {
    const { noiseLineColor } = await import('./noise-colors');
    const expr = noiseLineColor();
    const str = JSON.stringify(expr);
    expect(str).toContain('#ef4444');
  });

  it('expression references "d" property (slim GeoJSON key)', async () => {
    const { noiseLineColor } = await import('./noise-colors');
    const expr = noiseLineColor();
    const str = JSON.stringify(expr);
    expect(str).toContain('"d"');
  });
});
