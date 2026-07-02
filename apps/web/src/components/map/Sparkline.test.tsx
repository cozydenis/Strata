import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { Sparkline } from './Sparkline';

describe('Sparkline', () => {
  it('renders a polyline with one point per value', () => {
    const { container } = render(<Sparkline values={[10, 20, 15, 30]} label="rent trend" />);
    const polyline = container.querySelector('polyline');
    expect(polyline).toBeTruthy();
    const points = (polyline?.getAttribute('points') ?? '').trim().split(' ');
    expect(points.length).toBe(4);
  });

  it('normalizes values into the viewBox', () => {
    const { container } = render(<Sparkline values={[0, 100]} label="x" />);
    const polyline = container.querySelector('polyline');
    const points = (polyline?.getAttribute('points') ?? '').split(' ');
    // First value (min) sits at the bottom, last (max) at the top of the viewBox.
    const [, y0] = points[0].split(',').map(Number);
    const [, y1] = points[1].split(',').map(Number);
    expect(y0).toBeGreaterThan(y1);
  });

  it('renders flat line for constant values without NaN', () => {
    const { container } = render(<Sparkline values={[5, 5, 5]} label="x" />);
    const points = container.querySelector('polyline')?.getAttribute('points') ?? '';
    expect(points).not.toContain('NaN');
  });

  it('renders nothing for fewer than 2 values', () => {
    const { container } = render(<Sparkline values={[5]} label="x" />);
    expect(container.innerHTML).toBe('');
  });

  it('carries an aria-label', () => {
    const { container } = render(<Sparkline values={[1, 2]} label="rent trend" />);
    expect(container.querySelector('svg')?.getAttribute('aria-label')).toBe('rent trend');
  });
});
