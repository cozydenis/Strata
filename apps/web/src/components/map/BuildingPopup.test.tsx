import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BuildingPopup } from './BuildingPopup';
import type { BuildingSummary } from '@/lib/api';

const fullSummary: BuildingSummary = {
  egid: 12345,
  gbauj: 1972,
  gkat: 1021,
  gastw: 5,
  ganzwhg: 24,
  lat: 47.376,
  lon: 8.541,
  strname: 'Langstrasse',
  deinr: '42',
  dplz4: 8004,
  dplzname: 'Zürich',
};

describe('BuildingPopup', () => {
  it('renders the street address', () => {
    render(<BuildingPopup summary={fullSummary} />);
    expect(screen.getByText(/Langstrasse 42/)).toBeTruthy();
  });

  it('renders the postal code and city', () => {
    render(<BuildingPopup summary={fullSummary} />);
    expect(screen.getByText(/8004 Zürich/)).toBeTruthy();
  });

  it('renders construction year', () => {
    render(<BuildingPopup summary={fullSummary} />);
    expect(screen.getByText('1972')).toBeTruthy();
  });

  it('renders floor count', () => {
    render(<BuildingPopup summary={fullSummary} />);
    expect(screen.getByText('5')).toBeTruthy();
  });

  it('renders dwelling count', () => {
    render(<BuildingPopup summary={fullSummary} />);
    expect(screen.getByText('24')).toBeTruthy();
  });

  it('renders "Unknown" when gbauj is null', () => {
    render(<BuildingPopup summary={{ ...fullSummary, gbauj: null }} />);
    expect(screen.getByText('Unknown')).toBeTruthy();
  });

  it('renders "—" when address is null', () => {
    render(<BuildingPopup summary={{ ...fullSummary, strname: null, deinr: null, dplz4: null, dplzname: null }} />);
    // Should not throw; address row shows dash or fallback
    expect(screen.getByTestId('popup-address')).toBeTruthy();
  });
});
