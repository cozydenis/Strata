'use client';

import { relativeTime } from '@/lib/time';
import { airLevelColor, type AirLevel } from '@/lib/map/air-colors';

export interface AirParameter {
  latest: number | null;
  mean_24h: number | null;
  unit: string;
  level: string | null;
}

export interface AirStation {
  station: string;
  name?: string;
  level?: AirLevel | string | null;
  measured_at?: string | null;
  parameters: Record<string, AirParameter>;
}

interface Props {
  station: AirStation;
}

/**
 * Build an AirStation from raw MapLibre feature properties. MapLibre serializes
 * nested property values (the `parameters` object) to JSON strings, so this
 * safely re-parses them and narrows the primitive fields.
 */
export function parseAirStation(
  props: Record<string, unknown> | null | undefined,
): AirStation | null {
  if (!props) return null;
  const station = typeof props.station === 'string' ? props.station : undefined;
  const name = typeof props.name === 'string' ? props.name : undefined;
  if (!station && !name) return null;

  let parameters: Record<string, AirParameter> = {};
  const raw = props.parameters;
  if (typeof raw === 'string') {
    try {
      const parsed: unknown = JSON.parse(raw);
      if (parsed && typeof parsed === 'object') {
        parameters = parsed as Record<string, AirParameter>;
      }
    } catch {
      parameters = {};
    }
  } else if (raw && typeof raw === 'object') {
    parameters = raw as Record<string, AirParameter>;
  }

  return {
    station: station ?? name ?? 'Station',
    name,
    level: typeof props.level === 'string' ? props.level : null,
    measured_at: typeof props.measured_at === 'string' ? props.measured_at : null,
    parameters,
  };
}

// Preferred display order for the common pollutants; anything else is appended.
const PARAM_ORDER = ['NO2', 'O3', 'PM10', 'PM2.5', 'NO', 'NOx'];

const LEVEL_LABEL: Record<string, string> = {
  good: 'Good',
  moderate: 'Moderate',
  high: 'High',
};

/** Round to at most one decimal and drop a trailing ".0". */
function formatValue(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return '—';
  return Number(value.toFixed(1)).toString();
}

function orderedParamKeys(parameters: Record<string, AirParameter>): string[] {
  const keys = Object.keys(parameters);
  const preferred = PARAM_ORDER.filter((k) => keys.includes(k));
  const rest = keys.filter((k) => !PARAM_ORDER.includes(k));
  return [...preferred, ...rest];
}

export function AirQualityPopup({ station }: Props) {
  const title = station.name ?? station.station;
  const level = station.level ?? null;
  const levelLabel = level ? (LEVEL_LABEL[level] ?? level) : 'No data';
  const keys = orderedParamKeys(station.parameters);

  return (
    <div className="w-[300px] p-4 animate-fadeSlideUp">
      {/* Header: station + overall level */}
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-lg-15 font-semibold tracking-tight text-strata-cream">{title}</p>
          <p className="mt-0.5 text-2xs uppercase tracking-[0.18em] text-strata-muted">Air quality</p>
        </div>
        <span
          data-testid="air-level"
          className="inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-2xs font-medium text-strata-cream/85"
          style={{ backgroundColor: `${airLevelColor(level)}33` }}
        >
          <span
            aria-hidden
            className="inline-block h-1.5 w-1.5 rounded-full"
            style={{ backgroundColor: airLevelColor(level) }}
          />
          {levelLabel}
        </span>
      </div>

      {/* Per-parameter table */}
      <div className="strata-rule my-3" />
      <div className="grid grid-cols-[auto_1fr_1fr] gap-x-3 gap-y-1 text-xs-11">
        <span className="text-2xs uppercase tracking-[0.14em] text-strata-muted">Pollutant</span>
        <span className="text-right text-2xs uppercase tracking-[0.14em] text-strata-muted">Latest</span>
        <span className="text-right text-2xs uppercase tracking-[0.14em] text-strata-muted">24 h mean</span>
        {keys.map((key) => {
          const p = station.parameters[key];
          return (
            <div key={key} data-testid="air-param-row" className="contents">
              <span className="flex items-center gap-1.5 text-strata-cream/80">
                <span
                  aria-hidden
                  className="inline-block h-1.5 w-1.5 rounded-full"
                  style={{ backgroundColor: airLevelColor(p.level) }}
                />
                {key}
              </span>
              <span className="strata-data text-right text-strata-cream/85">
                {formatValue(p.latest)}
                <span className="ml-1 text-strata-muted">{p.unit}</span>
              </span>
              <span className="strata-data text-right text-strata-cream/70">
                {formatValue(p.mean_24h)}
              </span>
            </div>
          );
        })}
      </div>

      {/* Measured-at footer */}
      <div className="strata-rule my-3" />
      <p data-testid="air-measured-at" className="text-2xs text-strata-muted">
        {station.measured_at ? `Measured ${relativeTime(station.measured_at)}` : 'Measurement time unavailable'}
      </p>
    </div>
  );
}
