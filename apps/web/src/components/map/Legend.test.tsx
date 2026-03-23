import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
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

  it('does not render listings toggle when no callback provided', () => {
    render(<Legend />);
    expect(screen.queryByTestId('listings-toggle')).toBeNull();
  });

  it('renders listings toggle when onToggleListings provided', () => {
    render(<Legend listingsVisible={true} onToggleListings={() => {}} />);
    expect(screen.getByTestId('listings-toggle')).toBeTruthy();
    expect(screen.getByText('Active listings')).toBeTruthy();
  });

  it('checkbox reflects listingsVisible state', () => {
    render(<Legend listingsVisible={false} onToggleListings={() => {}} />);
    const checkbox = screen.getByRole('checkbox') as HTMLInputElement;
    expect(checkbox.checked).toBe(false);
  });

  it('calls onToggleListings when checkbox clicked', () => {
    const toggle = vi.fn();
    render(<Legend listingsVisible={true} onToggleListings={toggle} />);
    fireEvent.click(screen.getByRole('checkbox'));
    expect(toggle).toHaveBeenCalledTimes(1);
  });

  it('renders a red listing swatch', () => {
    render(<Legend listingsVisible={true} onToggleListings={() => {}} />);
    const swatch = screen.getByTestId('listings-swatch') as HTMLElement;
    expect(swatch.style.backgroundColor).toBeTruthy();
  });
});
