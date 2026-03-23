export interface Era {
  label: string;
  color: string;
  minYear?: number;
  maxYear?: number;
}

export const ERA_COLORS: Era[] = [
  { label: 'Unknown', color: '#8A8580' },
  { label: 'Pre-1900', color: '#7A5C4F', maxYear: 1899 },
  { label: '1900–1945', color: '#A67C5B', minYear: 1900, maxYear: 1945 },
  { label: '1946–1970', color: '#C4A35A', minYear: 1946, maxYear: 1970 },
  { label: '1971–1990', color: '#7A9A6D', minYear: 1971, maxYear: 1990 },
  { label: '1991–2010', color: '#5A7D8A', minYear: 1991, maxYear: 2010 },
  { label: '2011+', color: '#3D5A6E', minYear: 2011 },
];

const UNKNOWN_ERA = ERA_COLORS[0];

export function eraForYear(year: number | null | undefined): Era {
  if (year == null) return UNKNOWN_ERA;
  for (const era of ERA_COLORS) {
    if (era.minYear === undefined && era.maxYear === undefined) continue;
    const aboveMin = era.minYear === undefined || year >= era.minYear;
    const belowMax = era.maxYear === undefined || year <= era.maxYear;
    if (aboveMin && belowMax) return era;
  }
  return UNKNOWN_ERA;
}

const PRE1900_ERA = ERA_COLORS.find((e) => e.label === 'Pre-1900')!;

export function eraColorExpression(): unknown[] {
  // Eras with minYear defined, sorted ascending
  const eras = ERA_COLORS.filter((e) => e.minYear !== undefined);
  const sorted = [...eras].sort((a, b) => (a.minYear ?? 0) - (b.minYear ?? 0));

  // MapLibre step: ['step', input, fallback, stop1, color1, stop2, color2, ...]
  // - null gbauj coalesces to 0 → falls through to fallback (Unknown gray)
  // - real years >= 1 get Pre-1900 color until the first stop overrides it
  const expr: unknown[] = [
    'step',
    ['coalesce', ['get', 'gbauj'], 0],
    UNKNOWN_ERA.color,  // fallback for 0 (null sentinel)
    1,                  // any real year >= 1 → Pre-1900
    PRE1900_ERA.color,
  ];
  for (const era of sorted) {
    expr.push(era.minYear);
    expr.push(era.color);
  }
  return expr;
}
