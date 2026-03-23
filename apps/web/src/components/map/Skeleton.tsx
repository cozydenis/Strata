export function SkeletonLine({ width = 'w-full' }: { width?: string }) {
  return (
    <div
      className={`h-3 ${width} rounded-sm bg-strata-slate-700/50 animate-shimmer bg-gradient-to-r from-strata-slate-700/50 via-strata-slate-600/50 to-strata-slate-700/50 bg-[length:200%_100%]`}
    />
  );
}

export function SkeletonBlock({ height = 'h-12' }: { height?: string }) {
  return (
    <div
      className={`w-full ${height} rounded-md bg-strata-slate-700/50 animate-shimmer bg-gradient-to-r from-strata-slate-700/50 via-strata-slate-600/50 to-strata-slate-700/50 bg-[length:200%_100%]`}
    />
  );
}

export function PopupSkeleton() {
  return (
    <div className="p-4 space-y-3 min-w-[260px]">
      <SkeletonLine width="w-3/4" />
      <SkeletonLine width="w-1/2" />
      <div className="border-t border-strata-cream/10 my-2" />
      <div className="flex gap-3">
        <SkeletonLine width="w-1/4" />
        <SkeletonLine width="w-1/4" />
        <SkeletonLine width="w-1/4" />
      </div>
      <SkeletonBlock height="h-[72px]" />
      <SkeletonLine width="w-2/3" />
    </div>
  );
}
