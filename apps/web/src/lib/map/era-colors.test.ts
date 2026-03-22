import { describe, it, expect } from 'vitest';
import { ERA_COLORS, eraColorExpression, eraForYear } from './era-colors';

describe('ERA_COLORS', () => {
  it('has exactly 7 eras', () => {
    expect(ERA_COLORS).toHaveLength(7);
  });

  it('includes an unknown/null era', () => {
    const unknownEra = ERA_COLORS.find((e) => e.label === 'Unknown');
    expect(unknownEra).toBeDefined();
  });

  it('each era has label and color', () => {
    for (const era of ERA_COLORS) {
      expect(era.label).toBeTruthy();
      expect(era.color).toMatch(/^#[0-9A-Fa-f]{6}$/);
    }
  });
});

describe('eraForYear', () => {
  it('classifies pre-1900 buildings', () => {
    expect(eraForYear(1850).label).toBe('Pre-1900');
    expect(eraForYear(1899).label).toBe('Pre-1900');
  });

  it('classifies 1900 as 1900–1945 (boundary inclusive)', () => {
    expect(eraForYear(1900).label).toBe('1900–1945');
  });

  it('classifies 1945 as 1900–1945', () => {
    expect(eraForYear(1945).label).toBe('1900–1945');
  });

  it('classifies 1946 as 1946–1970', () => {
    expect(eraForYear(1946).label).toBe('1946–1970');
  });

  it('classifies 2011 as 2011+', () => {
    expect(eraForYear(2011).label).toBe('2011+');
  });

  it('returns Unknown era for null', () => {
    expect(eraForYear(null).label).toBe('Unknown');
  });

  it('returns Unknown era for undefined', () => {
    expect(eraForYear(undefined).label).toBe('Unknown');
  });
});

describe('eraColorExpression', () => {
  it('returns a MapLibre step expression array', () => {
    const expr = eraColorExpression();
    expect(Array.isArray(expr)).toBe(true);
    expect(expr[0]).toBe('step');
  });

  it('coalesces null gbauj to 0', () => {
    const expr = eraColorExpression();
    expect(expr[1]).toEqual(['coalesce', ['get', 'gbauj'], 0]);
  });

  it('uses Unknown color as fallback for null/0 values', () => {
    const expr = eraColorExpression();
    const unknownEra = ERA_COLORS.find((e) => e.label === 'Unknown')!;
    expect(expr[2]).toBe(unknownEra.color);
  });

  it('maps year >= 1 to Pre-1900 color before first era stop', () => {
    const expr = eraColorExpression();
    // ['step', input, fallback, 1, pre1900Color, 1900, ...]
    expect(expr[3]).toBe(1);
    const pre1900 = ERA_COLORS.find((e) => e.label === 'Pre-1900')!;
    expect(expr[4]).toBe(pre1900.color);
  });

  it('contains era stops after the pre-1900 entry', () => {
    const expr = eraColorExpression();
    // stops start at index 5: number, color, number, color...
    expect(typeof expr[5]).toBe('number');
    expect(typeof expr[6]).toBe('string');
  });
});
