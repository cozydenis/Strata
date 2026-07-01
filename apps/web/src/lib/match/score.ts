/**
 * Pure, explainable per-Quartier match scoring.
 *
 * Every score is derived from six normalized dimensions (each 0..1, min-max
 * normalized across the supplied Quartiere) combined via a weighted mean of the
 * user's preferences. No DOM, no fetch, no mutation of inputs.
 */

import {
  MATCH_DIMENSIONS,
  DIMENSION_SHORT_LABELS,
  type MatchDimension,
  type MatchPreferences,
} from './preferences';

export { MATCH_DIMENSIONS, type MatchDimension };

interface Amenities {
  bars?: number;
  cafes?: number;
  restaurants?: number;
  groceries?: number;
  pharmacies?: number;
  [key: string]: unknown;
}

interface Construction {
  approved_projects?: number;
  started_projects?: number;
  [key: string]: unknown;
}

export interface MatchScoreProperties {
  quartier_id: number;
  area_km2?: number;
  population_density?: number;
  growth_rate?: number;
  age_0_17_pct?: number;
  age_18_29_pct?: number;
  amenities?: Amenities | null;
  construction?: Construction | null;
}

export interface MatchScoreFeature {
  type?: string;
  properties: MatchScoreProperties;
}

export interface MatchResult {
  /** Whole-percent match score, or null when all weights are 0. */
  score: number | null;
  /** Per-dimension value in 0..1 used to explain the score. */
  contributions: Record<MatchDimension, number>;
}

/** Safe numeric coercion — non-finite or non-number values become 0. */
function num(value: unknown): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : 0;
}

/** Per-km² density, guarding against a zero/absent area (returns 0, never NaN). */
function perKm2(count: number, area: number): number {
  return area > 0 ? count / area : 0;
}

/** Base (pre-normalization) metrics extracted from a single feature. */
interface BaseMetrics {
  venueDensity: number;
  dailyDensity: number;
  popDensity: number;
  family: number;
  youngSocial: number;
  growth: number;
  constructionDensity: number;
}

function extractBaseMetrics(feature: MatchScoreFeature): BaseMetrics {
  const p = feature.properties;
  const a: Amenities = p.amenities ?? {};
  const c: Construction = p.construction ?? {};
  const area = num(p.area_km2);

  const venues = num(a.bars) + num(a.cafes) + num(a.restaurants);
  const daily = num(a.groceries) + num(a.pharmacies);
  const projects = num(c.approved_projects) + num(c.started_projects);

  return {
    venueDensity: perKm2(venues, area),
    dailyDensity: perKm2(daily, area),
    popDensity: num(p.population_density),
    family: num(p.age_0_17_pct),
    youngSocial: num(p.age_18_29_pct),
    growth: num(p.growth_rate),
    constructionDensity: perKm2(projects, area),
  };
}

/** Min-max normalize an array to 0..1; all-equal inputs collapse to 0.5. */
function minMax(values: number[]): number[] {
  if (values.length === 0) return [];
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min;
  if (span === 0) return values.map(() => 0.5);
  return values.map((v) => (v - min) / span);
}

/**
 * Compute match scores for every feature.
 * Returns a Map keyed by quartier_id → { score, contributions }.
 */
export function computeMatchScores(
  features: readonly MatchScoreFeature[],
  prefs: MatchPreferences,
): Map<number, MatchResult> {
  const base = features.map(extractBaseMetrics);

  const normVenue = minMax(base.map((b) => b.venueDensity));
  const normDaily = minMax(base.map((b) => b.dailyDensity));
  const normPop = minMax(base.map((b) => b.popDensity));
  const normFamily = minMax(base.map((b) => b.family));
  const normYoung = minMax(base.map((b) => b.youngSocial));
  const normGrowth = minMax(base.map((b) => b.growth));
  const normConstruction = minMax(base.map((b) => b.constructionDensity));

  const results = new Map<number, MatchResult>();

  features.forEach((feature, i) => {
    const contributions: Record<MatchDimension, number> = {
      nightlife: normVenue[i],
      dailyNeeds: normDaily[i],
      // "calm" is an honest proxy: inverse of combined venue + population density.
      calm: 1 - (0.5 * normVenue[i] + 0.5 * normPop[i]),
      family: normFamily[i],
      youngSocial: normYoung[i],
      upAndComing: 0.5 * normGrowth[i] + 0.5 * normConstruction[i],
    };
    results.set(feature.properties.quartier_id, {
      score: weightedScore(contributions, prefs),
      contributions,
    });
  });

  return results;
}

/** Weighted mean of dimension values × 100, rounded. Null when all weights 0. */
function weightedScore(
  contributions: Record<MatchDimension, number>,
  prefs: MatchPreferences,
): number | null {
  let weightSum = 0;
  let valueSum = 0;
  for (const dim of MATCH_DIMENSIONS) {
    const weight = prefs.weights[dim];
    if (weight > 0) {
      weightSum += weight;
      valueSum += weight * contributions[dim];
    }
  }
  if (weightSum === 0) return null;
  return Math.round((valueSum / weightSum) * 100);
}

export interface MatchExplanation {
  /** Short labels of the strongest dimensions (weight > 0), strongest first. */
  strong: string[];
  /** Short labels of the weakest dimensions (weight > 0), weakest first. */
  weak: string[];
}

/**
 * Surface the top-2 strongest and bottom-2 weakest dimensions among those the
 * user cares about (weight > 0). Strong and weak never overlap.
 */
export function explainMatch(
  contributions: Record<MatchDimension, number>,
  prefs: MatchPreferences,
): MatchExplanation {
  const active = MATCH_DIMENSIONS.filter((dim) => prefs.weights[dim] > 0).sort(
    (a, b) => contributions[b] - contributions[a],
  );

  const strong = active.slice(0, 2);
  // Start weak after the strong slice so the two sets never overlap.
  const weak = active.slice(Math.max(2, active.length - 2)).reverse();

  return {
    strong: strong.map((dim) => DIMENSION_SHORT_LABELS[dim]),
    weak: weak.map((dim) => DIMENSION_SHORT_LABELS[dim]),
  };
}
