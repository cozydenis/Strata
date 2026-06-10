import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ComparisonPanel } from './ComparisonPanel';
import type { QuartierProfile } from '@/lib/api';

function makeProfile(overrides: Partial<QuartierProfile> = {}): QuartierProfile {
  return {
    quartier_id: 42,
    quartier_name: 'Langstrasse',
    kreis: 4,
    population: {
      total: 12000,
      density_per_km2: 14000,
      swiss_pct: 55.5,
      foreign_pct: 44.5,
      growth_rate: 1.2,
      trend: 'growing',
    },
    age_distribution: [
      { bucket: '0-17', pct: 10 },
      { bucket: '18-29', pct: 35 },
    ],
    commute_hb_min: null,
    amenities: {
      groceries: 29,
      cafes: 30,
      restaurants: 166,
      bars: 78,
      pharmacies: 5,
      schools: 20,
      fitness: 13,
      total: 341,
      per_km2: 282.5,
    },
    ...overrides,
  };
}

const left = makeProfile();
const right = makeProfile({
  quartier_id: 91,
  quartier_name: 'Albisrieden',
  kreis: 9,
  population: {
    total: 23000,
    density_per_km2: 6200,
    swiss_pct: 70,
    foreign_pct: 30,
    growth_rate: -0.4,
    trend: 'declining',
  },
  amenities: {
    groceries: 16,
    cafes: 4,
    restaurants: 18,
    bars: 3,
    pharmacies: 4,
    schools: 12,
    fitness: 8,
    total: 65,
    per_km2: 19.2,
  },
});

describe('ComparisonPanel', () => {
  it('renders both quartier names and kreise', () => {
    render(<ComparisonPanel left={left} right={right} onClose={() => {}} />);
    expect(screen.getByText('Langstrasse')).toBeTruthy();
    expect(screen.getByText('Albisrieden')).toBeTruthy();
    expect(screen.getByText(/kreis 4/i)).toBeTruthy();
    expect(screen.getByText(/kreis 9/i)).toBeTruthy();
  });

  it('renders population values for both sides', () => {
    render(<ComparisonPanel left={left} right={right} onClose={() => {}} />);
    expect(screen.getByText(/12[,.']?000/)).toBeTruthy();
    expect(screen.getByText(/23[,.']?000/)).toBeTruthy();
  });

  it('renders amenity counts for both sides', () => {
    render(<ComparisonPanel left={left} right={right} onClose={() => {}} />);
    expect(screen.getByTestId('comparison-amenities')).toBeTruthy();
    expect(screen.getByText('166')).toBeTruthy();
    expect(screen.getByText('18')).toBeTruthy();
  });

  it('renders paired age distribution bars', () => {
    render(<ComparisonPanel left={left} right={right} onClose={() => {}} />);
    expect(screen.getByTestId('comparison-ages')).toBeTruthy();
    expect(screen.getByText('0-17')).toBeTruthy();
  });

  it('renders trends with direction words', () => {
    render(<ComparisonPanel left={left} right={right} onClose={() => {}} />);
    expect(screen.getByText(/growing/)).toBeTruthy();
    expect(screen.getByText(/declining/)).toBeTruthy();
  });

  it('shows em-dash for missing population data', () => {
    render(
      <ComparisonPanel left={makeProfile({ population: null })} right={right} onClose={() => {}} />,
    );
    expect(screen.getAllByText('—').length).toBeGreaterThan(0);
  });

  it('omits amenities section when both sides lack amenities', () => {
    render(
      <ComparisonPanel
        left={makeProfile({ amenities: null })}
        right={{ ...right, amenities: null }}
        onClose={() => {}}
      />,
    );
    expect(screen.queryByTestId('comparison-amenities')).toBeNull();
  });

  it('omits commute row when both sides have no commute data', () => {
    render(<ComparisonPanel left={left} right={right} onClose={() => {}} />);
    expect(screen.queryByText(/To Zürich HB/)).toBeNull();
  });

  it('shows commute row when one side has data', () => {
    render(
      <ComparisonPanel left={{ ...left, commute_hb_min: 12 }} right={right} onClose={() => {}} />,
    );
    expect(screen.getByText(/To Zürich HB/)).toBeTruthy();
    expect(screen.getByText('12 min')).toBeTruthy();
  });

  it('calls onClose when the close button is clicked', () => {
    const onClose = vi.fn();
    render(<ComparisonPanel left={left} right={right} onClose={onClose} />);
    fireEvent.click(screen.getByTestId('comparison-close'));
    expect(onClose).toHaveBeenCalledOnce();
  });
});
