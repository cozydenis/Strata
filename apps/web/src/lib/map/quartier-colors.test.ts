import { describe, it, expect } from 'vitest';

describe('quartierFillColor', () => {
  it('is importable', async () => {
    const { quartierFillColor } = await import('./quartier-colors');
    expect(quartierFillColor).toBeDefined();
  });

  it('returns a MapLibre expression array for population_density', async () => {
    const { quartierFillColor } = await import('./quartier-colors');
    const expr = quartierFillColor('population_density');
    expect(Array.isArray(expr)).toBe(true);
    expect(expr.length).toBeGreaterThan(0);
  });

  it('returns a MapLibre expression array for foreign_pct', async () => {
    const { quartierFillColor } = await import('./quartier-colors');
    const expr = quartierFillColor('foreign_pct');
    expect(Array.isArray(expr)).toBe(true);
  });

  it('returns a MapLibre expression array for growth_rate', async () => {
    const { quartierFillColor } = await import('./quartier-colors');
    const expr = quartierFillColor('growth_rate');
    expect(Array.isArray(expr)).toBe(true);
  });

  it('returns a MapLibre expression for age_avg metric', async () => {
    const { quartierFillColor } = await import('./quartier-colors');
    const expr = quartierFillColor('age_avg');
    expect(Array.isArray(expr)).toBe(true);
  });

  it('expression references the correct property for population_density', async () => {
    const { quartierFillColor } = await import('./quartier-colors');
    const expr = quartierFillColor('population_density');
    const str = JSON.stringify(expr);
    expect(str).toContain('population_density');
  });

  it('expression references the correct property for foreign_pct', async () => {
    const { quartierFillColor } = await import('./quartier-colors');
    const expr = quartierFillColor('foreign_pct');
    const str = JSON.stringify(expr);
    expect(str).toContain('foreign_pct');
  });

  it('unknown metric falls back to a valid expression', async () => {
    const { quartierFillColor } = await import('./quartier-colors');
    const expr = quartierFillColor('unknown_metric_xyz');
    expect(Array.isArray(expr)).toBe(true);
  });

  it('expression contains color strings (hex)', async () => {
    const { quartierFillColor } = await import('./quartier-colors');
    const expr = quartierFillColor('population_density');
    const str = JSON.stringify(expr);
    expect(str).toMatch(/#[0-9a-fA-F]{6}/);
  });
});
