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
        <p data-testid="barchart-title" className="strata-panel-title mb-2">
          {title}
        </p>
      )}
      <ul className="space-y-1.5">
        {buckets.map(({ bucket, pct }) => (
          <li key={bucket} className="flex items-center gap-2.5">
            <span className="strata-data w-10 flex-shrink-0 text-right text-2xs text-strata-cream/55">
              {bucket}
            </span>
            <div className="h-[5px] flex-1 overflow-hidden rounded-full bg-strata-stone-700/35">
              <div
                data-testid="bar-segment"
                className="h-full rounded-full bg-gradient-to-r from-strata-amber/70 to-strata-amber transition-[width] duration-500 ease-out"
                style={{ width: `${pct}%` }}
              />
            </div>
            <span className="strata-data w-8 flex-shrink-0 text-2xs text-strata-cream/55">
              {Number(pct.toFixed(1))}%
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
