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

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? '';

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
