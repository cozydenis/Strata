import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BarChart } from './BarChart';

const defaultBuckets = [
  { bucket: '0-17', pct: 15 },
  { bucket: '18-29', pct: 20 },
  { bucket: '30-44', pct: 30 },
  { bucket: '45-64', pct: 25 },
  { bucket: '65+', pct: 10 },
];

describe('BarChart', () => {
  it('renders without crashing', () => {
    render(<BarChart buckets={defaultBuckets} />);
  });

  it('renders a bar for each bucket', () => {
    render(<BarChart buckets={defaultBuckets} />);
    const bars = screen.getAllByTestId('bar-segment');
    expect(bars.length).toBe(5);
  });

  it('renders all bucket labels', () => {
    render(<BarChart buckets={defaultBuckets} />);
    expect(screen.getByText('0-17')).toBeTruthy();
    expect(screen.getByText('18-29')).toBeTruthy();
    expect(screen.getByText('30-44')).toBeTruthy();
    expect(screen.getByText('45-64')).toBeTruthy();
    expect(screen.getByText('65+')).toBeTruthy();
  });

  it('renders pct values as text', () => {
    render(<BarChart buckets={defaultBuckets} />);
    expect(screen.getByText('15%')).toBeTruthy();
    expect(screen.getByText('30%')).toBeTruthy();
  });

  it('bar width reflects percentage', () => {
    render(<BarChart buckets={defaultBuckets} />);
    const bars = screen.getAllByTestId('bar-segment');
    const thirtyPctBar = bars.find(
      (b) => (b as HTMLElement).style.width === '30%',
    );
    expect(thirtyPctBar).toBeTruthy();
  });

  it('renders empty buckets array without crashing', () => {
    render(<BarChart buckets={[]} />);
  });

  it('renders a single bucket', () => {
    render(<BarChart buckets={[{ bucket: '0-17', pct: 100 }]} />);
    expect(screen.getByText('0-17')).toBeTruthy();
    expect(screen.getByText('100%')).toBeTruthy();
  });

  it('accepts an optional title', () => {
    render(<BarChart buckets={defaultBuckets} title="Age distribution" />);
    expect(screen.getByText('Age distribution')).toBeTruthy();
  });

  it('does not render title element when title not provided', () => {
    render(<BarChart buckets={defaultBuckets} />);
    expect(screen.queryByTestId('barchart-title')).toBeNull();
  });

  it('renders title with correct testid', () => {
    render(<BarChart buckets={defaultBuckets} title="Age distribution" />);
    expect(screen.getByTestId('barchart-title')).toBeTruthy();
  });

  it('bar pct 0 renders a zero-width bar', () => {
    render(<BarChart buckets={[{ bucket: '0-17', pct: 0 }]} />);
    const bar = screen.getByTestId('bar-segment');
    expect((bar as HTMLElement).style.width).toBe('0%');
  });
});
