'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/apiClient';

type MessagesResponse = {
  exportable: boolean;
  total: number;
  page: number;
  page_size: number;
  messages: { sender_name: string | null; sender_phone: string | null; message_text: string; sent_at: string }[];
};

export function MessagesMonitor({ groupJid }: { groupJid: string }) {
  const [page, setPage] = useState(1);
  const [data, setData] = useState<MessagesResponse | null>(null);
  const pageSize = 50;

  useEffect(() => {
    setData(null);
    api
      .get<MessagesResponse>(`/api/v1/groups/${encodeURIComponent(groupJid)}/messages?page=${page}&page_size=${pageSize}`)
      .then(setData);
  }, [groupJid, page]);

  if (!data) return <div className="card"><p className="muted">Loading...</p></div>;

  const totalPages = Math.max(1, Math.ceil(data.total / data.page_size));

  return (
    <div className="card">
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <div className="muted">{data.total} message(s) recorded in this group</div>
      </div>

      {!data.exportable && (
        <div className="locked-banner" style={{ marginTop: 14 }}>
          This group isn't marked consented yet, so message content and senders aren't shown here. Only the
          total message count is visible. Mark the group consented on the Overview tab to unlock this monitor.
        </div>
      )}

      {data.exportable && (
        <>
          <div className="table-scroll">
            <table style={{ marginTop: 14 }}>
              <thead><tr><th>Sender</th><th>Phone</th><th>Message</th><th>Sent</th></tr></thead>
              <tbody>
                {data.messages.map((m, i) => (
                  <tr key={i}>
                    <td>{m.sender_name ?? '—'}</td>
                    <td>{m.sender_phone ?? '—'}</td>
                    <td>{m.message_text}</td>
                    <td className="muted">{new Date(m.sent_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {data.messages.length === 0 && <p className="muted" style={{ marginTop: 14 }}>No messages recorded yet.</p>}

          {totalPages > 1 && (
            <div className="row" style={{ justifyContent: 'center', marginTop: 14, gap: 12 }}>
              <button className="secondary" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
                ← Prev
              </button>
              <span className="muted">Page {page} of {totalPages}</span>
              <button className="secondary" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
                Next →
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
