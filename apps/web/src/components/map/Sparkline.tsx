interface SparklineProps {
  values: number[];
  label: string;
  width?: number;
  height?: number;
}

/** Tiny dependency-free inline SVG sparkline; renders nothing below 2 points. */
export function Sparkline({ values, label, width = 72, height = 20 }: SparklineProps) {
  if (values.length < 2) return null;

  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min;
  const pad = 2;

  const points = values
    .map((value, i) => {
      const x = pad + (i / (values.length - 1)) * (width - 2 * pad);
      // Flat series sits mid-height; otherwise higher values render higher (smaller y).
      const norm = span === 0 ? 0.5 : (value - min) / span;
      const y = pad + (1 - norm) * (height - 2 * pad);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(' ');

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      role="img"
      aria-label={label}
      className="inline-block align-middle"
    >
      <polyline
        points={points}
        fill="none"
        stroke="currentColor"
        strokeWidth={1.2}
        strokeLinejoin="round"
        strokeLinecap="round"
      />
    </svg>
  );
}
