import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import {
  DEFAULT_PREFERENCES,
  MATCH_DIMENSIONS,
  hasActivePreferences,
  loadPreferences,
  savePreferences,
  type MatchPreferences,
} from './preferences';

const STORAGE_KEY = 'strata.match.preferences.v1';

describe('DEFAULT_PREFERENCES', () => {
  it('assigns weight 1 to every dimension', () => {
    for (const dim of MATCH_DIMENSIONS) {
      expect(DEFAULT_PREFERENCES.weights[dim]).toBe(1);
    }
  });
});

describe('preferences persistence', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it('returns defaults when nothing is stored', () => {
    expect(loadPreferences()).toEqual(DEFAULT_PREFERENCES);
  });

  it('round-trips saved preferences', () => {
    const prefs: MatchPreferences = {
      weights: { nightlife: 2, dailyNeeds: 0, calm: 1, family: 2, youngSocial: 0, upAndComing: 1 },
    };
    savePreferences(prefs);
    expect(loadPreferences()).toEqual(prefs);
  });

  it('falls back to defaults on corrupted JSON', () => {
    window.localStorage.setItem(STORAGE_KEY, '{not valid json');
    expect(loadPreferences()).toEqual(DEFAULT_PREFERENCES);
  });

  it('merges missing keys with defaults', () => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify({ weights: { nightlife: 2 } }));
    const loaded = loadPreferences();
    expect(loaded.weights.nightlife).toBe(2);
    expect(loaded.weights.calm).toBe(1);
    expect(loaded.weights.upAndComing).toBe(1);
  });

  it('clamps out-of-range and non-numeric weights', () => {
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ weights: { nightlife: 99, dailyNeeds: -5, calm: 'x' } }),
    );
    const loaded = loadPreferences();
    expect(loaded.weights.nightlife).toBe(2);
    expect(loaded.weights.dailyNeeds).toBe(0);
    expect(loaded.weights.calm).toBe(1); // invalid → default
  });
});

describe('SSR guard', () => {
  const original = globalThis.window;
  afterEach(() => {
    vi.unstubAllGlobals();
    (globalThis as { window?: unknown }).window = original;
  });

  it('loadPreferences returns defaults without a window', () => {
    vi.stubGlobal('window', undefined);
    expect(loadPreferences()).toEqual(DEFAULT_PREFERENCES);
  });

  it('savePreferences does not throw without a window', () => {
    vi.stubGlobal('window', undefined);
    expect(() => savePreferences(DEFAULT_PREFERENCES)).not.toThrow();
  });
});

describe('hasActivePreferences', () => {
  it('is true when any weight is non-zero', () => {
    expect(hasActivePreferences(DEFAULT_PREFERENCES)).toBe(true);
  });

  it('is false when all weights are zero', () => {
    const allZero: MatchPreferences = {
      weights: { nightlife: 0, dailyNeeds: 0, calm: 0, family: 0, youngSocial: 0, upAndComing: 0 },
    };
    expect(hasActivePreferences(allZero)).toBe(false);
  });
});
