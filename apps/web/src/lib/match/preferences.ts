/**
 * Personalized match preferences — persisted client-side in localStorage.
 *
 * A preference is a per-dimension weight in the range 0..2:
 *   0 = don't care · 1 = matters · 2 = very important.
 *
 * Nothing here touches the DOM directly beyond guarded localStorage access,
 * and every read validates untrusted stored data before use.
 */

export const MATCH_DIMENSIONS = [
  'nightlife',
  'dailyNeeds',
  'calm',
  'family',
  'youngSocial',
  'upAndComing',
] as const;

export type MatchDimension = (typeof MATCH_DIMENSIONS)[number];

/** Human-readable panel labels for each dimension. */
export const DIMENSION_LABELS: Record<MatchDimension, string> = {
  nightlife: 'Nightlife & cafés',
  dailyNeeds: 'Daily needs',
  calm: 'Calm',
  family: 'Family-friendly',
  youngSocial: 'Young & social',
  upAndComing: 'Up-and-coming',
};

/** Short labels used in explanation chips ("strong on nightlife"). */
export const DIMENSION_SHORT_LABELS: Record<MatchDimension, string> = {
  nightlife: 'nightlife',
  dailyNeeds: 'daily needs',
  calm: 'calm',
  family: 'family',
  youngSocial: 'young & social',
  upAndComing: 'up-and-coming',
};

export const MIN_WEIGHT = 0;
export const MAX_WEIGHT = 2;
export const DEFAULT_WEIGHT = 1;

export interface MatchPreferences {
  weights: Record<MatchDimension, number>;
}

export const DEFAULT_PREFERENCES: MatchPreferences = {
  weights: {
    nightlife: DEFAULT_WEIGHT,
    dailyNeeds: DEFAULT_WEIGHT,
    calm: DEFAULT_WEIGHT,
    family: DEFAULT_WEIGHT,
    youngSocial: DEFAULT_WEIGHT,
    upAndComing: DEFAULT_WEIGHT,
  },
};

const STORAGE_KEY = 'strata.match.preferences.v1';

/** Coerce an untrusted value into a valid weight, falling back to the default. */
function sanitizeWeight(value: unknown): number {
  if (typeof value !== 'number' || !Number.isFinite(value)) return DEFAULT_WEIGHT;
  return Math.min(MAX_WEIGHT, Math.max(MIN_WEIGHT, value));
}

/** Merge an untrusted object with defaults — never trust stored data. */
function mergeWithDefaults(raw: unknown): MatchPreferences {
  const source =
    raw && typeof raw === 'object' && 'weights' in raw
      ? (raw as { weights?: unknown }).weights
      : undefined;
  const weightsSource =
    source && typeof source === 'object' ? (source as Record<string, unknown>) : {};

  const weights = {} as Record<MatchDimension, number>;
  for (const dim of MATCH_DIMENSIONS) {
    weights[dim] = sanitizeWeight(weightsSource[dim]);
  }
  return { weights };
}

/** Load preferences from localStorage, falling back to defaults on any error. */
export function loadPreferences(): MatchPreferences {
  if (typeof window === 'undefined') return DEFAULT_PREFERENCES;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULT_PREFERENCES;
    return mergeWithDefaults(JSON.parse(raw));
  } catch {
    return DEFAULT_PREFERENCES;
  }
}

/** Persist preferences to localStorage. No-op during SSR or on storage errors. */
export function savePreferences(prefs: MatchPreferences): void {
  if (typeof window === 'undefined') return;
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs));
  } catch {
    // Storage may be unavailable (private mode, quota) — ignore silently.
  }
}

/** True when at least one dimension has a non-zero weight. */
export function hasActivePreferences(prefs: MatchPreferences): boolean {
  return MATCH_DIMENSIONS.some((dim) => prefs.weights[dim] > 0);
}
