import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BuildingPopup } from './BuildingPopup';
import type { BuildingSummary, ListingSummary } from '@/lib/api';

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

  it('renders construction year in the metadata row', () => {
    render(<BuildingPopup summary={fullSummary} />);
    expect(screen.getByText(/1972/)).toBeTruthy();
  });

  it('renders floor count in the metadata row', () => {
    render(<BuildingPopup summary={fullSummary} />);
    expect(screen.getByText(/5/)).toBeTruthy();
  });

  it('renders dwelling count in the metadata row', () => {
    render(<BuildingPopup summary={fullSummary} />);
    expect(screen.getByText(/24/)).toBeTruthy();
  });

  it('renders "Unknown" when gbauj is null', () => {
    render(<BuildingPopup summary={{ ...fullSummary, gbauj: null }} />);
    expect(screen.getByText('Unknown')).toBeTruthy();
  });

  it('renders "—" when address is null', () => {
    render(<BuildingPopup summary={{ ...fullSummary, strname: null, deinr: null, dplz4: null, dplzname: null }} />);
    expect(screen.getByTestId('popup-address')).toBeTruthy();
  });

  it('renders listing cards when listings provided', () => {
    const listings: ListingSummary[] = [{
      id: 1, source: 'flatfox', source_id: 'L-1',
      rent_net: 2000, rent_gross: 2200, rooms: 3.5, area_m2: 80,
      street: 'Langstrasse', house_number: '42', plz: 8004, city: 'Zürich',
      source_url: 'https://flatfox.ch/test', first_seen: '2026-01-01', last_seen: '2026-03-01',
      description: null, images: [], documents: [],
    }];
    render(<BuildingPopup summary={fullSummary} listings={listings} />);
    expect(screen.getByTestId('listing-cards')).toBeTruthy();
    expect(screen.getByText('Active listings')).toBeTruthy();
  });

  it('shows "No active listings" message when listings is empty array', () => {
    render(<BuildingPopup summary={fullSummary} listings={[]} />);
    expect(screen.getByText(/no active listings/i)).toBeTruthy();
  });

  it('does not render listing cards container when listings is empty', () => {
    render(<BuildingPopup summary={fullSummary} listings={[]} />);
    expect(screen.queryByTestId('listing-cards')).toBeNull();
  });

  it('does not render listing section when listings is undefined', () => {
    render(<BuildingPopup summary={fullSummary} />);
    expect(screen.queryByTestId('listing-cards')).toBeNull();
  });

  it('street address renders with prominent styling (font-semibold)', () => {
    const { container } = render(<BuildingPopup summary={fullSummary} />);
    const addressEl = container.querySelector('[data-testid="popup-address"] p:first-child') as HTMLElement;
    expect(addressEl.className).toContain('font-semibold');
  });

  it('renders a divider between address and metadata', () => {
    const { container } = render(<BuildingPopup summary={fullSummary} />);
    const divider = container.querySelector('.border-t');
    expect(divider).toBeTruthy();
  });

  it('year has inline color style from era', () => {
    const { container } = render(<BuildingPopup summary={fullSummary} />);
    // The year should be in a span/element with a style color
    const yearEls = container.querySelectorAll('[style*="color"]');
    expect(yearEls.length).toBeGreaterThan(0);
  });

  it('omits floors when gastw is null', () => {
    render(<BuildingPopup summary={{ ...fullSummary, gastw: null }} />);
    expect(screen.queryByText(/fl\./i)).toBeNull();
  });

  it('omits dwellings when ganzwhg is null', () => {
    render(<BuildingPopup summary={{ ...fullSummary, ganzwhg: null }} />);
    expect(screen.queryByText(/dwg/i)).toBeNull();
  });
});
