interface Props {
  visible: boolean;
}

export function MapLoadingOverlay({ visible }: Props) {
  return (
    <div
      className={`absolute inset-0 z-30 flex flex-col items-center justify-center bg-strata-slate-900 transition-opacity duration-300 ${
        visible ? 'opacity-100' : 'opacity-0 pointer-events-none'
      }`}
    >
      <span className="text-strata-cream text-[18px] font-medium tracking-[0.2em] uppercase mb-4">
        Strata
      </span>
      <div className="w-[120px] h-[2px] rounded-full bg-gradient-to-r from-strata-slate-700 via-strata-cream/30 to-strata-slate-700 bg-[length:200%_100%] animate-shimmer" />
    </div>
  );
}
