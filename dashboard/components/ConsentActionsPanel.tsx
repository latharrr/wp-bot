'use client';

import { useState } from 'react';
import { api, ApiError } from '@/lib/apiClient';
import { ConsentStatusBadge } from '@/components/ConsentStatusBadge';

type Member = {
  member_jid: string;
  phone: string | null;
  display_name: string | null;
};

type MemberConsent = {
  member_phone: string;
  opted_in: boolean;
  opt_in_method: string;
};

export function ConsentActionsPanel({
  groupJid,
  consentStatus,
  members,
  memberConsent,
  onChanged,
}: {
  groupJid: string;
  consentStatus: string;
  members: Member[];
  memberConsent: MemberConsent[];
  onChanged: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const consentByPhone = new Map(memberConsent.map((m) => [m.member_phone, m]));
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

  function optIn(phone: string) {
    run(() =>
      api.post(`/api/v1/groups/${encodeURIComponent(groupJid)}/consent/members/${encodeURIComponent(phone)}/opt-in`, {
        reason: 'manual admin override (verbal consent)',
      }),
    );
  }

  function optOut(phone: string) {
    run(() => api.post(`/api/v1/groups/${encodeURIComponent(groupJid)}/consent/members/${encodeURIComponent(phone)}/opt-out`, {}));
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

      {members.length > 0 && (
        <table style={{ marginTop: 14 }}>
          <thead>
            <tr><th>Name</th><th>Phone</th><th>Status</th><th></th></tr>
          </thead>
          <tbody>
            {members.map((member) => {
              const phone = member.phone;
              const consent = phone ? consentByPhone.get(phone) : undefined;
              const isOptedIn = consent?.opted_in ?? false;
              return (
                <tr key={member.member_jid}>
                  <td>{member.display_name ?? '—'}</td>
                  <td>{phone ?? '—'}</td>
                  <td>
                    {isOptedIn
                      ? `Opted in (${consent?.opt_in_method})`
                      : consent
                        ? 'Opted out'
                        : 'No response yet'}
                  </td>
                  <td>
                    {!phone ? null : isOptedIn ? (
                      <button className="secondary" disabled={busy} onClick={() => optOut(phone)}>Opt out</button>
                    ) : (
                      <button className="secondary" disabled={busy} onClick={() => optIn(phone)}>Opt in (verbal)</button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}
