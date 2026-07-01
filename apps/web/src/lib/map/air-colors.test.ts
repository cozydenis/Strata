import { describe, it, expect } from 'vitest';
import {
  AIR_LEVELS,
  AIR_NEUTRAL_COLOR,
  airLevelColor,
  airCircleColor,
} from './air-colors';

describe('airLevelColor', () => {
  it('maps "good" to the sage green', () => {
    expect(airLevelColor('good')).toBe('#8FA071');
  });

  it('maps "moderate" to the amber', () => {
    expect(airLevelColor('moderate')).toBe('#D4915A');
  });

  it('maps "high" to the terracotta', () => {
    expect(airLevelColor('high')).toBe('#C4785B');
  });

  it('falls back to the neutral color for a missing level', () => {
    expect(airLevelColor(null)).toBe(AIR_NEUTRAL_COLOR);
    expect(airLevelColor(undefined)).toBe(AIR_NEUTRAL_COLOR);
  });

  it('falls back to the neutral color for an unknown level', () => {
    expect(airLevelColor('bogus')).toBe(AIR_NEUTRAL_COLOR);
  });
});

describe('AIR_LEVELS', () => {
  it('lists exactly the three functional levels in severity order', () => {
    expect(AIR_LEVELS.map((l) => l.level)).toEqual(['good', 'moderate', 'high']);
  });

  it('each level has a hex color and a human label', () => {
    for (const l of AIR_LEVELS) {
      expect(l.color).toMatch(/^#[0-9A-Fa-f]{6}$/);
      expect(l.label.length).toBeGreaterThan(0);
    }
  });
});

describe('airCircleColor', () => {
  it('returns a MapLibre expression array', () => {
    const expr = airCircleColor();
    expect(Array.isArray(expr)).toBe(true);
    expect(expr.length).toBeGreaterThan(0);
  });

  it('is keyed on the "level" property', () => {
    const str = JSON.stringify(airCircleColor());
    expect(str).toContain('"level"');
  });

  it('includes every level color and the neutral fallback', () => {
    const str = JSON.stringify(airCircleColor());
    expect(str).toContain('#8FA071');
    expect(str).toContain('#D4915A');
    expect(str).toContain('#C4785B');
    expect(str).toContain(AIR_NEUTRAL_COLOR);
  });
});
