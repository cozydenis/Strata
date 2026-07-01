import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QuartierProfile } from './QuartierProfile';

const fullProfile = {
  quartier_id: 11,
  quartier_name: 'Rathaus',
  kreis: 1,
  commute_hb_min: null,
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
  commute_hb_min: null,
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
    expect(card.className).toContain('strata-panel');
  });
});

describe('QuartierProfile amenities', () => {
  const amenities = {
    groceries: 8,
    cafes: 21,
    restaurants: 34,
    bars: 12,
    pharmacies: 4,
    schools: 6,
    fitness: 5,
    total: 90,
    per_km2: 18.4,
  };

  it('renders amenity counts when present', () => {
    render(<QuartierProfile profile={{ ...fullProfile, amenities }} />);
    expect(screen.getByTestId('amenities-section')).toBeTruthy();
    expect(screen.getByText('Groceries')).toBeTruthy();
    expect(screen.getByText('21')).toBeTruthy();
    expect(screen.getByText('Bars & pubs')).toBeTruthy();
  });

  it('renders amenity density per km2', () => {
    render(<QuartierProfile profile={{ ...fullProfile, amenities }} />);
    expect(screen.getByTestId('amenity-density').textContent).toContain('18.4');
  });

  it('hides density line when per_km2 is null', () => {
    render(
      <QuartierProfile profile={{ ...fullProfile, amenities: { ...amenities, per_km2: null } }} />,
    );
    expect(screen.queryByTestId('amenity-density')).toBeNull();
  });

  it('omits section when amenities are absent', () => {
    render(<QuartierProfile profile={fullProfile} />);
    expect(screen.queryByTestId('amenities-section')).toBeNull();
  });
});

describe('QuartierProfile match score', () => {
  const match = { score: 72, strong: ['nightlife', 'young & social'], weak: ['calm'] };

  it('renders "Your match: N%" when a score is provided', () => {
    render(<QuartierProfile profile={fullProfile} match={match} />);
    expect(screen.getByTestId('match-score')).toBeTruthy();
    expect(screen.getByTestId('match-score').textContent).toContain('72%');
  });

  it('renders strong and weak explanation chips', () => {
    render(<QuartierProfile profile={fullProfile} match={match} />);
    expect(screen.getByText(/strong on nightlife/i)).toBeTruthy();
    expect(screen.getByText(/weak on calm/i)).toBeTruthy();
  });

  it('omits the match line when no match prop is given', () => {
    render(<QuartierProfile profile={fullProfile} />);
    expect(screen.queryByTestId('match-score')).toBeNull();
  });

  it('omits the match line when the score is null', () => {
    render(<QuartierProfile profile={fullProfile} match={{ score: null, strong: [], weak: [] }} />);
    expect(screen.queryByTestId('match-score')).toBeNull();
  });
});

describe('QuartierProfile compare button', () => {
  it('renders compare button and fires onCompare', async () => {
    const { fireEvent } = await import('@testing-library/react');
    const onCompare = vi.fn();
    render(<QuartierProfile profile={fullProfile} onCompare={onCompare} />);
    const btn = screen.getByTestId('compare-button');
    fireEvent.click(btn);
    expect(onCompare).toHaveBeenCalledOnce();
  });

  it('omits compare button when onCompare is not provided', () => {
    render(<QuartierProfile profile={fullProfile} />);
    expect(screen.queryByTestId('compare-button')).toBeNull();
  });
});

describe('QuartierProfile vibe', () => {
  const vibe = {
    tags: [
      { tag: 'young crowd', evidence: '35% aged 18–29 — top quartile in Zürich' },
      { tag: 'nightlife hub', evidence: '47 bars & restaurants per km² — top quartile in Zürich' },
    ],
    summary: 'A young crowd, buzzing bars and restaurants.',
  };

  it('renders vibe tags with evidence tooltips', () => {
    render(<QuartierProfile profile={{ ...fullProfile, vibe }} />);
    const tags = screen.getAllByTestId('vibe-tag');
    expect(tags).toHaveLength(2);
    expect(screen.getByText('young crowd')).toBeTruthy();
    expect(tags[0].getAttribute('title')).toContain('top quartile');
  });

  it('renders the summary line', () => {
    render(<QuartierProfile profile={{ ...fullProfile, vibe }} />);
    expect(screen.getByTestId('vibe-summary').textContent).toBe(
      'A young crowd, buzzing bars and restaurants.',
    );
  });

  it('omits vibe section when absent', () => {
    render(<QuartierProfile profile={fullProfile} />);
    expect(screen.queryByTestId('vibe-section')).toBeNull();
  });
});

describe('QuartierProfile construction', () => {
  const construction = { year: 2025, approved_projects: 11, started_projects: 13, cost_mchf: 278.0 };

  it('renders construction pipeline rows', () => {
    render(<QuartierProfile profile={{ ...fullProfile, construction }} />);
    expect(screen.getByTestId('construction-section')).toBeTruthy();
    expect(screen.getByText(/New construction · 2025/)).toBeTruthy();
    expect(screen.getByText('11')).toBeTruthy();
    expect(screen.getByText('13')).toBeTruthy();
    expect(screen.getByText(/CHF 278 M/)).toBeTruthy();
  });

  it('hides investment row when cost is masked', () => {
    render(
      <QuartierProfile profile={{ ...fullProfile, construction: { ...construction, cost_mchf: null } }} />,
    );
    expect(screen.queryByText(/Investment/)).toBeNull();
  });

  it('omits section entirely with zero activity', () => {
    render(
      <QuartierProfile
        profile={{
          ...fullProfile,
          construction: { year: 2025, approved_projects: 0, started_projects: 0, cost_mchf: null },
        }}
      />,
    );
    expect(screen.queryByTestId('construction-section')).toBeNull();
  });

  it('omits section when construction absent', () => {
    render(<QuartierProfile profile={fullProfile} />);
    expect(screen.queryByTestId('construction-section')).toBeNull();
  });
});
