'use client';

import { useEffect, useState } from 'react';
import { api, ApiError } from '@/lib/apiClient';

type Toggle = { key: string; enabled: boolean; updated_at: string };

const TOGGLE_LABELS: Record<string, { label: string; description: string }> = {
  keyword_analysis: {
    label: 'Keyword matching',
    description: 'Continuously check incoming messages against the watched-keyword list.',
  },
  propensity_scoring: {
    label: 'Live propensity scoring',
    description: 'Automatically score a live "yes" vote on a recognizable yes/no poll the instant it arrives.',
  },
};

/** Global operator kill-switches -- pause either automated pipeline without disconnecting
 * WhatsApp itself. Ported from poison-br09/whatsapp-propensity-scoring's start/stop endpoints,
 * but gated with the dashboard's own super_admin JWT rather than an API key embedded in the
 * frontend build (that would leak a server secret to anyone viewing the page source). */
export function FeatureTogglesPanel() {
  const [toggles, setToggles] = useState<Toggle[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadFailed, setLoadFailed] = useState(false);

  async function refresh() {
    try {
      setToggles(await api.get<Toggle[]>('/api/v1/feature-toggles'));
      setLoadFailed(false);
    } catch (err) {
      setLoadFailed(true);
      setError(err instanceof ApiError ? err.message : 'Failed to load automation switches');
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function toggle(key: string, enabled: boolean) {
    setBusy(true);
    setError(null);
    try {
      await api.post(`/api/v1/feature-toggles/${encodeURIComponent(key)}/${enabled ? 'enable' : 'disable'}`);
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to update toggle');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="card">
      <h3 style={{ marginTop: 0 }}>Automation switches</h3>
      {error && <div className="error">{error}</div>}
      {loadFailed ? null : !toggles ? (
        <p className="muted">Loading...</p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 8 }}>
          {toggles.map((t) => {
            const meta = TOGGLE_LABELS[t.key] ?? { label: t.key, description: '' };
            return (
              <div key={t.key} className="row" style={{ justifyContent: 'space-between' }}>
                <div>
                  <div className="row"><strong>{meta.label}</strong> <span className={`badge ${t.enabled ? 'connected' : 'revoked'}`}>{t.enabled ? 'On' : 'Off'}</span></div>
                  {meta.description && <div className="muted" style={{ marginTop: 2 }}>{meta.description}</div>}
                </div>
                <button
                  className={t.enabled ? 'danger' : 'secondary'}
                  disabled={busy}
                  onClick={() => toggle(t.key, !t.enabled)}
                >
                  {t.enabled ? 'Turn off' : 'Turn on'}
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
