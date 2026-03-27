interface Bucket {
  bucket: string;
  pct: number;
}

interface BarChartProps {
  buckets: Bucket[];
  title?: string;
}

export function BarChart({ buckets, title }: BarChartProps) {
  return (
    <div className="w-full">
      {title && (
        <p
          data-testid="barchart-title"
          className="text-2xs font-semibold uppercase tracking-widest text-strata-cream/50 mb-1"
        >
          {title}
        </p>
      )}
      <ul className="space-y-1">
        {buckets.map(({ bucket, pct }) => (
          <li key={bucket} className="flex items-center gap-2">
            <span className="w-10 text-right text-2xs text-strata-cream/60 flex-shrink-0">
              {bucket}
            </span>
            <div className="flex-1 bg-strata-stone-700/40 rounded-full h-2 overflow-hidden">
              <div
                data-testid="bar-segment"
                className="h-2 rounded-full bg-strata-amber"
                style={{ width: `${pct}%` }}
              />
            </div>
            <span className="w-8 text-2xs text-strata-cream/60 flex-shrink-0">
              {pct}%
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
