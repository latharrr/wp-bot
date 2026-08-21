'use client';

import { use, useEffect, useState } from 'react';
import { api } from '@/lib/apiClient';
import { ConsentActionsPanel } from '@/components/ConsentActionsPanel';
import { ContactsTable } from '@/components/ContactsTable';
import { PollsList } from '@/components/PollsList';

type Group = { group_jid: string; group_name: string | null; consent_status: string };
type Tab = 'overview' | 'contacts' | 'polls';

export default function GroupDetailPage({ params }: { params: Promise<{ groupJid: string }> }) {
  const { groupJid: encodedGroupJid } = use(params);
  const groupJid = decodeURIComponent(encodedGroupJid);

  const [tab, setTab] = useState<Tab>('overview');
  const [group, setGroup] = useState<Group | null>(null);
  const [memberConsent, setMemberConsent] = useState<any[]>([]);
  const [contacts, setContacts] = useState<any>(null);
  const [polls, setPolls] = useState<any[] | null>(null);

  async function loadOverview() {
    const [g, mc] = await Promise.all([
      api.get<Group>(`/api/v1/groups/${encodeURIComponent(groupJid)}`),
      api.get<any[]>(`/api/v1/groups/${encodeURIComponent(groupJid)}/consent/members`),
    ]);
    setGroup(g);
    setMemberConsent(mc);
  }

  useEffect(() => {
    loadOverview();
  }, [groupJid]);

  useEffect(() => {
    if (tab === 'contacts') api.get<any>(`/api/v1/groups/${encodeURIComponent(groupJid)}/contacts`).then(setContacts);
    if (tab === 'polls') api.get<any[]>(`/api/v1/groups/${encodeURIComponent(groupJid)}/polls`).then(setPolls);
  }, [tab, groupJid]);

  if (!group) return <p className="muted">Loading...</p>;

  return (
    <div>
      <h2>{group.group_name ?? group.group_jid}</h2>
      <div className="tabs">
        <a className={tab === 'overview' ? 'active' : ''} onClick={() => setTab('overview')}>Overview</a>
        <a className={tab === 'contacts' ? 'active' : ''} onClick={() => setTab('contacts')}>Contacts</a>
        <a className={tab === 'polls' ? 'active' : ''} onClick={() => setTab('polls')}>Polls</a>
      </div>

      {tab === 'overview' && (
        <ConsentActionsPanel
          groupJid={groupJid}
          consentStatus={group.consent_status}
          memberConsent={memberConsent}
          onChanged={loadOverview}
        />
      )}

      {tab === 'contacts' && (contacts ? <ContactsTable groupJid={groupJid} contacts={contacts} /> : <p className="muted">Loading...</p>)}

      {tab === 'polls' && (
        <div className="card">
          {polls ? <PollsList groupJid={groupJid} polls={polls} /> : <p className="muted">Loading...</p>}
        </div>
      )}
    </div>
  );
}
