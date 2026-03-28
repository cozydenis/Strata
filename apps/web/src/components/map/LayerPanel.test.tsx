import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { LayerPanel } from './LayerPanel';

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

describe('LayerPanel', () => {
  it('renders without crashing', () => {
    render(<LayerPanel {...defaultProps} />);
  });

  it('renders a buildings toggle', () => {
    render(<LayerPanel {...defaultProps} />);
    expect(screen.getByTestId('toggle-buildings')).toBeTruthy();
  });

  it('renders a listings toggle', () => {
    render(<LayerPanel {...defaultProps} />);
    expect(screen.getByTestId('toggle-listings')).toBeTruthy();
  });

  it('renders a quartiere toggle', () => {
    render(<LayerPanel {...defaultProps} />);
    expect(screen.getByTestId('toggle-quartiere')).toBeTruthy();
  });

  it('renders a noise toggle', () => {
    render(<LayerPanel {...defaultProps} />);
    expect(screen.getByTestId('toggle-noise')).toBeTruthy();
  });

  it('buildings checkbox reflects buildingsVisible=true', () => {
    render(<LayerPanel {...defaultProps} buildingsVisible={true} />);
    const cb = screen.getByTestId('toggle-buildings').querySelector('input[type="checkbox"]') as HTMLInputElement;
    expect(cb.checked).toBe(true);
  });

  it('buildings checkbox reflects buildingsVisible=false', () => {
    render(<LayerPanel {...defaultProps} buildingsVisible={false} />);
    const cb = screen.getByTestId('toggle-buildings').querySelector('input[type="checkbox"]') as HTMLInputElement;
    expect(cb.checked).toBe(false);
  });

  it('quartiere checkbox reflects quartiereVisible=false', () => {
    render(<LayerPanel {...defaultProps} quartiereVisible={false} />);
    const cb = screen.getByTestId('toggle-quartiere').querySelector('input[type="checkbox"]') as HTMLInputElement;
    expect(cb.checked).toBe(false);
  });

  it('calls onToggle with "buildings" when buildings checkbox clicked', () => {
    const onToggle = vi.fn();
    render(<LayerPanel {...defaultProps} onToggle={onToggle} />);
    fireEvent.click(
      screen.getByTestId('toggle-buildings').querySelector('input[type="checkbox"]')!,
    );
    expect(onToggle).toHaveBeenCalledWith('buildings');
  });

  it('calls onToggle with "quartiere" when quartiere checkbox clicked', () => {
    const onToggle = vi.fn();
    render(<LayerPanel {...defaultProps} onToggle={onToggle} />);
    fireEvent.click(
      screen.getByTestId('toggle-quartiere').querySelector('input[type="checkbox"]')!,
    );
    expect(onToggle).toHaveBeenCalledWith('quartiere');
  });

  it('calls onToggle with "noise" when noise checkbox clicked', () => {
    const onToggle = vi.fn();
    render(<LayerPanel {...defaultProps} onToggle={onToggle} />);
    fireEvent.click(
      screen.getByTestId('toggle-noise').querySelector('input[type="checkbox"]')!,
    );
    expect(onToggle).toHaveBeenCalledWith('noise');
  });

  it('renders metric selector when quartiere is visible', () => {
    render(<LayerPanel {...defaultProps} quartiereVisible={true} />);
    expect(screen.getByTestId('metric-select')).toBeTruthy();
  });

  it('does not render metric selector when quartiere is hidden', () => {
    render(<LayerPanel {...defaultProps} quartiereVisible={false} />);
    expect(screen.queryByTestId('metric-select')).toBeNull();
  });

  it('calls onMetricChange when metric is changed', () => {
    const onMetricChange = vi.fn();
    render(<LayerPanel {...defaultProps} quartiereVisible={true} onMetricChange={onMetricChange} />);
    const select = screen.getByTestId('metric-select') as HTMLSelectElement;
    fireEvent.change(select, { target: { value: 'foreign_pct' } });
    expect(onMetricChange).toHaveBeenCalledWith('foreign_pct');
  });

  it('shows "Layers" heading or label', () => {
    render(<LayerPanel {...defaultProps} />);
    expect(screen.getByText(/layers/i)).toBeTruthy();
  });

  it('applies glass card styling', () => {
    const { container } = render(<LayerPanel {...defaultProps} />);
    const card = container.firstChild as HTMLElement;
    expect(card.className).toContain('backdrop-blur');
  });
});
