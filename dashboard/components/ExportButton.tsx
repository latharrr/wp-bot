'use client';

import { useState } from 'react';
import { api, ApiError } from '@/lib/apiClient';

/** The shared "one tap export" button: authenticated fetch -> blob -> browser download.
 * `locked` renders a disabled state with a reason instead of letting the click 403. */
export function ExportButton({
  path,
  filename,
  label = 'Export to Excel',
  locked,
  lockedReason,
}: {
  path: string;
  filename: string;
  label?: string;
  locked?: boolean;
  lockedReason?: string;
}) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (locked) {
    return (
      <div>
        <button className="secondary" disabled title={lockedReason}>
          🔒 {label}
        </button>
        {lockedReason && <div className="muted" style={{ marginTop: 6 }}>{lockedReason}</div>}
      </div>
    );
  }

  async function onClick() {
    setLoading(true);
    setError(null);
    try {
      await api.download(path, filename);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Export failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <button onClick={onClick} disabled={loading}>
        {loading ? 'Exporting...' : label}
      </button>
      {error && <div className="error">{error}</div>}
    </div>
  );
}
