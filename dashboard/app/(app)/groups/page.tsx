'use client';

import { useMemo, useState, useEffect } from 'react';
import Link from 'next/link';
import { api, ApiError } from '@/lib/apiClient';
import { ConsentStatusBadge } from '@/components/ConsentStatusBadge';
import { RequireFeature } from '@/components/RequireFeature';

type Group = {
  group_jid: string;
  group_name: string | null;
  member_count: number;
  consent_status: string;
  last_synced_at: string | null;
};

export default function GroupsPage() {
  return (
    <RequireFeature feature="groups">
      <GroupsPageContent />
    </RequireFeature>
  );
}

function GroupsPageContent() {
  const [groups, setGroups] = useState<Group[] | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function refresh() {
    return api.get<Group[]>('/api/v1/groups').then(setGroups);
  }

  useEffect(() => {
    refresh();
  }, []);

  const allJids = useMemo(() => (groups ?? []).map((g) => g.group_jid), [groups]);
  const allSelected = allJids.length > 0 && allJids.every((jid) => selected.has(jid));

  function toggleSelected(jid: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(jid)) next.delete(jid);
      else next.add(jid);
      return next;
    });
  }

  function toggleSelectAll() {
    setSelected(allSelected ? new Set() : new Set(allJids));
  }

  async function runBulk(path: string) {
    if (selected.size === 0) return;
    setBusy(true);
    setError(null);
    try {
      await api.post(path, { group_jids: Array.from(selected) });
      setSelected(new Set());
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Bulk action failed');
    } finally {
      setBusy(false);
    }
  }

  const consentedCount = (groups ?? []).filter((g) => g.consent_status === 'consented').length;

  return (
    <div>
      <h2>Groups</h2>
      <p className="muted">Groups the connected WhatsApp account belongs to. Nothing is exportable until you mark a group consented.</p>

      {groups && groups.length > 0 && (
        <div className="stat-grid" style={{ marginBottom: 20 }}>
          <div className="stat-tile">
            <div className="stat-label">Total groups</div>
            <div className="stat-value">{groups.length}</div>
          </div>
          <div className="stat-tile">
            <div className="stat-label">Consented</div>
            <div className="stat-value">{consentedCount}</div>
          </div>
          <div className="stat-tile">
            <div className="stat-label">Total members</div>
            <div className="stat-value">{groups.reduce((sum, g) => sum + g.member_count, 0).toLocaleString()}</div>
          </div>
        </div>
      )}

      <div className="card">
        {!groups ? (
          <p className="muted">Loading...</p>
        ) : groups.length === 0 ? (
          <p className="muted">No groups synced yet. Connect WhatsApp first, then this list fills in automatically.</p>
        ) : (
          <>
            <div className="row" style={{ justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
              <div className="muted">{selected.size} of {groups.length} selected</div>
              <div className="row" style={{ flexWrap: 'wrap' }}>
                <button disabled={busy || selected.size === 0} onClick={() => runBulk('/api/v1/groups/bulk-mark-consented')}>
                  {busy ? 'Working...' : `Mark ${selected.size || ''} consented`}
                </button>
                <button
                  className="danger"
                  disabled={busy || selected.size === 0}
                  onClick={() => runBulk('/api/v1/groups/bulk-revoke-consent')}
                >
                  Revoke selected
                </button>
              </div>
            </div>
            {error && <div className="error" style={{ marginTop: 8 }}>{error}</div>}

            <div className="table-scroll">
              <table style={{ marginTop: 14 }}>
                <thead>
                  <tr>
                    <th><input type="checkbox" checked={allSelected} onChange={toggleSelectAll} /></th>
                    <th>Group</th>
                    <th>Members</th>
                    <th>Consent</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {groups.map((g) => (
                    <tr key={g.group_jid}>
                      <td><input type="checkbox" checked={selected.has(g.group_jid)} onChange={() => toggleSelected(g.group_jid)} /></td>
                      <td>{g.group_name ?? g.group_jid}</td>
                      <td>{g.member_count}</td>
                      <td><ConsentStatusBadge status={g.consent_status} /></td>
                      <td><Link href={`/groups/${encodeURIComponent(g.group_jid)}`}>Open →</Link></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
