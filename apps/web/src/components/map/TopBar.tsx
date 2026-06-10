export function TopBar() {
  return (
    <div className="absolute top-4 left-4 z-20">
      <div className="strata-panel px-4 py-2.5">
        <div className="flex items-baseline gap-2">
          <span className="text-strata-cream text-base-13 font-semibold tracking-[0.28em] uppercase">
            Strata
          </span>
          <span className="h-1 w-1 rounded-full bg-strata-amber translate-y-[-2px]" aria-hidden />
        </div>
        <p className="mt-0.5 text-2xs tracking-[0.08em] text-strata-cream/40">
          Zürich · housing intelligence
        </p>
      </div>
    </div>
  );
}
