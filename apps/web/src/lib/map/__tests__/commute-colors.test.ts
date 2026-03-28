import { describe, it, expect } from 'vitest';

describe('commute-colors', () => {
  it('exports COMMUTE_MINUTES_EXPRESSION as an array starting with "step"', async () => {
    const { COMMUTE_MINUTES_EXPRESSION } = await import('../commute-colors');
    expect(Array.isArray(COMMUTE_MINUTES_EXPRESSION)).toBe(true);
    expect(COMMUTE_MINUTES_EXPRESSION[0]).toBe('step');
  });

  it('exports COMMUTE_COLORS object with exactly 5 keys', async () => {
    const { COMMUTE_COLORS } = await import('../commute-colors');
    expect(typeof COMMUTE_COLORS).toBe('object');
    expect(Object.keys(COMMUTE_COLORS)).toHaveLength(5);
  });

  it('maps "0-10" band to green hex', async () => {
    const { COMMUTE_COLORS } = await import('../commute-colors');
    expect(COMMUTE_COLORS['0-10']).toBe('#1a9850');
  });

  it('maps "45+" band to red hex', async () => {
    const { COMMUTE_COLORS } = await import('../commute-colors');
    expect(COMMUTE_COLORS['45+']).toBe('#d73027');
  });

  it('exports COMMUTE_OPACITY_EXPRESSION as an array', async () => {
    const { COMMUTE_OPACITY_EXPRESSION } = await import('../commute-colors');
    expect(Array.isArray(COMMUTE_OPACITY_EXPRESSION)).toBe(true);
    expect(COMMUTE_OPACITY_EXPRESSION[0]).toBe('step');
  });

  it('COMMUTE_MINUTES_EXPRESSION uses contour_minutes property', async () => {
    const { COMMUTE_MINUTES_EXPRESSION } = await import('../commute-colors');
    const exprStr = JSON.stringify(COMMUTE_MINUTES_EXPRESSION);
    expect(exprStr).toContain('contour_minutes');
  });

  it('COMMUTE_COLORS contains all expected band keys', async () => {
    const { COMMUTE_COLORS } = await import('../commute-colors');
    const expectedKeys = ['0-10', '10-20', '20-30', '30-45', '45+'];
    for (const key of expectedKeys) {
      expect(COMMUTE_COLORS).toHaveProperty(key);
    }
  });

  it('all COMMUTE_COLORS values are valid hex color strings', async () => {
    const { COMMUTE_COLORS } = await import('../commute-colors');
    const hexPattern = /^#[0-9a-fA-F]{6}$/;
    for (const [band, color] of Object.entries(COMMUTE_COLORS)) {
      expect(color, `Color for band "${band}" should be a valid hex`).toMatch(hexPattern);
    }
  });
});
