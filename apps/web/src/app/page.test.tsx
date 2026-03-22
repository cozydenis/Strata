import { describe, it, expect, vi } from 'vitest';
import { render } from '@testing-library/react';

// Mock next/dynamic to render the component directly
vi.mock('next/dynamic', () => ({
  default: (loader: () => Promise<{ default: React.ComponentType }>) => {
    // Immediately resolve for tests
    let Component: React.ComponentType | null = null;
    loader().then((mod) => {
      Component = 'default' in mod ? mod.default : (mod as unknown as React.ComponentType);
    });
    return function DynamicWrapper(props: Record<string, unknown>) {
      if (!Component) return null;
      return <Component {...props} />;
    };
  },
}));

// Mock maplibre-gl
vi.mock('maplibre-gl', () => {
  const Map = vi.fn().mockImplementation(() => ({
    on: vi.fn(),
    remove: vi.fn(),
    addControl: vi.fn(),
    getCanvas: vi.fn().mockReturnValue({ style: {} }),
  }));
  const NavigationControl = vi.fn();
  const Popup = vi.fn().mockImplementation(() => ({
    setLngLat: vi.fn().mockReturnThis(),
    setDOMContent: vi.fn().mockReturnThis(),
    addTo: vi.fn().mockReturnThis(),
    on: vi.fn().mockReturnThis(),
    remove: vi.fn(),
  }));
  return { default: { Map, NavigationControl, Popup } };
});

describe('HomePage', () => {
  it('renders the page', async () => {
    const { default: HomePage } = await import('./page');
    const { container } = render(<HomePage />);
    expect(container.querySelector('main')).toBeTruthy();
  });
});
