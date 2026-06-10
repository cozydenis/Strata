import { describe, it, expect } from 'vitest';
import { relativeTime } from './time';

const NOW = new Date('2026-06-10T12:00:00');

describe('relativeTime', () => {
  it('today for same-day timestamps', () => {
    expect(relativeTime('2026-06-10T08:00:00', NOW)).toBe('today');
  });
  it('yesterday', () => {
    expect(relativeTime('2026-06-09T08:00:00', NOW)).toBe('yesterday');
  });
  it('days', () => {
    expect(relativeTime('2026-06-03T08:00:00', NOW)).toBe('7 d ago');
  });
  it('months', () => {
    expect(relativeTime('2026-04-01T08:00:00', NOW)).toBe('2 mo ago');
  });
});
