import type { QuartierAmenities } from '@/lib/api';

/** Round to one decimal for display — API values can carry full float precision. */
export function fmtPct(value: number): string {
  return `${Number(value.toFixed(1))}%`;
}

export const AMENITY_LABELS: { key: keyof QuartierAmenities; label: string }[] = [
  { key: 'groceries', label: 'Groceries' },
  { key: 'cafes', label: 'Cafés' },
  { key: 'restaurants', label: 'Restaurants' },
  { key: 'bars', label: 'Bars & pubs' },
  { key: 'pharmacies', label: 'Pharmacies' },
  { key: 'schools', label: 'Schools' },
  { key: 'fitness', label: 'Fitness' },
  { key: 'clubs', label: 'Clubs' },
  { key: 'culture', label: 'Culture' },
  { key: 'music_venues', label: 'Live music' },
];
