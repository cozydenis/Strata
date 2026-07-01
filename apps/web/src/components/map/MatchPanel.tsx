import {
  DIMENSION_LABELS,
  MATCH_DIMENSIONS,
  type MatchDimension,
  type MatchPreferences,
} from '@/lib/match/preferences';

interface MatchPanelProps {
  preferences: MatchPreferences;
  onChange: (prefs: MatchPreferences) => void;
  onReset: () => void;
}

const WEIGHT_OPTIONS: { value: number; label: string; title: string }[] = [
  { value: 0, label: '–', title: "Don't care" },
  { value: 1, label: '•', title: 'Matters' },
  { value: 2, label: '★', title: 'Very important' },
];

function WeightControl({
  dimension,
  weight,
  onSelect,
}: {
  dimension: MatchDimension;
  weight: number;
  onSelect: (value: number) => void;
}) {
  return (
    <div
      className="flex items-center justify-between gap-2"
      data-testid={`match-dim-${dimension}`}
    >
      <span className="flex-1 text-xs-11 text-strata-cream/70">{DIMENSION_LABELS[dimension]}</span>
      <div className="flex gap-0.5" role="group" aria-label={DIMENSION_LABELS[dimension]}>
        {WEIGHT_OPTIONS.map(({ value, label, title }) => {
          const active = weight === value;
          return (
            <button
              key={value}
              type="button"
              title={title}
              aria-pressed={active}
              data-testid={`match-dim-${dimension}-weight-${value}`}
              onClick={() => onSelect(value)}
              className={`h-6 w-6 rounded-md border text-2xs transition-colors duration-150 ${
                active
                  ? 'border-strata-amber bg-strata-amber font-medium text-strata-slate-900'
                  : 'border-strata-cream/15 bg-transparent text-strata-cream/50 hover:border-strata-cream/40 hover:text-strata-cream'
              }`}
            >
              {label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

export function MatchPanel({ preferences, onChange, onReset }: MatchPanelProps) {
  function handleSelect(dimension: MatchDimension, value: number) {
    // Immutable update — never mutate the incoming preferences object.
    onChange({
      weights: { ...preferences.weights, [dimension]: value },
    });
  }

  return (
    <div className="strata-panel w-56 p-3.5" data-testid="match-panel">
      <div className="mb-2.5 flex items-baseline justify-between">
        <p className="strata-panel-title">Your match</p>
        <button
          type="button"
          onClick={onReset}
          data-testid="match-reset"
          className="text-2xs text-strata-cream/40 transition-colors hover:text-strata-cream"
        >
          Reset
        </button>
      </div>
      <div className="space-y-1.5">
        {MATCH_DIMENSIONS.map((dimension) => (
          <WeightControl
            key={dimension}
            dimension={dimension}
            weight={preferences.weights[dimension]}
            onSelect={(value) => handleSelect(dimension, value)}
          />
        ))}
      </div>
      <p className="mt-2.5 text-2xs leading-relaxed text-strata-cream/40">
        Weight what matters to you. Quartiere are shaded by how well they fit.
      </p>
    </div>
  );
}
