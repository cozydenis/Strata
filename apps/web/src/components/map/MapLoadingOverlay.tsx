interface Props {
  visible: boolean;
}

export function MapLoadingOverlay({ visible }: Props) {
  return (
    <div
      className={`absolute inset-0 z-30 flex flex-col items-center justify-center bg-strata-slate-900 transition-opacity duration-500 ${
        visible ? 'opacity-100' : 'opacity-0 pointer-events-none'
      }`}
    >
      <span className="mb-2 text-[20px] font-semibold uppercase tracking-[0.35em] text-strata-cream">
        Strata
      </span>
      <p className="mb-6 text-xs-11 tracking-[0.08em] text-strata-cream/35">
        A living model of every home in Zürich
      </p>
      <div className="h-[2px] w-[120px] animate-shimmer rounded-full bg-gradient-to-r from-strata-slate-700 via-strata-amber/40 to-strata-slate-700 bg-[length:200%_100%]" />
    </div>
  );
}
