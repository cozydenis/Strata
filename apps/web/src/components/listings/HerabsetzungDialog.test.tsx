import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { HerabsetzungDialog } from './HerabsetzungDialog';

vi.mock('@/lib/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/api')>();
  return {
    ...actual,
    generateHerabsetzung: vi.fn(),
  };
});

import { generateHerabsetzung } from '@/lib/api';

const mockGenerate = vi.mocked(generateHerabsetzung);

beforeEach(() => {
  mockGenerate.mockReset();
});

function fillTenantName(value = 'Anna Muster') {
  fireEvent.change(screen.getByTestId('field-tenant-name'), { target: { value } });
}

describe('HerabsetzungDialog', () => {
  it('shows a validation message when tenant name is empty on submit', async () => {
    render(<HerabsetzungDialog listingId={42} onClose={() => {}} />);

    fireEvent.click(screen.getByTestId('herabsetzung-submit'));

    expect(screen.getByTestId('herabsetzung-error').textContent).toBeTruthy();
    expect(mockGenerate).not.toHaveBeenCalled();
  });

  it('submits and renders the returned letter text', async () => {
    mockGenerate.mockResolvedValueOnce({
      status: 'ok',
      data: { listing_id: 42, basis: 'known', letter: 'Sehr geehrte Damen und Herren, Herabsetzung.' },
    });
    render(<HerabsetzungDialog listingId={42} onClose={() => {}} />);

    fillTenantName();
    fireEvent.click(screen.getByTestId('herabsetzung-submit'));

    const letter = await screen.findByTestId('herabsetzung-letter');
    expect(letter.textContent).toContain('Herabsetzung');
    expect(mockGenerate).toHaveBeenCalledWith(42, expect.objectContaining({ tenant_name: 'Anna Muster' }));
  });

  it('shows a friendly German message on a 409 no_reduction result', async () => {
    mockGenerate.mockResolvedValueOnce({ status: 'no_reduction' });
    render(<HerabsetzungDialog listingId={42} onClose={() => {}} />);

    fillTenantName();
    fireEvent.click(screen.getByTestId('herabsetzung-submit'));

    const err = await screen.findByTestId('herabsetzung-error');
    expect(err.textContent).toMatch(/keine|kein|Mietzinssenkung/i);
    expect(screen.queryByTestId('herabsetzung-letter')).toBeNull();
  });

  it('shows an inline error message when the request throws (validation)', async () => {
    mockGenerate.mockRejectedValueOnce(new Error('tenant_name is required'));
    render(<HerabsetzungDialog listingId={42} onClose={() => {}} />);

    fillTenantName();
    fireEvent.click(screen.getByTestId('herabsetzung-submit'));

    const err = await screen.findByTestId('herabsetzung-error');
    expect(err.textContent).toContain('tenant_name is required');
  });

  it('copies the letter to the clipboard when Copy is clicked', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText } });

    mockGenerate.mockResolvedValueOnce({
      status: 'ok',
      data: { listing_id: 42, basis: 'known', letter: 'LETTER-BODY' },
    });
    render(<HerabsetzungDialog listingId={42} onClose={() => {}} />);

    fillTenantName();
    fireEvent.click(screen.getByTestId('herabsetzung-submit'));

    await screen.findByTestId('herabsetzung-letter');
    fireEvent.click(screen.getByTestId('herabsetzung-copy'));

    await waitFor(() => expect(writeText).toHaveBeenCalledWith('LETTER-BODY'));
  });

  it('calls onClose when the close button is clicked', () => {
    const onClose = vi.fn();
    render(<HerabsetzungDialog listingId={42} onClose={onClose} />);

    fireEvent.click(screen.getByTestId('herabsetzung-close'));
    expect(onClose).toHaveBeenCalled();
  });
});
