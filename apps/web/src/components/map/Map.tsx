'use client';

import { useEffect, useRef, useState } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { createElement } from 'react';
import { Legend } from './Legend';
import { TopBar } from './TopBar';
import { BuildingPopup } from './BuildingPopup';
import { MapLoadingOverlay } from './MapLoadingOverlay';
import { PopupSkeleton } from './Skeleton';
import { LayerPanel } from './LayerPanel';
import { QuartierProfile } from './QuartierProfile';
import { eraColorExpression } from '@/lib/map/era-colors';
import { quartierFillColor } from '@/lib/map/quartier-colors';
import { noiseLineColor } from '@/lib/map/noise-colors';
import {
  fetchBuildingSummary,
  fetchBuildingListings,
  fetchQuartierProfile,
  type BuildingSummary,
  type ListingSummary,
  type QuartierProfile as QuartierProfileType,
} from '@/lib/api';

const ZURICH_CENTER: [number, number] = [8.54, 47.38];
const INITIAL_ZOOM = 12;
const GEOJSON_URL = '/data/buildings.geojson';
const LISTINGS_GEOJSON_URL = '/data/listings.geojson';
const QUARTIERE_GEOJSON_URL = '/data/quartiere.geojson';
const NOISE_GEOJSON_URL = '/data/noise.geojson';
const TILE_STYLE = 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json';
const LISTING_COLOR = '#D4915A';
const BUILDING_LAYERS = ['clusters', 'cluster-count', 'buildings-unclustered'] as const;
const QUARTIERE_LAYERS = ['quartiere-fill', 'quartiere-outline', 'quartiere-labels'] as const;

export function MapView() {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<unknown>(null);
  const popupRef = useRef<unknown>(null);
  const popupRootRef = useRef<Root | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [popup, setPopup] = useState<BuildingSummary | null>(null);
  const [popupListings, setPopupListings] = useState<ListingSummary[] | null>(null);
  const [popupCoords, setPopupCoords] = useState<[number, number] | null>(null);
  const [mapLoaded, setMapLoaded] = useState(false);

  // Layer visibility state
  const [buildingsVisible, setBuildingsVisible] = useState(true);
  const [listingsVisible, setListingsVisible] = useState(true);
  const [quartiereVisible, setQuartiereVisible] = useState(false);
  const [noiseVisible, setNoiseVisible] = useState(false);
  const [activeMetric, setActiveMetric] = useState('population_density');

  // Quartier profile panel
  const [quartierProfile, setQuartierProfile] = useState<QuartierProfileType | null>(null);

  // Handle building click — show skeleton immediately, then fetch real data
  async function handleBuildingClick(egid: number, coords: [number, number]) {
    setQuartierProfile(null); // close quartier panel when building clicked
    try {
      await showSkeletonPopup(coords);
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

  async function handleQuartierClick(quartierId: number) {
    // Close building popup when quartier clicked
    const prev = popupRef.current as { remove: () => void } | null;
    prev?.remove();
    popupRootRef.current?.unmount();
    popupRootRef.current = null;
    setPopup(null);
    setPopupListings(null);

    try {
      const profile = await fetchQuartierProfile(quartierId);
      setQuartierProfile(profile);
    } catch (err) {
      console.error('[Strata] Failed to load quartier profile:', err);
    }
  }

  async function showSkeletonPopup(coords: [number, number]) {
    if (!mapRef.current) return;

    // Clean up previous popup
    popupRootRef.current?.unmount();
    popupRootRef.current = null;
    const prev = popupRef.current as { remove: () => void } | null;
    prev?.remove();

    const mod = await import('maplibre-gl');
    const maplibregl = mod.default ?? mod;

    const el = document.createElement('div');
    const root = createRoot(el);
    popupRootRef.current = root;
    root.render(createElement(PopupSkeleton));

    const PopupClass = maplibregl.Popup ?? (mod as unknown as { Popup: unknown }).Popup;
    const mp = new PopupClass({ closeOnClick: true, maxWidth: '340px' })
      .setLngLat(coords)
      .setDOMContent(el)
      .addTo(mapRef.current as Parameters<typeof mp.addTo>[0]);

    mp.on('close', () => {
      popupRootRef.current?.unmount();
      popupRootRef.current = null;
      setPopup(null);
      setPopupListings(null);
    });
    popupRef.current = mp;
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
          setMapLoaded(true);

          // ── Quartiere source + layers (below buildings) ───────────────
          map.addSource('quartiere', {
            type: 'geojson',
            data: QUARTIERE_GEOJSON_URL,
          });

          map.addLayer({
            id: 'quartiere-fill',
            type: 'fill',
            source: 'quartiere',
            layout: { visibility: 'none' },
            paint: {
              'fill-color': quartierFillColor('population_density') as unknown as string,
              'fill-opacity': 0.65,
            },
          });

          map.addLayer({
            id: 'quartiere-outline',
            type: 'line',
            source: 'quartiere',
            layout: { visibility: 'none' },
            paint: {
              'line-color': 'rgba(250,247,242,0.7)',
              'line-width': 1.5,
            },
          });

          map.addLayer({
            id: 'quartiere-labels',
            type: 'symbol',
            source: 'quartiere',
            layout: {
              visibility: 'none',
              'text-field': ['get', 'quartier_name'],
              'text-size': 11,
              'text-max-width': 8,
            },
            paint: {
              'text-color': 'rgba(250,247,242,0.8)',
              'text-halo-color': 'rgba(0,0,0,0.6)',
              'text-halo-width': 1,
            },
          });

          // ── Noise source + layer (below buildings) ────────────────────
          map.addSource('noise', {
            type: 'geojson',
            data: NOISE_GEOJSON_URL,
          });

          map.addLayer({
            id: 'noise-segments',
            type: 'circle',
            source: 'noise',
            layout: { visibility: 'none' },
            paint: {
              'circle-color': noiseLineColor() as unknown as string,
              'circle-radius': 3,
              'circle-opacity': 0.7,
            },
          });

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
              'circle-color': '#504C47',
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
            paint: { 'text-color': '#FAF7F2' },
          });

          map.addLayer({
            id: 'buildings-unclustered',
            type: 'circle',
            source: 'buildings',
            filter: ['!', ['has', 'point_count']],
            paint: {
              'circle-color': eraColorExpression() as unknown as string,
              'circle-radius': 4,
              'circle-stroke-width': 0.5,
              'circle-stroke-color': 'rgba(250,247,242,0.3)',
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

          // ── Click: quartiere layer ────────────────────────────────────
          map.on('click', 'quartiere-fill', async (e: { features?: Array<{ properties?: Record<string, unknown> }>; originalEvent: Event }) => {
            e.originalEvent.stopPropagation();
            if (!e.features?.length) return;
            const quartierId = e.features[0].properties?.quartier_id;
            if (typeof quartierId !== 'number') return;
            handleQuartierClick(quartierId);
          });

          // ── Cursor hints ──────────────────────────────────────────────
          for (const layer of ['buildings-unclustered', 'listings-markers', 'quartiere-fill']) {
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

  // Toggle buildings layer visibility with opacity fade
  useEffect(() => {
    const map = mapRef.current as {
      setPaintProperty?: (layer: string, prop: string, val: number) => void;
      setLayoutProperty?: (layer: string, prop: string, val: string) => void;
      getLayer?: (id: string) => unknown;
    } | null;
    if (!map?.setLayoutProperty || !map?.getLayer?.('buildings-unclustered')) return;

    const FADE_DURATION = 300;
    const START_OPACITY = buildingsVisible ? 0 : 0.85;
    const END_OPACITY = buildingsVisible ? 0.85 : 0;
    const startTime = performance.now();

    if (buildingsVisible) {
      for (const layer of BUILDING_LAYERS) {
        if (map.getLayer?.(layer)) {
          map.setLayoutProperty(layer, 'visibility', 'visible');
        }
      }
    }

    function tick(now: number) {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / FADE_DURATION, 1);
      const opacity = START_OPACITY + (END_OPACITY - START_OPACITY) * progress;
      map?.setPaintProperty?.('buildings-unclustered', 'circle-opacity', opacity);
      map?.setPaintProperty?.('clusters', 'circle-opacity', opacity * (0.7 / 0.85));

      if (progress < 1) {
        requestAnimationFrame(tick);
      } else if (!buildingsVisible) {
        for (const layer of BUILDING_LAYERS) {
          if (map?.getLayer?.(layer)) {
            map?.setLayoutProperty?.(layer, 'visibility', 'none');
          }
        }
      }
    }

    requestAnimationFrame(tick);
  }, [buildingsVisible]);

  // Toggle listings layer visibility with opacity fade
  useEffect(() => {
    const map = mapRef.current as {
      setPaintProperty?: (layer: string, prop: string, val: number) => void;
      setLayoutProperty?: (layer: string, prop: string, val: string) => void;
      getLayer?: (id: string) => unknown;
      getPaintProperty?: (layer: string, prop: string) => number;
    } | null;
    if (!map?.setLayoutProperty || !map?.getLayer?.('listings-markers')) return;

    const FADE_DURATION = 300;
    const START_OPACITY = listingsVisible ? 0 : 0.9;
    const END_OPACITY = listingsVisible ? 0.9 : 0;
    const startTime = performance.now();

    if (listingsVisible) {
      map.setLayoutProperty('listings-markers', 'visibility', 'visible');
    }

    function tick(now: number) {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / FADE_DURATION, 1);
      const opacity = START_OPACITY + (END_OPACITY - START_OPACITY) * progress;
      map?.setPaintProperty?.('listings-markers', 'circle-opacity', opacity);

      if (progress < 1) {
        requestAnimationFrame(tick);
      } else if (!listingsVisible) {
        map?.setLayoutProperty?.('listings-markers', 'visibility', 'none');
      }
    }

    requestAnimationFrame(tick);
  }, [listingsVisible]);

  // Toggle quartiere layers visibility with opacity fade
  useEffect(() => {
    const map = mapRef.current as {
      setPaintProperty?: (layer: string, prop: string, val: number) => void;
      setLayoutProperty?: (layer: string, prop: string, val: string) => void;
      getLayer?: (id: string) => unknown;
    } | null;
    if (!map?.setLayoutProperty || !map?.getLayer?.('quartiere-fill')) return;

    const FADE_DURATION = 300;
    const START_OPACITY = quartiereVisible ? 0 : 0.65;
    const END_OPACITY = quartiereVisible ? 0.65 : 0;
    const startTime = performance.now();

    if (quartiereVisible) {
      for (const layer of QUARTIERE_LAYERS) {
        if (map.getLayer?.(layer)) {
          map.setLayoutProperty(layer, 'visibility', 'visible');
        }
      }
    }

    function tick(now: number) {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / FADE_DURATION, 1);
      const opacity = START_OPACITY + (END_OPACITY - START_OPACITY) * progress;
      map?.setPaintProperty?.('quartiere-fill', 'fill-opacity', opacity);

      if (progress < 1) {
        requestAnimationFrame(tick);
      } else if (!quartiereVisible) {
        for (const layer of QUARTIERE_LAYERS) {
          if (map?.getLayer?.(layer)) {
            map?.setLayoutProperty?.(layer, 'visibility', 'none');
          }
        }
        setQuartierProfile(null);
      }
    }

    requestAnimationFrame(tick);

    if (!quartiereVisible) setQuartierProfile(null);
  }, [quartiereVisible]);

  // Toggle noise layer visibility
  useEffect(() => {
    const map = mapRef.current as {
      setLayoutProperty?: (layer: string, prop: string, val: string) => void;
      getLayer?: (id: string) => unknown;
    } | null;
    if (!map?.setLayoutProperty || !map?.getLayer?.('noise-segments')) return;
    map.setLayoutProperty('noise-segments', 'visibility', noiseVisible ? 'visible' : 'none');
  }, [noiseVisible]);

  // Update choropleth color when active metric changes
  useEffect(() => {
    const map = mapRef.current as {
      setPaintProperty?: (layer: string, prop: string, val: unknown) => void;
      getLayer?: (id: string) => unknown;
    } | null;
    if (!map?.setPaintProperty || !map?.getLayer?.('quartiere-fill')) return;
    map.setPaintProperty('quartiere-fill', 'fill-color', quartierFillColor(activeMetric));
  }, [activeMetric]);

  // Popup rendering — re-render with real data once fetched
  useEffect(() => {
    if (!mapRef.current || !popup || !popupCoords) return;

    async function updatePopup() {
      const mod = await import('maplibre-gl');
      const maplibregl = mod.default ?? mod;

      // If there's an existing popup root (skeleton), update it in-place
      const existingRoot = popupRootRef.current;
      if (existingRoot) {
        existingRoot.render(
          createElement(BuildingPopup, {
            summary: popup!,
            listings: popupListings ?? undefined,
          })
        );
        return;
      }

      // Fallback: create fresh popup (skeleton was never shown)
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
      const mp = new PopupClass({ closeOnClick: true, maxWidth: '340px' })
        .setLngLat(popupCoords!)
        .setDOMContent(el)
        .addTo(mapRef.current as Parameters<typeof mp.addTo>[0]);

      mp.on('close', () => {
        popupRootRef.current?.unmount();
        popupRootRef.current = null;
        setPopup(null);
        setPopupListings(null);
      });
      popupRef.current = mp;
    }

    updatePopup();
  }, [popup, popupCoords, popupListings]);

  function handleLayerToggle(key: string) {
    switch (key) {
      case 'buildings':
        setBuildingsVisible((v) => !v);
        break;
      case 'listings':
        setListingsVisible((v) => !v);
        break;
      case 'quartiere':
        setQuartiereVisible((v) => !v);
        break;
      case 'noise':
        setNoiseVisible((v) => !v);
        break;
    }
  }

  if (error) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-strata-slate-900 text-strata-terracotta">
        <p>Map failed to load: {error}</p>
      </div>
    );
  }

  return (
    <div className="relative h-screen w-screen" data-testid="map-container">
      <div ref={containerRef} className="absolute inset-0" />
      <TopBar />
      {/* Top-left below TopBar: layer toggles */}
      <div className="absolute top-16 left-4 z-10 animate-fadeSlideUp">
        <LayerPanel
          buildingsVisible={buildingsVisible}
          listingsVisible={listingsVisible}
          quartiereVisible={quartiereVisible}
          noiseVisible={noiseVisible}
          activeMetric={activeMetric}
          onToggle={handleLayerToggle}
          onMetricChange={setActiveMetric}
        />
      </div>
      {/* Bottom-left: construction era legend */}
      <div className="absolute bottom-8 left-4 z-10 animate-fadeSlideUp">
        <Legend />
      </div>
      {/* Bottom-right: quartier profile panel */}
      {quartierProfile && (
        <div className="absolute bottom-8 right-4 z-10 animate-fadeSlideUp">
          <QuartierProfile
            profile={quartierProfile}
            onClose={() => setQuartierProfile(null)}
          />
        </div>
      )}
      <MapLoadingOverlay visible={!mapLoaded} />
    </div>
  );
}
