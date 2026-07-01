import { describe, it, expect } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import { AirQualityPopup, parseAirStation, type AirStation } from './AirQualityPopup';

const station: AirStation = {
  station: 'Heubeeribüel',
  name: 'Zürich Heubeeribüel',
  level: 'moderate',
  measured_at: '2026-07-01T21:00:00+01:00',
  parameters: {
    NO2: { latest: 4.35, mean_24h: 4.852, unit: 'µg/m3', level: 'good' },
    O3: { latest: 90.63, mean_24h: 92.7, unit: 'µg/m3', level: 'moderate' },
    'PM2.5': { latest: 2.28, mean_24h: 3.239, unit: 'µg/m3', level: 'good' },
  },
};

describe('AirQualityPopup', () => {
  it('renders the station name', () => {
    render(<AirQualityPopup station={station} />);
    expect(screen.getByText(/Zürich Heubeeribüel/)).toBeTruthy();
  });

  it('shows the overall level label', () => {
    render(<AirQualityPopup station={station} />);
    expect(screen.getByTestId('air-level')).toBeTruthy();
    expect(screen.getByTestId('air-level').textContent).toMatch(/moderate/i);
  });

  it('renders a row per parameter', () => {
    render(<AirQualityPopup station={station} />);
    const rows = screen.getAllByTestId('air-param-row');
    expect(rows.length).toBe(3);
  });

  it('shows the latest value with its unit', () => {
    render(<AirQualityPopup station={station} />);
    const rows = screen.getAllByTestId('air-param-row');
    const no2 = rows.find((r) => within(r).queryByText('NO2'));
    expect(no2).toBeTruthy();
    expect(no2!.textContent).toContain('µg/m3');
    // 4.35 -> "4.3" via toFixed(1) (IEEE-754 rounding)
    expect(no2!.textContent).toContain('4.3');
  });

  it('shows the 24h mean, rounded', () => {
    render(<AirQualityPopup station={station} />);
    const rows = screen.getAllByTestId('air-param-row');
    const o3 = rows.find((r) => within(r).queryByText('O3'));
    // mean_24h 92.7 -> 92.7
    expect(o3!.textContent).toContain('92.7');
  });

  it('renders the measured_at timestamp region', () => {
    render(<AirQualityPopup station={station} />);
    expect(screen.getByTestId('air-measured-at')).toBeTruthy();
  });

  it('falls back to station when name is absent', () => {
    const noName: AirStation = { ...station, name: undefined };
    render(<AirQualityPopup station={noName} />);
    expect(screen.getByText(/Heubeeribüel/)).toBeTruthy();
  });

  it('handles a missing overall level gracefully', () => {
    const noLevel: AirStation = { ...station, level: null };
    render(<AirQualityPopup station={noLevel} />);
    expect(screen.getByTestId('air-level')).toBeTruthy();
  });
});

describe('parseAirStation', () => {
  it('returns null for null/empty properties', () => {
    expect(parseAirStation(null)).toBeNull();
    expect(parseAirStation({})).toBeNull();
  });

  it('parses a JSON-stringified parameters object (MapLibre serialization)', () => {
    const parsed = parseAirStation({
      station: 'Schimmelstrasse',
      name: 'Zürich Schimmelstrasse',
      level: 'moderate',
      measured_at: '2026-07-01T21:00:00+01:00',
      parameters: JSON.stringify({
        O3: { latest: 69.34, mean_24h: 77.858, unit: 'µg/m3', level: 'moderate' },
      }),
    });
    expect(parsed).not.toBeNull();
    expect(parsed!.name).toBe('Zürich Schimmelstrasse');
    expect(parsed!.parameters.O3.latest).toBe(69.34);
  });

  it('tolerates unparseable parameters by returning an empty object', () => {
    const parsed = parseAirStation({ station: 'X', parameters: '{not json' });
    expect(parsed).not.toBeNull();
    expect(parsed!.parameters).toEqual({});
  });

  it('accepts an already-parsed parameters object', () => {
    const parsed = parseAirStation({
      station: 'X',
      parameters: { NO2: { latest: 1, mean_24h: 2, unit: 'µg/m3', level: 'good' } },
    });
    expect(parsed!.parameters.NO2.unit).toBe('µg/m3');
  });
});
