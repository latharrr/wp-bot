'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/apiClient';
import { PairingModal } from '@/components/PairingModal';
import { ConnectionStatusBadge } from '@/components/ConnectionStatusBadge';
import { RequireFeature } from '@/components/RequireFeature';

type SessionStatus = {
  status: string;
  phone_number: string | null;
  pairing_required: boolean;
  last_event_at: string | null;
  last_error: string | null;
};

export default function ConnectionPage() {
  return (
    <RequireFeature feature="connection">
      <ConnectionPageContent />
    </RequireFeature>
  );
}

function ConnectionPageContent() {
  const [session, setSession] = useState<SessionStatus | null>(null);

  async function refresh() {
    const status = await api.get<SessionStatus>('/api/v1/session/status');
    setSession(status);
  }

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 4000);
    return () => clearInterval(interval);
  }, []);

  if (!session) return <p className="muted">Loading...</p>;

  return (
    <div>
      <h2>Connection</h2>
      <div className="card">
        <div className="row">
          <ConnectionStatusBadge status={session.status} />
          {session.phone_number && <span className="muted">{session.phone_number}</span>}
        </div>
        {session.last_error && <div className="error" style={{ marginTop: 8 }}>{session.last_error}</div>}
        {session.last_event_at && (
          <div className="muted" style={{ marginTop: 8 }}>Last event: {new Date(session.last_event_at).toLocaleString()}</div>
        )}
      </div>

      {session.pairing_required && <PairingModal onPaired={refresh} />}
    </div>
  );
}
