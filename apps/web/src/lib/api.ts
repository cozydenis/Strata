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

export interface QuartierProfile {
  quartier_id: number;
  quartier_name: string;
  kreis: number;
  population: QuartierPopulation | null;
  age_distribution: AgeBucket[];
}

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
