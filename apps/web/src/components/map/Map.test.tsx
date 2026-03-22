import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render } from '@testing-library/react';

// Mock maplibre-gl — it requires a WebGL context unavailable in jsdom
vi.mock('maplibre-gl', () => {
  const Map = vi.fn().mockImplementation(() => ({
    on: vi.fn(),
    off: vi.fn(),
    remove: vi.fn(),
    addSource: vi.fn(),
    addLayer: vi.fn(),
    getSource: vi.fn(),
    getLayer: vi.fn(),
    getCanvas: vi.fn().mockReturnValue({ style: {} }),
    isStyleLoaded: vi.fn().mockReturnValue(true),
    addControl: vi.fn(),
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

beforeEach(() => {
  vi.resetModules();
});

describe('Map component', () => {
  it('renders a container div', async () => {
    const { MapView } = await import('./Map');
    const { container } = render(<MapView />);
    const mapDiv = container.querySelector('[data-testid="map-container"]');
    expect(mapDiv).toBeTruthy();
  });

  it('renders the Legend inside the map container', async () => {
    const { MapView } = await import('./Map');
    const { getByText } = render(<MapView />);
    expect(getByText('Construction era')).toBeTruthy();
  });
});
