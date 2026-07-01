/**
 * Air-quality level coloring for the station point layer.
 *
 * Uses Strata's functional palette (see globals.css):
 *   good     -> sage green  (#8FA071)
 *   moderate -> amber       (#D4915A)
 *   high     -> terracotta  (#C4785B)
 *   missing  -> neutral muted (#8A8580)
 */
export type AirLevel = 'good' | 'moderate' | 'high';

export interface AirLevelSwatch {
  level: AirLevel;
  label: string;
  color: string;
}

/** Neutral fallback for stations without a resolved overall level. */
export const AIR_NEUTRAL_COLOR = '#8A8580';

/** Severity-ordered levels used by the legend and the color lookup. */
export const AIR_LEVELS: AirLevelSwatch[] = [
  { level: 'good', label: 'Good', color: '#8FA071' },
  { level: 'moderate', label: 'Moderate', color: '#D4915A' },
  { level: 'high', label: 'High', color: '#C4785B' },
];

const LEVEL_COLOR: Record<AirLevel, string> = {
  good: AIR_LEVELS[0].color,
  moderate: AIR_LEVELS[1].color,
  high: AIR_LEVELS[2].color,
};

/** Pure level → color, with a neutral fallback for missing/unknown levels. */
export function airLevelColor(level: string | null | undefined): string {
  if (level === 'good' || level === 'moderate' || level === 'high') {
    return LEVEL_COLOR[level];
  }
  return AIR_NEUTRAL_COLOR;
}

/**
 * MapLibre circle-color expression keyed on the `level` feature property.
 * `match` falls through to the neutral color when the level is absent/null
 * or not one of the three known values.
 */
export function airCircleColor(): unknown[] {
  return [
    'match',
    ['get', 'level'],
    'good', LEVEL_COLOR.good,
    'moderate', LEVEL_COLOR.moderate,
    'high', LEVEL_COLOR.high,
    AIR_NEUTRAL_COLOR,
  ];
}
