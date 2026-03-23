import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { TopBar } from './TopBar';

describe('TopBar', () => {
  it('renders the brand name Strata', () => {
    render(<TopBar />);
    expect(screen.getByText(/strata/i)).toBeTruthy();
  });

  it('renders with uppercase text styling class', () => {
    const { container } = render(<TopBar />);
    const span = container.querySelector('span');
    expect(span).toBeTruthy();
    expect(span?.className).toContain('uppercase');
  });

  it('is absolutely positioned in the top-left', () => {
    const { container } = render(<TopBar />);
    const wrapper = container.firstElementChild as HTMLElement;
    expect(wrapper.className).toContain('absolute');
    expect(wrapper.className).toContain('top-4');
    expect(wrapper.className).toContain('left-4');
  });

  it('has a z-index class for layering above the map', () => {
    const { container } = render(<TopBar />);
    const wrapper = container.firstElementChild as HTMLElement;
    expect(wrapper.className).toMatch(/z-\d+/);
  });
});
