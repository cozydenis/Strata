import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MatchPanel } from './MatchPanel';
import {
  DEFAULT_PREFERENCES,
  DIMENSION_LABELS,
  MATCH_DIMENSIONS,
  type MatchPreferences,
} from '@/lib/match/preferences';

const defaultProps = {
  preferences: DEFAULT_PREFERENCES,
  onChange: vi.fn(),
  onReset: vi.fn(),
};

describe('MatchPanel', () => {
  it('renders without crashing', () => {
    render(<MatchPanel {...defaultProps} />);
  });

  it('applies glass card styling', () => {
    const { container } = render(<MatchPanel {...defaultProps} />);
    const card = container.firstChild as HTMLElement;
    expect(card.className).toContain('strata-panel');
  });

  it('renders a control for every one of the seven dimensions', () => {
    render(<MatchPanel {...defaultProps} />);
    expect(MATCH_DIMENSIONS).toHaveLength(7);
    for (const dim of MATCH_DIMENSIONS) {
      expect(screen.getByTestId(`match-dim-${dim}`)).toBeTruthy();
    }
  });

  it('renders a green space row with weight controls', () => {
    render(<MatchPanel {...defaultProps} />);
    expect(screen.getByTestId('match-dim-green')).toBeTruthy();
    expect(screen.getByText('Green space')).toBeTruthy();
    expect(screen.getByTestId('match-dim-green-weight-2')).toBeTruthy();
  });

  it('calls onChange with an updated green weight', () => {
    const onChange = vi.fn();
    render(<MatchPanel {...defaultProps} onChange={onChange} />);
    fireEvent.click(screen.getByTestId('match-dim-green-weight-0'));
    const updated = onChange.mock.calls[0][0] as MatchPreferences;
    expect(updated.weights.green).toBe(0);
    expect(updated.weights.nightlife).toBe(1);
  });

  it('renders human-readable labels', () => {
    render(<MatchPanel {...defaultProps} />);
    expect(screen.getByText(DIMENSION_LABELS.nightlife)).toBeTruthy();
    expect(screen.getByText(DIMENSION_LABELS.calm)).toBeTruthy();
    expect(screen.getByText(DIMENSION_LABELS.upAndComing)).toBeTruthy();
    expect(screen.getByText(DIMENSION_LABELS.green)).toBeTruthy();
  });

  it('calls onChange with updated preferences when a control changes', () => {
    const onChange = vi.fn();
    render(<MatchPanel {...defaultProps} onChange={onChange} />);
    // Select "very important" (weight 2) for nightlife
    fireEvent.click(screen.getByTestId('match-dim-nightlife-weight-2'));
    expect(onChange).toHaveBeenCalledTimes(1);
    const updated = onChange.mock.calls[0][0] as MatchPreferences;
    expect(updated.weights.nightlife).toBe(2);
    // Other dimensions untouched
    expect(updated.weights.calm).toBe(1);
  });

  it('does not mutate the passed preferences object', () => {
    const onChange = vi.fn();
    const prefs = DEFAULT_PREFERENCES;
    render(<MatchPanel {...defaultProps} preferences={prefs} onChange={onChange} />);
    fireEvent.click(screen.getByTestId('match-dim-nightlife-weight-0'));
    expect(prefs.weights.nightlife).toBe(1); // original unchanged
  });

  it('calls onReset when the reset button is clicked', () => {
    const onReset = vi.fn();
    render(<MatchPanel {...defaultProps} onReset={onReset} />);
    fireEvent.click(screen.getByTestId('match-reset'));
    expect(onReset).toHaveBeenCalledOnce();
  });

  it('marks the active weight for a dimension', () => {
    const prefs: MatchPreferences = {
      weights: { ...DEFAULT_PREFERENCES.weights, nightlife: 2 },
    };
    render(<MatchPanel {...defaultProps} preferences={prefs} />);
    const active = screen.getByTestId('match-dim-nightlife-weight-2');
    expect(active.getAttribute('aria-pressed')).toBe('true');
    const inactive = screen.getByTestId('match-dim-nightlife-weight-1');
    expect(inactive.getAttribute('aria-pressed')).toBe('false');
  });
});
