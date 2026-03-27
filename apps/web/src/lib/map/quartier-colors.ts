/**
 * MapLibre choropleth color expressions for Quartier demographic layers.
 * Each metric maps to a sequential color ramp using `step` expressions.
 */

type Metric = 'population_density' | 'foreign_pct' | 'age_avg' | 'growth_rate' | string;

// Perceptually-uniform palettes tuned for the dark-matter basemap (dark bg).
// Using Viridis/Plasma/Magma-inspired ramps — visible and distinct on dark gray.

// Population density: Viridis (purple → blue → green → yellow)
const DENSITY_STOPS: [number, string][] = [
  [0, '#440154'],
  [2000, '#31688e'],
  [5000, '#35b779'],
  [10000, '#90d743'],
  [20000, '#fde725'],
];

// Foreign %: Plasma (deep blue → magenta → orange → yellow)
const FOREIGN_PCT_STOPS: [number, string][] = [
  [0, '#0d0887'],
  [10, '#7e03a8'],
  [20, '#cc4778'],
  [30, '#f89540'],
  [40, '#f0f921'],
];

// Average age: Magma (purple → rose → peach → cream)
const AGE_AVG_STOPS: [number, string][] = [
  [0, '#3b0f70'],
  [30, '#8c2981'],
  [35, '#de4968'],
  [40, '#fe9f6d'],
  [45, '#fcfdbf'],
];

// Growth rate: diverging red–gray–green (vivid on dark bg)
const GROWTH_RATE_STOPS: [number, string][] = [
  [-5, '#d73027'],
  [-1, '#fc8d59'],
  [0, '#737373'],
  [1, '#69f0ae'],
  [3, '#00c853'],
];

function _stepExpression(
  property: string,
  stops: [number, string][],
): unknown[] {
  const [firstStop, ...rest] = stops;
  const expr: unknown[] = [
    'step',
    ['coalesce', ['get', property], firstStop[0]],
    firstStop[1], // fallback
  ];
  for (const [value, color] of rest) {
    expr.push(value, color);
  }
  return expr;
}

/**
 * Returns a MapLibre fill-color expression for a given demographic metric.
 *
 * Supported metrics:
 *   - "population_density" — residents per km2
 *   - "foreign_pct"        — percentage of foreign residents
 *   - "age_avg"            — average age proxy
 *   - "growth_rate"        — year-over-year growth rate
 *
 * Unknown metrics fall back to the population_density expression.
 */
export function quartierFillColor(metric: Metric): unknown[] {
  switch (metric) {
    case 'population_density':
      return _stepExpression('population_density', DENSITY_STOPS);
    case 'foreign_pct':
      return _stepExpression('foreign_pct', FOREIGN_PCT_STOPS);
    case 'age_avg':
      return _stepExpression('age_avg', AGE_AVG_STOPS);
    case 'growth_rate':
      return _stepExpression('growth_rate', GROWTH_RATE_STOPS);
    default:
      return _stepExpression('population_density', DENSITY_STOPS);
  }
}
