/**
 * MapLibre color expression for noise cadastre point layer.
 *
 * Thresholds (daytime dB):
 *   < 50 dB  -> #4ade80 (quiet, green)
 *   50-60 dB -> #facc15 (moderate, yellow)
 *   60-70 dB -> #fb923c (loud, orange)
 *   > 70 dB  -> #ef4444 (very loud, red)
 */
export function noiseLineColor(): unknown[] {
  return [
    'step',
    ['coalesce', ['get', 'd'], 0],
    '#4ade80', // fallback / < 50 dB: quiet
    50, '#facc15', // 50-60 dB: moderate
    60, '#fb923c', // 60-70 dB: loud
    70, '#ef4444', // > 70 dB: very loud
  ];
}
