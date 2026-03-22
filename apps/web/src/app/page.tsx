import type { Unit } from '@strata/shared';

// Type import validates workspace link at build time
type _UnitCheck = Unit;

export default function HomePage() {
  return (
    <main>
      <h1>Strata</h1>
      <p>Spatial intelligence for the Zurich housing market.</p>
    </main>
  );
}
