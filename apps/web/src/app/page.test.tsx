import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import HomePage from './page';

describe('HomePage', () => {
  it('renders the Strata heading', () => {
    render(<HomePage />);
    expect(screen.getByRole('heading', { name: /strata/i })).toBeInTheDocument();
  });

  it('renders the description', () => {
    render(<HomePage />);
    expect(screen.getByText(/zurich housing market/i)).toBeInTheDocument();
  });
});
