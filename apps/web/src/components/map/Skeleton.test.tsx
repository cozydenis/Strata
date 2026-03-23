import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { SkeletonLine, SkeletonBlock, PopupSkeleton } from './Skeleton';

describe('SkeletonLine', () => {
  it('renders a div with animate-shimmer class', () => {
    const { container } = render(<SkeletonLine />);
    const el = container.firstElementChild as HTMLElement;
    expect(el).toBeTruthy();
    expect(el.className).toContain('animate-shimmer');
  });

  it('uses default w-full width', () => {
    const { container } = render(<SkeletonLine />);
    const el = container.firstElementChild as HTMLElement;
    expect(el.className).toContain('w-full');
  });

  it('accepts a custom width prop', () => {
    const { container } = render(<SkeletonLine width="w-3/4" />);
    const el = container.firstElementChild as HTMLElement;
    expect(el.className).toContain('w-3/4');
  });

  it('renders with height class h-3', () => {
    const { container } = render(<SkeletonLine />);
    const el = container.firstElementChild as HTMLElement;
    expect(el.className).toContain('h-3');
  });
});

describe('SkeletonBlock', () => {
  it('renders a div with animate-shimmer class', () => {
    const { container } = render(<SkeletonBlock />);
    const el = container.firstElementChild as HTMLElement;
    expect(el).toBeTruthy();
    expect(el.className).toContain('animate-shimmer');
  });

  it('uses default h-12 height', () => {
    const { container } = render(<SkeletonBlock />);
    const el = container.firstElementChild as HTMLElement;
    expect(el.className).toContain('h-12');
  });

  it('accepts a custom height prop', () => {
    const { container } = render(<SkeletonBlock height="h-[72px]" />);
    const el = container.firstElementChild as HTMLElement;
    expect(el.className).toContain('h-[72px]');
  });

  it('spans full width', () => {
    const { container } = render(<SkeletonBlock />);
    const el = container.firstElementChild as HTMLElement;
    expect(el.className).toContain('w-full');
  });
});

describe('PopupSkeleton', () => {
  it('renders without crashing', () => {
    const { container } = render(<PopupSkeleton />);
    expect(container.firstElementChild).toBeTruthy();
  });

  it('renders multiple skeleton lines', () => {
    const { container } = render(<PopupSkeleton />);
    // SkeletonLines have h-3 class
    const lines = container.querySelectorAll('.h-3');
    expect(lines.length).toBeGreaterThanOrEqual(2);
  });

  it('renders at least one skeleton block', () => {
    const { container } = render(<PopupSkeleton />);
    // SkeletonBlock has h-12 or custom height
    const blocks = container.querySelectorAll('[class*="rounded-md"]');
    expect(blocks.length).toBeGreaterThanOrEqual(1);
  });

  it('has a minimum width for the popup', () => {
    const { container } = render(<PopupSkeleton />);
    const wrapper = container.firstElementChild as HTMLElement;
    expect(wrapper.className).toContain('min-w-');
  });

  it('renders a divider between header and body sections', () => {
    const { container } = render(<PopupSkeleton />);
    const divider = container.querySelector('.border-t');
    expect(divider).toBeTruthy();
  });
});
