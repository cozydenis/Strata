import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QuartierProfile } from './QuartierProfile';

const fullProfile = {
  quartier_id: 11,
  quartier_name: 'Rathaus',
  kreis: 1,
  population: {
    total: 4200,
    density_per_km2: 8400,
    swiss_pct: 65.5,
    foreign_pct: 34.5,
    growth_rate: 1.2,
    trend: 'growing' as const,
  },
  age_distribution: [
    { bucket: '0-17', pct: 12 },
    { bucket: '18-29', pct: 22 },
    { bucket: '30-44', pct: 35 },
    { bucket: '45-64', pct: 21 },
    { bucket: '65+', pct: 10 },
  ],
};

const nullPopulationProfile = {
  quartier_id: 12,
  quartier_name: 'Hochschulen',
  kreis: 1,
  population: null,
  age_distribution: [],
};

describe('QuartierProfile', () => {
  it('renders without crashing', () => {
    render(<QuartierProfile profile={fullProfile} />);
  });

  it('displays quartier name', () => {
    render(<QuartierProfile profile={fullProfile} />);
    expect(screen.getByText('Rathaus')).toBeTruthy();
  });

  it('displays kreis', () => {
    render(<QuartierProfile profile={fullProfile} />);
    expect(screen.getByText(/kreis 1/i)).toBeTruthy();
  });

  it('displays total population', () => {
    render(<QuartierProfile profile={fullProfile} />);
    expect(screen.getByText(/4[,.]?200/)).toBeTruthy();
  });

  it('displays population density', () => {
    render(<QuartierProfile profile={fullProfile} />);
    expect(screen.getByText(/8[,.]?400/)).toBeTruthy();
  });

  it('displays swiss_pct', () => {
    render(<QuartierProfile profile={fullProfile} />);
    expect(screen.getByText(/65\.5%/)).toBeTruthy();
  });

  it('displays foreign_pct', () => {
    render(<QuartierProfile profile={fullProfile} />);
    expect(screen.getByText(/34\.5%/)).toBeTruthy();
  });

  it('displays trend as "growing"', () => {
    render(<QuartierProfile profile={fullProfile} />);
    expect(screen.getByText(/growing/i)).toBeTruthy();
  });

  it('renders age distribution chart', () => {
    render(<QuartierProfile profile={fullProfile} />);
    expect(screen.getAllByTestId('bar-segment').length).toBe(5);
  });

  it('renders null population gracefully', () => {
    render(<QuartierProfile profile={nullPopulationProfile} />);
    expect(screen.getByText('Hochschulen')).toBeTruthy();
  });

  it('shows "No data" or similar when population is null', () => {
    render(<QuartierProfile profile={nullPopulationProfile} />);
    expect(screen.getByText(/no data/i)).toBeTruthy();
  });

  it('renders growth_rate value', () => {
    render(<QuartierProfile profile={fullProfile} />);
    expect(screen.getByText(/1\.2/)).toBeTruthy();
  });

  it('applies glass card styling', () => {
    const { container } = render(<QuartierProfile profile={fullProfile} />);
    const card = container.firstChild as HTMLElement;
    expect(card.className).toContain('backdrop-blur');
  });
});
