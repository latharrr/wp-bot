'use client';

import { useState } from 'react';
import { api, ApiError } from '@/lib/apiClient';
import { ConsentStatusBadge } from '@/components/ConsentStatusBadge';

type MemberConsent = {
  member_phone: string;
  opted_in: boolean;
  opt_in_method: string;
};

export function ConsentActionsPanel({
  groupJid,
  consentStatus,
  memberConsent,
  onChanged,
}: {
  groupJid: string;
  consentStatus: string;
  memberConsent: MemberConsent[];
  onChanged: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const optedInCount = memberConsent.filter((m) => m.opted_in).length;

  async function run(fn: () => Promise<unknown>) {
    setBusy(true);
    setError(null);
    try {
      await fn();
      onChanged();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Action failed');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="card">
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <div>
          <div className="row"><strong>Group consent</strong> <ConsentStatusBadge status={consentStatus} /></div>
          <div className="muted" style={{ marginTop: 4 }}>{optedInCount} member(s) opted in individually</div>
        </div>
        <div className="row">
          {consentStatus !== 'consented' && (
            <button
              disabled={busy}
              onClick={() => run(() => api.post(`/api/v1/groups/${encodeURIComponent(groupJid)}/consent/request`, {}))}
            >
              Request consent
            </button>
          )}
          {consentStatus !== 'consented' && (
            <button
              className="secondary"
              disabled={busy}
              onClick={() => run(() => api.post(`/api/v1/groups/${encodeURIComponent(groupJid)}/consent/mark-consented`, {}))}
            >
              Mark consented
            </button>
          )}
          {consentStatus === 'consented' && (
            <button
              className="danger"
              disabled={busy}
              onClick={() => run(() => api.post(`/api/v1/groups/${encodeURIComponent(groupJid)}/consent/revoke`, {}))}
            >
              Revoke consent
            </button>
          )}
        </div>
      </div>
      {error && <div className="error">{error}</div>}

      {memberConsent.length > 0 && (
        <table style={{ marginTop: 14 }}>
          <thead>
            <tr><th>Phone</th><th>Status</th><th>Method</th></tr>
          </thead>
          <tbody>
            {memberConsent.map((m) => (
              <tr key={m.member_phone}>
                <td>{m.member_phone}</td>
                <td>{m.opted_in ? 'Opted in' : 'Opted out'}</td>
                <td className="muted">{m.opt_in_method}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
