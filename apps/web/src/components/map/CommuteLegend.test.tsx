import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';

describe('CommuteLegend', () => {
  it('renders null/empty when visible=false', async () => {
    const { CommuteLegend } = await import('./CommuteLegend');
    const { container } = render(<CommuteLegend visible={false} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders when visible=true', async () => {
    const { CommuteLegend } = await import('./CommuteLegend');
    const { container } = render(<CommuteLegend visible={true} />);
    expect(container.firstChild).toBeTruthy();
  });

  it('renders exactly 5 legend band items when visible', async () => {
    const { CommuteLegend } = await import('./CommuteLegend');
    const { container } = render(<CommuteLegend visible={true} />);
    const items = container.querySelectorAll('[data-testid="commute-legend-item"]');
    expect(items).toHaveLength(5);
  });

  it('shows "0-10 min" label', async () => {
    const { CommuteLegend } = await import('./CommuteLegend');
    const { getByText } = render(<CommuteLegend visible={true} />);
    expect(getByText('0-10 min')).toBeTruthy();
  });

  it('shows "45+ min" label', async () => {
    const { CommuteLegend } = await import('./CommuteLegend');
    const { getByText } = render(<CommuteLegend visible={true} />);
    expect(getByText('45+ min')).toBeTruthy();
  });

  it('shows "10-20 min" label', async () => {
    const { CommuteLegend } = await import('./CommuteLegend');
    const { getByText } = render(<CommuteLegend visible={true} />);
    expect(getByText('10-20 min')).toBeTruthy();
  });

  it('shows "20-30 min" label', async () => {
    const { CommuteLegend } = await import('./CommuteLegend');
    const { getByText } = render(<CommuteLegend visible={true} />);
    expect(getByText('20-30 min')).toBeTruthy();
  });

  it('shows "30-45 min" label', async () => {
    const { CommuteLegend } = await import('./CommuteLegend');
    const { getByText } = render(<CommuteLegend visible={true} />);
    expect(getByText('30-45 min')).toBeTruthy();
  });

  it('renders color swatches for each band', async () => {
    const { CommuteLegend } = await import('./CommuteLegend');
    const { container } = render(<CommuteLegend visible={true} />);
    const swatches = container.querySelectorAll('[data-testid="commute-legend-swatch"]');
    expect(swatches).toHaveLength(5);
  });

  it('has a legend title', async () => {
    const { CommuteLegend } = await import('./CommuteLegend');
    const { container } = render(<CommuteLegend visible={true} />);
    expect(container.textContent).toContain('Commute');
  });
});
