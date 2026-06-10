export interface BuildingSummary {
  egid: number;
  gbauj: number | null;
  gkat: number | null;
  gastw: number | null;
  ganzwhg: number | null;
  lat: number;
  lon: number;
  strname: string | null;
  deinr: string | null;
  dplz4: number | null;
  dplzname: string | null;
}

export interface ListingImage {
  id: number;
  url: string | null;
  local_path: string | null;
  caption: string | null;
  ordering: number;
  image_type: 'photo' | 'floorplan' | 'cover';
}

export interface ListingDocument {
  id: number;
  url: string | null;
  local_path: string | null;
  caption: string | null;
  doc_type: 'floorplan' | 'other';
}

export interface ListingSummary {
  id: number;
  source: string;
  source_id: string;
  rent_net: number | null;
  rent_gross: number | null;
  rooms: number | null;
  area_m2: number | null;
  street: string | null;
  house_number: string | null;
  plz: number | null;
  city: string | null;
  source_url: string | null;
  first_seen: string;
  last_seen: string;
  description: string | null;
  images: ListingImage[];
  documents: ListingDocument[];
}

export interface AgeBucket {
  bucket: string;
  pct: number;
}

export interface QuartierPopulation {
  total: number;
  density_per_km2: number | null;
  swiss_pct: number | null;
  foreign_pct: number | null;
  growth_rate: number | null;
  trend: 'growing' | 'stable' | 'declining';
}

export interface QuartierAmenities {
  groceries: number;
  cafes: number;
  restaurants: number;
  bars: number;
  pharmacies: number;
  schools: number;
  fitness: number;
  total: number;
  per_km2: number | null;
}

export interface QuartierProfile {
  quartier_id: number;
  quartier_name: string;
  kreis: number;
  population: QuartierPopulation | null;
  age_distribution: AgeBucket[];
  commute_hb_min: number | null;
  amenities?: QuartierAmenities | null;
}

export type CommuteDestination = 'hb' | 'eth' | 'airport' | 'technopark';

export const COMMUTE_DESTINATIONS: Record<CommuteDestination, string> = {
  hb: 'Zürich HB',
  eth: 'ETH Zentrum',
  airport: 'Flughafen',
  technopark: 'Technopark',
};

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? '';

/** Prefix a relative media path (e.g. /media/images/...) with the API base URL. */
export function mediaUrl(path: string | null): string | null {
  if (!path) return null;
  if (path.startsWith('http')) return path;
  return `${BASE_URL}${path}`;
}

export async function fetchBuildingSummary(egid: number): Promise<BuildingSummary> {
  const res = await fetch(`${BASE_URL}/registry/buildings/${egid}/summary`);
  if (!res.ok) {
    throw new Error(`${res.status}`);
  }
  const data: unknown = await res.json();
  if (typeof data !== 'object' || data === null || typeof (data as Record<string, unknown>).egid !== 'number') {
    throw new Error('Unexpected response shape: missing egid');
  }
  return data as BuildingSummary;
}

export async function fetchQuartierProfile(quartierId: number): Promise<QuartierProfile> {
  const res = await fetch(`${BASE_URL}/neighborhoods/${quartierId}/profile`);
  if (!res.ok) {
    throw new Error(`${res.status}`);
  }
  const data: unknown = await res.json();
  if (
    typeof data !== 'object' ||
    data === null ||
    typeof (data as Record<string, unknown>).quartier_id !== 'number'
  ) {
    throw new Error('Unexpected response shape: missing quartier_id');
  }
  return data as QuartierProfile;
}

export async function fetchCommuteIsochrone(
  destinationKey: CommuteDestination,
): Promise<{ type: string; features: unknown[] } | null> {
  const res = await fetch(`/data/commutes/${destinationKey}.geojson`);
  if (res.status === 404) return null;
  if (!res.ok) {
    throw new Error(`${res.status}`);
  }
  const data: unknown = await res.json();
  if (
    typeof data !== 'object' ||
    data === null ||
    (data as Record<string, unknown>).type !== 'FeatureCollection' ||
    !Array.isArray((data as Record<string, unknown>).features)
  ) {
    throw new Error('Unexpected response shape: not a FeatureCollection');
  }
  return data as { type: string; features: unknown[] };
}

export async function fetchBuildingListings(egid: number): Promise<ListingSummary[]> {
  const res = await fetch(`${BASE_URL}/registry/buildings/${egid}/listings`);
  if (!res.ok) {
    throw new Error(`${res.status}`);
  }
  const data: unknown = await res.json();
  if (
    typeof data !== 'object' ||
    data === null ||
    !Array.isArray((data as Record<string, unknown>).listings)
  ) {
    throw new Error('Unexpected response shape: missing listings');
  }
  return (data as { listings: ListingSummary[] }).listings;
}

// ── Units ─────────────────────────────────────────────────────────────────────

export interface UnitSummary {
  egid: number;
  ewid: number;
  wstwklang: string | null;
  wazim: number | null;
  warea: number | null;
}

export async function fetchBuildingUnits(egid: number): Promise<{ total: number; items: UnitSummary[] }> {
  const res = await fetch(`${BASE_URL}/registry/buildings/${egid}/units`);
  if (!res.ok) {
    throw new Error(`${res.status}`);
  }
  const data: unknown = await res.json();
  if (typeof data !== 'object' || data === null || !Array.isArray((data as Record<string, unknown>).items)) {
    throw new Error('Unexpected response shape: missing items');
  }
  return data as { total: number; items: UnitSummary[] };
}

// ── Watchlist (authenticated) ─────────────────────────────────────────────────

export interface WatchItem {
  id: number;
  egid: number;
  ewid: number | null;
  created_at: string;
  strname: string | null;
  deinr: string | null;
  dplz4: number | null;
  dplzname: string | null;
}

function authHeaders(token: string): Record<string, string> {
  return { Authorization: `Bearer ${token}` };
}

export async function fetchWatchlist(token: string): Promise<{ total: number; items: WatchItem[] }> {
  const res = await fetch(`${BASE_URL}/watchlist`, { headers: authHeaders(token) });
  if (!res.ok) {
    throw new Error(`${res.status}`);
  }
  const data: unknown = await res.json();
  if (typeof data !== 'object' || data === null || !Array.isArray((data as Record<string, unknown>).items)) {
    throw new Error('Unexpected response shape: missing items');
  }
  return data as { total: number; items: WatchItem[] };
}

export async function addWatch(token: string, egid: number, ewid?: number): Promise<WatchItem> {
  const res = await fetch(`${BASE_URL}/watchlist`, {
    method: 'POST',
    headers: { ...authHeaders(token), 'Content-Type': 'application/json' },
    body: JSON.stringify({ egid, ewid: ewid ?? null }),
  });
  if (!res.ok) {
    throw new Error(`${res.status}`);
  }
  return (await res.json()) as WatchItem;
}

export async function removeWatch(token: string, watchId: number): Promise<void> {
  const res = await fetch(`${BASE_URL}/watchlist/${watchId}`, {
    method: 'DELETE',
    headers: authHeaders(token),
  });
  if (!res.ok && res.status !== 204) {
    throw new Error(`${res.status}`);
  }
}

export type WatchEventType = 'new_listing' | 'price_change' | 'listing_gone';

export interface WatchEvent {
  type: WatchEventType;
  ts: string;
  listing_id: number;
  egid: number;
  street: string | null;
  house_number: string | null;
  plz: number | null;
  city: string | null;
  rent_gross: number | null;
  rooms: number | null;
  area_m2: number | null;
  source_url: string | null;
  old_value: string | null;
  new_value: string | null;
}

export async function fetchWatchEvents(token: string, days = 90): Promise<{ total: number; items: WatchEvent[] }> {
  const res = await fetch(`${BASE_URL}/watchlist/events?days=${days}`, { headers: authHeaders(token) });
  if (!res.ok) {
    throw new Error(`${res.status}`);
  }
  const data: unknown = await res.json();
  if (typeof data !== 'object' || data === null || !Array.isArray((data as Record<string, unknown>).items)) {
    throw new Error('Unexpected response shape: missing items');
  }
  return data as { total: number; items: WatchEvent[] };
}
