import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AirLegend } from './AirLegend';
import { AIR_LEVELS } from '@/lib/map/air-colors';

describe('AirLegend', () => {
  it('renders nothing when not visible', () => {
    const { container } = render(<AirLegend visible={false} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders a swatch for each level when visible', () => {
    const { container } = render(<AirLegend visible={true} />);
    const swatches = container.querySelectorAll('[data-testid="air-legend-swatch"]');
    expect(swatches.length).toBe(AIR_LEVELS.length);
  });

  it('labels each level', () => {
    render(<AirLegend visible={true} />);
    for (const l of AIR_LEVELS) {
      expect(screen.getByText(l.label)).toBeTruthy();
    }
  });

  it('applies the level color to each swatch', () => {
    const { container } = render(<AirLegend visible={true} />);
    const swatches = container.querySelectorAll('[data-testid="air-legend-swatch"]');
    swatches.forEach((swatch) => {
      expect((swatch as HTMLElement).style.backgroundColor).toBeTruthy();
    });
  });

  it('applies glass card styling', () => {
    const { container } = render(<AirLegend visible={true} />);
    const card = container.firstChild as HTMLElement;
    expect(card.className).toContain('strata-panel');
  });
});
