'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/apiClient';
import { ConsentStatusBadge } from '@/components/ConsentStatusBadge';

type Group = {
  group_jid: string;
  group_name: string | null;
  member_count: number;
  consent_status: string;
  last_synced_at: string | null;
};

export default function GroupsPage() {
  const [groups, setGroups] = useState<Group[] | null>(null);

  useEffect(() => {
    api.get<Group[]>('/api/v1/groups').then(setGroups);
  }, []);

  return (
    <div>
      <h2>Groups</h2>
      <p className="muted">Groups the connected WhatsApp account belongs to. Nothing is exportable until you mark a group consented.</p>
      <div className="card">
        {!groups ? (
          <p className="muted">Loading...</p>
        ) : groups.length === 0 ? (
          <p className="muted">No groups synced yet. Connect WhatsApp first, then this list fills in automatically.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Group</th>
                <th>Members</th>
                <th>Consent</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {groups.map((g) => (
                <tr key={g.group_jid}>
                  <td>{g.group_name ?? g.group_jid}</td>
                  <td>{g.member_count}</td>
                  <td><ConsentStatusBadge status={g.consent_status} /></td>
                  <td><Link href={`/groups/${encodeURIComponent(g.group_jid)}`}>Open →</Link></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
