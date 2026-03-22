export interface Coordinates {
  lat: number;
  lng: number;
}

export type BuildingType = 'residential' | 'mixed_use' | 'cooperative' | 'commercial';

export interface Unit {
  buildingId: number; // EGID
  unitId: number; // EWID
  floor: number | null;
  roomCount: number | null;
  areaM2: number | null;
  constructionYear: number | null;
  buildingType: BuildingType;
  coordinates: Coordinates;
  verwaltung: string | null;
}
