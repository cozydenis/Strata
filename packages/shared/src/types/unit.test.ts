import { describe, it, expect } from 'vitest';
import type { Unit, Coordinates, BuildingType } from './unit';

describe('Unit type', () => {
  it('accepts a fully-populated valid Unit object', () => {
    const coords: Coordinates = { lat: 47.3769, lng: 8.5417 };

    const unit: Unit = {
      buildingId: 123456789,
      unitId: 987654321,
      floor: 3,
      roomCount: 4,
      areaM2: 95.5,
      constructionYear: 1975,
      buildingType: 'residential',
      coordinates: coords,
      verwaltung: 'Wincasa AG',
    };

    expect(unit.buildingId).toBe(123456789);
    expect(unit.unitId).toBe(987654321);
    expect(unit.floor).toBe(3);
    expect(unit.roomCount).toBe(4);
    expect(unit.areaM2).toBe(95.5);
    expect(unit.constructionYear).toBe(1975);
    expect(unit.buildingType).toBe('residential');
    expect(unit.coordinates.lat).toBe(47.3769);
    expect(unit.coordinates.lng).toBe(8.5417);
    expect(unit.verwaltung).toBe('Wincasa AG');
  });

  it('accepts a Unit with all nullable fields set to null', () => {
    const unit: Unit = {
      buildingId: 100000001,
      unitId: 200000001,
      floor: null,
      roomCount: null,
      areaM2: null,
      constructionYear: null,
      buildingType: 'cooperative',
      coordinates: { lat: 47.4, lng: 8.5 },
      verwaltung: null,
    };

    expect(unit.floor).toBeNull();
    expect(unit.roomCount).toBeNull();
    expect(unit.areaM2).toBeNull();
    expect(unit.constructionYear).toBeNull();
    expect(unit.verwaltung).toBeNull();
  });

  it('accepts all valid BuildingType values', () => {
    const types: BuildingType[] = ['residential', 'mixed_use', 'cooperative', 'commercial'];
    const base = {
      buildingId: 1,
      unitId: 1,
      floor: null,
      roomCount: null,
      areaM2: null,
      constructionYear: null,
      coordinates: { lat: 0, lng: 0 },
      verwaltung: null,
    };

    for (const buildingType of types) {
      const unit: Unit = { ...base, buildingType };
      expect(unit.buildingType).toBe(buildingType);
    }
  });

  it('Coordinates holds numeric lat and lng', () => {
    const coords: Coordinates = { lat: 47.3769, lng: 8.5417 };
    expect(typeof coords.lat).toBe('number');
    expect(typeof coords.lng).toBe('number');
  });

  it('buildingId and unitId are numbers (EGID / EWID)', () => {
    const unit: Unit = {
      buildingId: 490123456,
      unitId: 1,
      floor: 1,
      roomCount: 2,
      areaM2: 60,
      constructionYear: 2000,
      buildingType: 'mixed_use',
      coordinates: { lat: 47.3, lng: 8.5 },
      verwaltung: null,
    };

    expect(typeof unit.buildingId).toBe('number');
    expect(typeof unit.unitId).toBe('number');
  });
});
