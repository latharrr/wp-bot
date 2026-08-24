'use client';

import { useMemo, useState } from 'react';
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
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const consentByPhone = new Map(memberConsent.map((m) => [m.member_phone, m]));
  const optedInCount = memberConsent.filter((m) => m.opted_in).length;
  const noPhoneCount = members.filter((m) => !m.phone).length;

  // Only members with a phone that aren't already opted in are eligible for bulk verbal opt-in.
  const eligiblePhones = useMemo(
    () => members.map((m) => m.phone).filter((phone): phone is string => !!phone && !consentByPhone.get(phone)?.opted_in),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [members, memberConsent],
  );
  const allSelected = eligiblePhones.length > 0 && eligiblePhones.every((phone) => selected.has(phone));

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

  function toggleSelected(phone: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(phone)) next.delete(phone);
      else next.add(phone);
      return next;
    });
  }

  function toggleSelectAll() {
    setSelected(allSelected ? new Set() : new Set(eligiblePhones));
  }

  async function bulkOptIn() {
    if (selected.size === 0) return;
    await run(() =>
      api.post(`/api/v1/groups/${encodeURIComponent(groupJid)}/consent/members/bulk-opt-in`, {
        phones: Array.from(selected),
      }),
    );
    setSelected(new Set());
  }

  return (
    <div className="card">
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <div>
          <div className="row"><strong>Group consent</strong> <ConsentStatusBadge status={consentStatus} /></div>
          <div className="muted" style={{ marginTop: 4 }}>{optedInCount} member(s) opted in individually</div>
          {noPhoneCount > 0 && (
            <div className="muted" style={{ marginTop: 2 }}>
              {noPhoneCount} of {members.length} member(s) have no phone number disclosed by WhatsApp to this
              account — they can't be opted in or contacted through this app.
            </div>
          )}
        </div>
        <div className="row">
          {consentStatus !== 'consented' && (
            <button
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

      {eligiblePhones.length > 0 && (
        <button
          onClick={bulkOptIn}
          disabled={busy || selected.size === 0}
          style={{
            marginTop: 14,
            width: '100%',
            padding: '12px 16px',
            fontSize: 15,
            fontWeight: 700,
            background: selected.size > 0 ? 'var(--accent-hover)' : undefined,
          }}
        >
          {busy
            ? 'Opting in...'
            : selected.size > 0
              ? `Opt in ${selected.size} selected member(s) — verbal consent`
              : 'Select members below to opt in verbally'}
        </button>
      )}

      {members.length > 0 && (
        <div className="table-scroll">
        <table style={{ marginTop: 14 }}>
          <thead>
            <tr>
              <th>
                <input type="checkbox" checked={allSelected} onChange={toggleSelectAll} disabled={eligiblePhones.length === 0} />
              </th>
              <th>Name</th>
              <th>Phone</th>
              <th>Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {members.map((member) => {
              const phone = member.phone;
              const consent = phone ? consentByPhone.get(phone) : undefined;
              const isOptedIn = consent?.opted_in ?? false;
              return (
                <tr key={member.member_jid}>
                  <td>
                    {phone && !isOptedIn && (
                      <input type="checkbox" checked={selected.has(phone)} onChange={() => toggleSelected(phone)} />
                    )}
                  </td>
                  <td>{member.display_name ?? '—'}</td>
                  <td>{phone ?? <span className="muted">Not disclosed by WhatsApp</span>}</td>
                  <td>
                    {!phone
                      ? '—'
                      : isOptedIn
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
        </div>
      )}
    </div>
  );
}
