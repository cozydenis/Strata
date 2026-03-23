'use client';

import { useEffect, useRef, useState } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { createElement } from 'react';
import { Legend } from './Legend';
import { BuildingPopup } from './BuildingPopup';
import { eraColorExpression } from '@/lib/map/era-colors';
import {
  fetchBuildingSummary,
  fetchBuildingListings,
  type BuildingSummary,
  type ListingSummary,
} from '@/lib/api';

const ZURICH_CENTER: [number, number] = [8.54, 47.38];
const INITIAL_ZOOM = 12;
const GEOJSON_URL = '/data/buildings.geojson';
const LISTINGS_GEOJSON_URL = '/data/listings.geojson';
const TILE_STYLE = 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json';
const LISTING_COLOR = '#E53935';

export function MapView() {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<unknown>(null);
  const popupRef = useRef<unknown>(null);
  const popupRootRef = useRef<Root | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [popup, setPopup] = useState<BuildingSummary | null>(null);
  const [popupListings, setPopupListings] = useState<ListingSummary[] | null>(null);
  const [popupCoords, setPopupCoords] = useState<[number, number] | null>(null);
  const [listingsVisible, setListingsVisible] = useState(true);

  // Handle building click — fetch summary + listings in parallel
  async function handleBuildingClick(egid: number, coords: [number, number]) {
    try {
      const [summary, listings] = await Promise.all([
        fetchBuildingSummary(egid),
        fetchBuildingListings(egid).catch(() => []),
      ]);
      setPopup(summary);
      setPopupListings(listings);
      setPopupCoords(coords);
    } catch (err) {
      console.error('[Strata] Failed to load building data:', err);
    }
  }

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    let cancelled = false;

    async function init() {
      try {
        const mod = await import('maplibre-gl');
        const maplibregl = mod.default ?? mod;
        const MapClass = maplibregl.Map ?? (mod as unknown as { Map: unknown }).Map;

        if (cancelled || !containerRef.current) return;

        const map = new MapClass({
          container: containerRef.current,
          style: TILE_STYLE,
          center: ZURICH_CENTER,
          zoom: INITIAL_ZOOM,
        });
        mapRef.current = map;

        const NavControl = maplibregl.NavigationControl ?? (mod as unknown as { NavigationControl: unknown }).NavigationControl;
        map.addControl(new NavControl(), 'top-right');

        map.on('load', () => {
          // ── Buildings source + layers ──────────────────────────────────
          map.addSource('buildings', {
            type: 'geojson',
            data: GEOJSON_URL,
            cluster: true,
            clusterMaxZoom: 14,
            clusterRadius: 30,
          });

          map.addLayer({
            id: 'clusters',
            type: 'circle',
            source: 'buildings',
            filter: ['has', 'point_count'],
            paint: {
              'circle-color': '#4682B4',
              'circle-radius': ['step', ['get', 'point_count'], 8, 50, 12, 200, 16],
              'circle-opacity': 0.7,
            },
          });

          map.addLayer({
            id: 'cluster-count',
            type: 'symbol',
            source: 'buildings',
            filter: ['has', 'point_count'],
            layout: {
              'text-field': '{point_count_abbreviated}',
              'text-size': 10,
            },
            paint: { 'text-color': '#fff' },
          });

          map.addLayer({
            id: 'buildings-unclustered',
            type: 'circle',
            source: 'buildings',
            filter: ['!', ['has', 'point_count']],
            paint: {
              'circle-color': eraColorExpression() as unknown as string,
              'circle-radius': 4,
              'circle-stroke-width': 1,
              'circle-stroke-color': '#fff',
              'circle-opacity': 0.85,
            },
          });

          // ── Listings source + layer ───────────────────────────────────
          map.addSource('listings', {
            type: 'geojson',
            data: LISTINGS_GEOJSON_URL,
          });

          map.addLayer({
            id: 'listings-markers',
            type: 'circle',
            source: 'listings',
            paint: {
              'circle-color': LISTING_COLOR,
              'circle-radius': 6,
              'circle-stroke-width': 2,
              'circle-stroke-color': '#fff',
              'circle-opacity': 0.9,
            },
          });

          // ── Click: listings layer (on top) ────────────────────────────
          map.on('click', 'listings-markers', async (e: { features?: Array<{ geometry: GeoJSON.Geometry; properties?: Record<string, unknown> }>; originalEvent: Event }) => {
            e.originalEvent.stopPropagation();
            if (!e.features?.length) return;
            const feature = e.features[0];
            const egid = feature.properties?.egid;
            if (typeof egid !== 'number') return;
            const coords = (feature.geometry as GeoJSON.Point).coordinates as [number, number];
            handleBuildingClick(egid, coords);
          });

          // ── Click: buildings layer ────────────────────────────────────
          map.on('click', 'buildings-unclustered', async (e: { features?: Array<{ geometry: GeoJSON.Geometry; properties?: Record<string, unknown> }> }) => {
            if (!e.features?.length) return;
            const feature = e.features[0];
            const egid = feature.properties?.egid;
            if (typeof egid !== 'number') return;
            const coords = (feature.geometry as GeoJSON.Point).coordinates as [number, number];
            handleBuildingClick(egid, coords);
          });

          // ── Cursor hints ──────────────────────────────────────────────
          for (const layer of ['buildings-unclustered', 'listings-markers']) {
            map.on('mouseenter', layer, () => {
              map.getCanvas().style.cursor = 'pointer';
            });
            map.on('mouseleave', layer, () => {
              map.getCanvas().style.cursor = '';
            });
          }
        });
      } catch (err) {
        console.error('[Strata] Failed to initialize map:', err);
        setError(String(err));
      }
    }

    init();

    return () => {
      cancelled = true;
      const map = mapRef.current as { remove: () => void } | null;
      if (map) {
        map.remove();
        mapRef.current = null;
      }
    };
  }, []);

  // Toggle listings layer visibility
  useEffect(() => {
    const map = mapRef.current as { setLayoutProperty?: (layer: string, prop: string, val: string) => void; getLayer?: (id: string) => unknown } | null;
    if (!map?.setLayoutProperty || !map?.getLayer?.('listings-markers')) return;
    map.setLayoutProperty('listings-markers', 'visibility', listingsVisible ? 'visible' : 'none');
  }, [listingsVisible]);

  // Popup rendering
  useEffect(() => {
    if (!mapRef.current || !popup || !popupCoords) return;

    // Clean up previous popup root and popup
    popupRootRef.current?.unmount();
    popupRootRef.current = null;
    const prev = popupRef.current as { remove: () => void } | null;
    prev?.remove();

    async function showPopup() {
      const mod = await import('maplibre-gl');
      const maplibregl = mod.default ?? mod;

      const el = document.createElement('div');
      const root = createRoot(el);
      popupRootRef.current = root;
      root.render(
        createElement(BuildingPopup, {
          summary: popup!,
          listings: popupListings ?? undefined,
        })
      );

      const PopupClass = maplibregl.Popup ?? (mod as unknown as { Popup: unknown }).Popup;
      const mp = new PopupClass({ closeOnClick: true, maxWidth: '320px' })
        .setLngLat(popupCoords!)
        .setDOMContent(el)
        .addTo(mapRef.current!);

      mp.on('close', () => {
        popupRootRef.current?.unmount();
        popupRootRef.current = null;
        setPopup(null);
        setPopupListings(null);
      });
      popupRef.current = mp;
    }

    showPopup();
  }, [popup, popupCoords, popupListings]);

  if (error) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-red-50 text-red-600">
        <p>Map failed to load: {error}</p>
      </div>
    );
  }

  return (
    <div className="relative h-screen w-screen" data-testid="map-container">
      <div ref={containerRef} className="absolute inset-0" />
      <Legend
        listingsVisible={listingsVisible}
        onToggleListings={() => setListingsVisible((v) => !v)}
      />
    </div>
  );
}
