import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';

const baseProfile = {
  quartier_id: 1,
  quartier_name: 'Rathaus',
  kreis: 1,
  population: {
    total: 5000,
    density_per_km2: 12000,
    swiss_pct: 75,
    foreign_pct: 25,
    growth_rate: 1.2,
    trend: 'growing' as const,
  },
  age_distribution: [],
};

describe('QuartierProfile commute_hb_min display', () => {
  it('shows commute time row when commute_hb_min is a number', async () => {
    const { QuartierProfile } = await import('./QuartierProfile');
    const { getByTestId } = render(
      <QuartierProfile
        profile={{ ...baseProfile, commute_hb_min: 12 }}
        onClose={() => {}}
      />
    );
    const row = getByTestId('commute-hb-row');
    expect(row).toBeTruthy();
    expect(row.textContent).toContain('12');
  });

  it('shows "min" unit in commute row', async () => {
    const { QuartierProfile } = await import('./QuartierProfile');
    const { getByTestId } = render(
      <QuartierProfile
        profile={{ ...baseProfile, commute_hb_min: 18 }}
        onClose={() => {}}
      />
    );
    const row = getByTestId('commute-hb-row');
    expect(row.textContent).toContain('min');
  });

  it('does NOT show commute row when commute_hb_min is null', async () => {
    const { QuartierProfile } = await import('./QuartierProfile');
    const { queryByTestId } = render(
      <QuartierProfile
        profile={{ ...baseProfile, commute_hb_min: null }}
        onClose={() => {}}
      />
    );
    expect(queryByTestId('commute-hb-row')).toBeNull();
  });

  it('does NOT show commute row when commute_hb_min is undefined', async () => {
    const { QuartierProfile } = await import('./QuartierProfile');
    // Cast to allow undefined for legacy data compatibility test
    const profile = { ...baseProfile } as typeof baseProfile & { commute_hb_min?: number | null };
    const { queryByTestId } = render(
      <QuartierProfile
        profile={profile}
        onClose={() => {}}
      />
    );
    expect(queryByTestId('commute-hb-row')).toBeNull();
  });

  it('shows "To Zürich HB" label in commute row', async () => {
    const { QuartierProfile } = await import('./QuartierProfile');
    const { getByTestId } = render(
      <QuartierProfile
        profile={{ ...baseProfile, commute_hb_min: 22 }}
        onClose={() => {}}
      />
    );
    const row = getByTestId('commute-hb-row');
    expect(row.textContent).toContain('HB');
  });
});
