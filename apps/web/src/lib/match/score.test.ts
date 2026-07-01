import { describe, it, expect } from 'vitest';
import {
  computeMatchScores,
  explainMatch,
  MATCH_DIMENSIONS,
  type MatchScoreFeature,
} from './score';
import { DEFAULT_PREFERENCES, type MatchPreferences } from './preferences';

/** Build a fake quartier GeoJSON feature with area_km2 = 1 so per-km² == raw count. */
function feat(
  id: number,
  o: {
    pop?: number;
    growth?: number;
    a017?: number;
    a1829?: number;
    bars?: number;
    cafes?: number;
    rest?: number;
    groc?: number;
    pharm?: number;
    appr?: number;
    start?: number;
    area?: number;
    amenities?: unknown;
  },
): MatchScoreFeature {
  return {
    type: 'Feature',
    properties: {
      quartier_id: id,
      area_km2: o.area ?? 1,
      population_density: o.pop ?? 0,
      growth_rate: o.growth ?? 0,
      age_0_17_pct: o.a017 ?? 0,
      age_18_29_pct: o.a1829 ?? 0,
      amenities:
        'amenities' in o
          ? (o.amenities as never)
          : {
              bars: o.bars ?? 0,
              cafes: o.cafes ?? 0,
              restaurants: o.rest ?? 0,
              groceries: o.groc ?? 0,
              pharmacies: o.pharm ?? 0,
            },
      construction: { approved_projects: o.appr ?? 0, started_projects: o.start ?? 0 },
    },
  } as MatchScoreFeature;
}

// Hand-built fixture. area = 1 for all, so densities equal raw counts.
//   A: venue 0,  daily 10, pop 0,     a017 20, a1829 0,  growth 0, constr 0
//   B: venue 5,  daily 5,  pop 5000,  a017 10, a1829 10, growth 1, constr 5
//   C: venue 10, daily 0,  pop 10000, a017 0,  a1829 20, growth 2, constr 10
const FIXTURE: MatchScoreFeature[] = [
  feat(1, { bars: 0, cafes: 0, rest: 0, groc: 10, pharm: 0, pop: 0, a017: 20, a1829: 0, growth: 0, appr: 0, start: 0 }),
  feat(2, { bars: 1, cafes: 2, rest: 2, groc: 5, pharm: 0, pop: 5000, a017: 10, a1829: 10, growth: 1, appr: 2, start: 3 }),
  feat(3, { bars: 2, cafes: 4, rest: 4, groc: 0, pharm: 0, pop: 10000, a017: 0, a1829: 20, growth: 2, appr: 4, start: 6 }),
];

const weights = (partial: Partial<Record<string, number>>): MatchPreferences => ({
  weights: { ...DEFAULT_PREFERENCES.weights, ...partial } as MatchPreferences['weights'],
});

describe('computeMatchScores', () => {
  it('returns a score + contributions per quartier keyed by quartier_id', () => {
    const scores = computeMatchScores(FIXTURE, DEFAULT_PREFERENCES);
    expect(scores.size).toBe(3);
    expect(scores.get(1)).toBeDefined();
    expect(scores.get(3)?.contributions).toBeDefined();
  });

  it('min-max normalizes: max→1, min→0 for a dimension', () => {
    const scores = computeMatchScores(FIXTURE, DEFAULT_PREFERENCES);
    // nightlife (venue density): C is max, A is min
    expect(scores.get(3)?.contributions.nightlife).toBeCloseTo(1);
    expect(scores.get(1)?.contributions.nightlife).toBeCloseTo(0);
    // dailyNeeds: A is max, C is min
    expect(scores.get(1)?.contributions.dailyNeeds).toBeCloseTo(1);
    expect(scores.get(3)?.contributions.dailyNeeds).toBeCloseTo(0);
  });

  it('produces the hand-computed contributions for feature C', () => {
    const c = computeMatchScores(FIXTURE, DEFAULT_PREFERENCES).get(3)!;
    expect(c.contributions.nightlife).toBeCloseTo(1);
    expect(c.contributions.dailyNeeds).toBeCloseTo(0);
    expect(c.contributions.calm).toBeCloseTo(0);
    expect(c.contributions.family).toBeCloseTo(0);
    expect(c.contributions.youngSocial).toBeCloseTo(1);
    expect(c.contributions.upAndComing).toBeCloseTo(1);
  });

  it('all-equal inputs normalize every dimension to 0.5', () => {
    const equal = [feat(1, { bars: 3, cafes: 3, rest: 3, groc: 2, pharm: 2, pop: 4000, a017: 15, a1829: 15, growth: 1, appr: 1, start: 1 })];
    const c = computeMatchScores(equal, DEFAULT_PREFERENCES).get(1)!;
    for (const d of MATCH_DIMENSIONS) {
      expect(c.contributions[d]).toBeCloseTo(0.5);
    }
    expect(c.score).toBe(50);
  });

  it('scores every fixture quartier at 50% with default (all-equal) weights', () => {
    const scores = computeMatchScores(FIXTURE, DEFAULT_PREFERENCES);
    expect(scores.get(1)?.score).toBe(50);
    expect(scores.get(2)?.score).toBe(50);
    expect(scores.get(3)?.score).toBe(50);
  });

  it('applies weighted mean and excludes weight-0 dimensions', () => {
    // nightlife weight 2, calm weight 0, all others weight 1
    const prefs = weights({ nightlife: 2, calm: 0 });
    // Feature C: nightlife=1(w2), dailyNeeds=0(w1), family=0(w1), youngSocial=1(w1), upAndComing=1(w1)
    // weighted sum = 2*1 + 0 + 0 + 1 + 1 = 4 ; weight sum = 2+1+1+1+1 = 6 → 66.67 → 67
    expect(computeMatchScores(FIXTURE, prefs).get(3)?.score).toBe(67);
    // Feature A: nightlife=0(w2), dailyNeeds=1(w1), family=1(w1), youngSocial=0, upAndComing=0
    // weighted sum = 0 + 1 + 1 + 0 + 0 = 2 ; weight sum = 6 → 33.33 → 33
    expect(computeMatchScores(FIXTURE, prefs).get(1)?.score).toBe(33);
  });

  it('returns null score when all weights are 0', () => {
    const prefs = weights({
      nightlife: 0,
      dailyNeeds: 0,
      calm: 0,
      family: 0,
      youngSocial: 0,
      upAndComing: 0,
    });
    expect(computeMatchScores(FIXTURE, prefs).get(1)?.score).toBeNull();
  });

  it('never produces NaN when amenities are missing or area_km2 is 0', () => {
    const broken: MatchScoreFeature[] = [
      feat(10, { amenities: undefined, area: 0, pop: 1000, a017: 10, a1829: 10, growth: 1, appr: 0, start: 0 }),
      feat(11, { bars: 5, cafes: 5, rest: 5, groc: 3, pharm: 1, pop: 8000, a017: 20, a1829: 25, growth: 2, appr: 3, start: 2 }),
    ];
    const scores = computeMatchScores(broken, DEFAULT_PREFERENCES);
    for (const [, v] of scores) {
      expect(v.score === null || Number.isFinite(v.score)).toBe(true);
      for (const d of MATCH_DIMENSIONS) {
        expect(Number.isFinite(v.contributions[d])).toBe(true);
      }
    }
  });

  it('does not mutate the input features', () => {
    const snapshot = JSON.stringify(FIXTURE);
    computeMatchScores(FIXTURE, DEFAULT_PREFERENCES);
    expect(JSON.stringify(FIXTURE)).toBe(snapshot);
  });
});

describe('explainMatch', () => {
  const contributions = {
    nightlife: 0.9,
    dailyNeeds: 0.1,
    calm: 0.5,
    family: 0.8,
    youngSocial: 0.3,
    upAndComing: 0.2,
  };

  it('returns the top-2 strongest and bottom-2 weakest dimensions', () => {
    const { strong, weak } = explainMatch(contributions, DEFAULT_PREFERENCES);
    expect(strong).toEqual(['nightlife', 'family']);
    expect(weak).toEqual(['daily needs', 'up-and-coming']);
  });

  it('excludes weight-0 dimensions from strong and weak', () => {
    const prefs = weights({ upAndComing: 0 });
    const { strong, weak } = explainMatch(contributions, prefs);
    expect(strong).toEqual(['nightlife', 'family']);
    expect(weak).not.toContain('up-and-coming');
    expect(weak).toEqual(['daily needs', 'young & social']);
  });

  it('does not overlap strong and weak when few dimensions are active', () => {
    const prefs = weights({
      nightlife: 1,
      family: 1,
      dailyNeeds: 0,
      calm: 0,
      youngSocial: 0,
      upAndComing: 0,
    });
    const { strong, weak } = explainMatch(contributions, prefs);
    expect(strong).toEqual(['nightlife', 'family']);
    for (const label of weak) {
      expect(strong).not.toContain(label);
    }
  });
});
