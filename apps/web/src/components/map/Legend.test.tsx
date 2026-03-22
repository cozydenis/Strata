import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Legend } from './Legend';
import { ERA_COLORS } from '@/lib/map/era-colors';

describe('Legend', () => {
  it('renders a row for every era', () => {
    render(<Legend />);
    for (const era of ERA_COLORS) {
      expect(screen.getByText(era.label)).toBeTruthy();
    }
  });

  it('renders a color swatch for each era', () => {
    const { container } = render(<Legend />);
    const swatches = container.querySelectorAll('[data-testid="era-swatch"]');
    expect(swatches.length).toBe(ERA_COLORS.length);
  });

  it('applies the correct background color to each swatch', () => {
    const { container } = render(<Legend />);
    const swatches = container.querySelectorAll('[data-testid="era-swatch"]');
    swatches.forEach((swatch, i) => {
      expect((swatch as HTMLElement).style.backgroundColor).toBeTruthy();
      expect(ERA_COLORS[i].color).toMatch(/^#[0-9A-Fa-f]{6}$/);
    });
  });
});
