import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { MapLoadingOverlay } from './MapLoadingOverlay';

describe('MapLoadingOverlay', () => {
  it('renders without crashing', () => {
    const { container } = render(<MapLoadingOverlay visible={true} />);
    expect(container.firstElementChild).toBeTruthy();
  });

  it('is fully visible when visible=true (opacity-100)', () => {
    const { container } = render(<MapLoadingOverlay visible={true} />);
    const el = container.firstElementChild as HTMLElement;
    expect(el.className).toContain('opacity-100');
  });

  it('is invisible when visible=false (opacity-0)', () => {
    const { container } = render(<MapLoadingOverlay visible={false} />);
    const el = container.firstElementChild as HTMLElement;
    expect(el.className).toContain('opacity-0');
  });

  it('has pointer-events-none when not visible', () => {
    const { container } = render(<MapLoadingOverlay visible={false} />);
    const el = container.firstElementChild as HTMLElement;
    expect(el.className).toContain('pointer-events-none');
  });

  it('covers the entire viewport with absolute inset-0', () => {
    const { container } = render(<MapLoadingOverlay visible={true} />);
    const el = container.firstElementChild as HTMLElement;
    expect(el.className).toContain('absolute');
    expect(el.className).toContain('inset-0');
  });

  it('displays the brand name Strata', () => {
    const { container } = render(<MapLoadingOverlay visible={true} />);
    expect(container.textContent).toMatch(/strata/i);
  });

  it('renders a shimmer loading bar', () => {
    const { container } = render(<MapLoadingOverlay visible={true} />);
    const shimmer = container.querySelector('.animate-shimmer');
    expect(shimmer).toBeTruthy();
  });

  it('has a high z-index to cover the map', () => {
    const { container } = render(<MapLoadingOverlay visible={true} />);
    const el = container.firstElementChild as HTMLElement;
    expect(el.className).toMatch(/z-\d+/);
  });
});
