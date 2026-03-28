import { describe, it, expect, vi } from 'vitest';
import { render, fireEvent } from '@testing-library/react';

// Mock @/lib/api to provide COMMUTE_DESTINATIONS without needing the full module
vi.mock('@/lib/api', () => ({
  COMMUTE_DESTINATIONS: {
    hb: 'Zürich HB',
    eth: 'ETH Zentrum',
    airport: 'Flughafen',
    technopark: 'Technopark',
  },
}));

const defaultProps = {
  buildingsVisible: true,
  listingsVisible: true,
  quartiereVisible: false,
  noiseVisible: false,
  activeMetric: 'population_density',
  onToggle: vi.fn(),
  onMetricChange: vi.fn(),
  commuteVisible: false,
  activeDestination: 'hb' as const,
  onCommuteToggle: vi.fn(),
  onDestinationChange: vi.fn(),
};

describe('LayerPanel commute toggle', () => {
  it('renders a commute toggle checkbox', async () => {
    const { LayerPanel } = await import('./LayerPanel');
    const { getByTestId } = render(<LayerPanel {...defaultProps} />);
    const toggle = getByTestId('toggle-commute');
    expect(toggle).toBeTruthy();
  });

  it('commute toggle checkbox is unchecked when commuteVisible=false', async () => {
    const { LayerPanel } = await import('./LayerPanel');
    const { getByTestId } = render(<LayerPanel {...defaultProps} commuteVisible={false} />);
    const toggle = getByTestId('toggle-commute');
    const checkbox = toggle.querySelector('input[type="checkbox"]');
    expect((checkbox as HTMLInputElement).checked).toBe(false);
  });

  it('commute toggle checkbox is checked when commuteVisible=true', async () => {
    const { LayerPanel } = await import('./LayerPanel');
    const { getByTestId } = render(<LayerPanel {...defaultProps} commuteVisible={true} />);
    const toggle = getByTestId('toggle-commute');
    const checkbox = toggle.querySelector('input[type="checkbox"]');
    expect((checkbox as HTMLInputElement).checked).toBe(true);
  });

  it('calls onCommuteToggle when commute checkbox is clicked', async () => {
    const { LayerPanel } = await import('./LayerPanel');
    const onCommuteToggle = vi.fn();
    const { getByTestId } = render(
      <LayerPanel {...defaultProps} onCommuteToggle={onCommuteToggle} />
    );
    const toggle = getByTestId('toggle-commute');
    const checkbox = toggle.querySelector('input[type="checkbox"]')!;
    fireEvent.click(checkbox);
    expect(onCommuteToggle).toHaveBeenCalledTimes(1);
  });
});

describe('LayerPanel destination buttons', () => {
  it('destination buttons are NOT shown when commuteVisible=false', async () => {
    const { LayerPanel } = await import('./LayerPanel');
    const { queryByTestId } = render(<LayerPanel {...defaultProps} commuteVisible={false} />);
    expect(queryByTestId('commute-destinations')).toBeNull();
  });

  it('destination buttons ARE shown when commuteVisible=true', async () => {
    const { LayerPanel } = await import('./LayerPanel');
    const { getByTestId } = render(<LayerPanel {...defaultProps} commuteVisible={true} />);
    expect(getByTestId('commute-destinations')).toBeTruthy();
  });

  it('HB button is present when commute is visible', async () => {
    const { LayerPanel } = await import('./LayerPanel');
    const { getByTestId } = render(<LayerPanel {...defaultProps} commuteVisible={true} />);
    expect(getByTestId('destination-hb')).toBeTruthy();
  });

  it('all four destination buttons are rendered when commute is visible', async () => {
    const { LayerPanel } = await import('./LayerPanel');
    const { getByTestId } = render(<LayerPanel {...defaultProps} commuteVisible={true} />);
    expect(getByTestId('destination-hb')).toBeTruthy();
    expect(getByTestId('destination-eth')).toBeTruthy();
    expect(getByTestId('destination-airport')).toBeTruthy();
    expect(getByTestId('destination-technopark')).toBeTruthy();
  });

  it('active destination button has distinct styling (hb by default)', async () => {
    const { LayerPanel } = await import('./LayerPanel');
    const { getByTestId } = render(
      <LayerPanel {...defaultProps} commuteVisible={true} activeDestination="hb" />
    );
    const hbButton = getByTestId('destination-hb');
    // Active button should have bg-strata-amber class
    expect(hbButton.className).toContain('bg-strata-amber');
  });

  it('calls onDestinationChange when ETH button is clicked', async () => {
    const { LayerPanel } = await import('./LayerPanel');
    const onDestinationChange = vi.fn();
    const { getByTestId } = render(
      <LayerPanel
        {...defaultProps}
        commuteVisible={true}
        onDestinationChange={onDestinationChange}
      />
    );
    fireEvent.click(getByTestId('destination-eth'));
    expect(onDestinationChange).toHaveBeenCalledWith('eth');
  });

  it('calls onDestinationChange with "airport" when Airport button clicked', async () => {
    const { LayerPanel } = await import('./LayerPanel');
    const onDestinationChange = vi.fn();
    const { getByTestId } = render(
      <LayerPanel
        {...defaultProps}
        commuteVisible={true}
        onDestinationChange={onDestinationChange}
      />
    );
    fireEvent.click(getByTestId('destination-airport'));
    expect(onDestinationChange).toHaveBeenCalledWith('airport');
  });
});
