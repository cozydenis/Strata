// MapLibre step expression for commute time coloring
export const COMMUTE_MINUTES_EXPRESSION = [
  'step',
  ['get', 'contour_minutes'],
  '#1a9850',   // 0–10 min: green
  10, '#91cf60',  // 10–20: light green
  20, '#fee08b',  // 20–30: amber
  30, '#fc8d59',  // 30–45: orange
  45, '#d73027',  // 45+: red
] as const;

export const COMMUTE_OPACITY_EXPRESSION = [
  'step',
  ['get', 'contour_minutes'],
  0.5,   // 0–10 min
  10, 0.4,
  20, 0.3,
  30, 0.2,
  45, 0.1,
] as const;

export const COMMUTE_COLORS: Record<string, string> = {
  '0-10': '#1a9850',
  '10-20': '#91cf60',
  '20-30': '#fee08b',
  '30-45': '#fc8d59',
  '45+': '#d73027',
};
