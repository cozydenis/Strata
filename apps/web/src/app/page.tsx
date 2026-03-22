'use client';

import type { Unit } from '@strata/shared';
import dynamic from 'next/dynamic';

// Type import validates workspace link at build time
type _UnitCheck = Unit;

const MapView = dynamic(
  () => import('@/components/map/Map').then((m) => m.MapView),
  { ssr: false },
);

export default function HomePage() {
  return (
    <main className="h-screen w-screen">
      <MapView />
    </main>
  );
}
