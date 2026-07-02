import { describe, it, expect } from 'vitest';
import {
  GREEN_FILL_COLOR,
  GREEN_FILL_OPACITY,
  GREEN_OUTLINE_COLOR,
  GREEN_OUTLINE_WIDTH,
} from './green-colors';

const HEX_RE = /^#[0-9a-fA-F]{6}$/;

/** Sum of RGB channels — a simple relative-darkness proxy for hex colors. */
function channelSum(hex: string): number {
  return (
    parseInt(hex.slice(1, 3), 16) + parseInt(hex.slice(3, 5), 16) + parseInt(hex.slice(5, 7), 16)
  );
}

describe('green layer palette', () => {
  it('uses the design-system sage for the fill', () => {
    // --strata-sage in globals.css
    expect(GREEN_FILL_COLOR.toLowerCase()).toBe('#8fa071');
  });

  it('exposes valid 6-digit hex colors', () => {
    expect(GREEN_FILL_COLOR).toMatch(HEX_RE);
    expect(GREEN_OUTLINE_COLOR).toMatch(HEX_RE);
  });

  it('keeps the fill muted at 0.35 opacity', () => {
    expect(GREEN_FILL_OPACITY).toBe(0.35);
  });

  it('outline is darker than the fill', () => {
    expect(channelSum(GREEN_OUTLINE_COLOR)).toBeLessThan(channelSum(GREEN_FILL_COLOR));
  });

  it('outline is 1px wide', () => {
    expect(GREEN_OUTLINE_WIDTH).toBe(1);
  });
});
