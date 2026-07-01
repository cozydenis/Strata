'use client';

import { useState } from 'react';
import type { HerabsetzungPayload } from '@/lib/api';
import { generateHerabsetzung } from '@/lib/api';

interface HerabsetzungDialogProps {
  listingId: number;
  onClose: () => void;
}

const NO_REDUCTION_MESSAGE =
  'Für dieses Inserat besteht aktuell kein Anspruch auf eine Mietzinssenkung.';
const GENERIC_ERROR_MESSAGE = 'Das Schreiben konnte nicht erstellt werden. Bitte erneut versuchen.';
const REQUIRED_NAME_MESSAGE = 'Bitte den Namen der Mieterin / des Mieters angeben.';

function getErrorMessage(error: unknown): string {
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return GENERIC_ERROR_MESSAGE;
}

/** Copy text to clipboard with a document.execCommand fallback for older browsers. */
async function copyToClipboard(text: string): Promise<void> {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return;
  }
  const textarea = document.createElement('textarea');
  textarea.value = text;
  textarea.style.position = 'fixed';
  textarea.style.opacity = '0';
  document.body.appendChild(textarea);
  textarea.select();
  try {
    document.execCommand('copy');
  } finally {
    document.body.removeChild(textarea);
  }
}

function downloadLetter(text: string, listingId: number): void {
  const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = `herabsetzungsbegehren-${listingId}.txt`;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(url);
}

const inputClass =
  'w-full rounded-md border border-strata-cream/[0.12] bg-strata-slate-800/60 px-2.5 py-1.5 text-xs-11 text-strata-cream placeholder:text-strata-cream/30 focus:border-strata-amber/50 focus:outline-none';
const labelClass = 'mb-1 block text-2xs text-strata-cream/50';

export function HerabsetzungDialog({ listingId, onClose }: HerabsetzungDialogProps) {
  const [tenantName, setTenantName] = useState('');
  const [tenantAddress, setTenantAddress] = useState('');
  const [landlordName, setLandlordName] = useState('');
  const [landlordAddress, setLandlordAddress] = useState('');
  const [letter, setLetter] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [copied, setCopied] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!tenantName.trim()) {
      setError(REQUIRED_NAME_MESSAGE);
      return;
    }
    setError(null);
    setSubmitting(true);
    const payload: HerabsetzungPayload = {
      tenant_name: tenantName.trim(),
      tenant_address: tenantAddress.trim() || undefined,
      landlord_name: landlordName.trim() || undefined,
      landlord_address: landlordAddress.trim() || undefined,
    };
    try {
      const result = await generateHerabsetzung(listingId, payload);
      if (result.status === 'no_reduction') {
        setError(NO_REDUCTION_MESSAGE);
      } else {
        setLetter(result.data.letter);
      }
    } catch (err: unknown) {
      setError(getErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleCopy() {
    if (!letter) return;
    try {
      await copyToClipboard(letter);
      setCopied(true);
    } catch {
      setError('Kopieren fehlgeschlagen. Bitte den Text manuell markieren.');
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      role="dialog"
      aria-modal="true"
      aria-label="Herabsetzungsbegehren erstellen"
      data-testid="herabsetzung-dialog"
    >
      <div className="strata-panel w-full max-w-md p-4">
        <div className="mb-3 flex items-start justify-between">
          <p className="strata-panel-title">Herabsetzungsbegehren</p>
          <button
            onClick={onClose}
            data-testid="herabsetzung-close"
            className="-mr-1 -mt-1 rounded-md p-1 text-[15px] leading-none text-strata-cream/35 transition-colors hover:bg-strata-cream/5 hover:text-strata-cream"
            aria-label="Schliessen"
          >
            ×
          </button>
        </div>

        {letter === null ? (
          <form onSubmit={handleSubmit} data-testid="herabsetzung-form">
            <p className="mb-3 text-2xs leading-relaxed text-strata-cream/45">
              Erstellt ein formelles Schreiben zur Mietzinssenkung an die Verwaltung.
            </p>

            <div className="mb-2">
              <label htmlFor="tenant-name" className={labelClass}>
                Name Mieter:in *
              </label>
              <input
                id="tenant-name"
                data-testid="field-tenant-name"
                className={inputClass}
                value={tenantName}
                onChange={(e) => setTenantName(e.target.value)}
                placeholder="Anna Muster"
              />
            </div>

            <div className="mb-2">
              <label htmlFor="tenant-address" className={labelClass}>
                Adresse Mieter:in
              </label>
              <input
                id="tenant-address"
                data-testid="field-tenant-address"
                className={inputClass}
                value={tenantAddress}
                onChange={(e) => setTenantAddress(e.target.value)}
                placeholder="Langstrasse 1, 8004 Zürich"
              />
            </div>

            <div className="mb-2">
              <label htmlFor="landlord-name" className={labelClass}>
                Name Verwaltung / Vermieter:in
              </label>
              <input
                id="landlord-name"
                data-testid="field-landlord-name"
                className={inputClass}
                value={landlordName}
                onChange={(e) => setLandlordName(e.target.value)}
                placeholder="Immo AG"
              />
            </div>

            <div className="mb-3">
              <label htmlFor="landlord-address" className={labelClass}>
                Adresse Verwaltung
              </label>
              <input
                id="landlord-address"
                data-testid="field-landlord-address"
                className={inputClass}
                value={landlordAddress}
                onChange={(e) => setLandlordAddress(e.target.value)}
                placeholder="Bahnhofstrasse 1, 8001 Zürich"
              />
            </div>

            {error && (
              <p className="mb-2 text-xs-11 text-strata-terracotta" data-testid="herabsetzung-error">
                {error}
              </p>
            )}

            <button
              type="submit"
              data-testid="herabsetzung-submit"
              disabled={submitting}
              className="w-full rounded-md border border-strata-amber/30 bg-strata-amber/10 px-3 py-1.5 text-xs-11 font-medium text-strata-amber transition-colors hover:bg-strata-amber/20 disabled:opacity-50"
            >
              {submitting ? 'Wird erstellt…' : 'Schreiben erstellen'}
            </button>
          </form>
        ) : (
          <div data-testid="herabsetzung-result">
            <pre
              data-testid="herabsetzung-letter"
              className="strata-scroll strata-data max-h-[320px] overflow-y-auto whitespace-pre-wrap rounded-md border border-strata-cream/[0.08] bg-strata-slate-800/60 p-3 text-2xs leading-relaxed text-strata-cream/90"
            >
              {letter}
            </pre>
            <div className="mt-3 flex gap-2">
              <button
                onClick={handleCopy}
                data-testid="herabsetzung-copy"
                className="flex-1 rounded-md border border-strata-cream/[0.12] px-3 py-1.5 text-xs-11 text-strata-cream/80 transition-colors hover:bg-strata-cream/[0.06]"
              >
                {copied ? 'Kopiert ✓' : 'Kopieren'}
              </button>
              <button
                onClick={() => downloadLetter(letter, listingId)}
                data-testid="herabsetzung-download"
                className="flex-1 rounded-md border border-strata-amber/30 bg-strata-amber/10 px-3 py-1.5 text-xs-11 font-medium text-strata-amber transition-colors hover:bg-strata-amber/20"
              >
                Download .txt
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
