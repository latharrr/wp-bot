'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/apiClient';
import { RequireFeature } from '@/components/RequireFeature';

type Poll = {
  poll_message_id: string;
  poll_title: string;
  poll_options: string[];
  group_jid: string;
  group_name: string | null;
  poll_created_at: string;
};

type PollsResponse = { total: number; page: number; page_size: number; polls: Poll[] };

const PAGE_SIZE = 25;

export default function AllPollsPage() {
  return (
    <RequireFeature feature="groups">
      <AllPollsPageContent />
    </RequireFeature>
  );
}

function AllPollsPageContent() {
  const [data, setData] = useState<PollsResponse | null>(null);
  const [page, setPage] = useState(1);
  const [groupFilter, setGroupFilter] = useState('');

  useEffect(() => {
    const params = new URLSearchParams({ page: String(page), page_size: String(PAGE_SIZE) });
    if (groupFilter.trim()) params.set('group_jid', groupFilter.trim());
    api.get<PollsResponse>(`/api/v1/polls?${params.toString()}`).then(setData).catch(() => setData({ total: 0, page, page_size: PAGE_SIZE, polls: [] }));
  }, [page, groupFilter]);

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;

  return (
    <div>
      <h2>All polls</h2>
      <p className="muted">Every poll seen across every group the connected WhatsApp account belongs to.</p>

      <div className="card row" style={{ justifyContent: 'space-between', flexWrap: 'wrap' }}>
        <input
          placeholder="Filter by group JID..."
          value={groupFilter}
          onChange={(e) => {
            setGroupFilter(e.target.value);
            setPage(1);
          }}
          style={{ minWidth: 260 }}
        />
        {data && <div className="muted">{data.total} poll(s) total</div>}
      </div>

      <div className="card">
        {!data ? (
          <p className="muted">Loading...</p>
        ) : data.polls.length === 0 ? (
          <p className="muted">No polls found.</p>
        ) : (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Poll</th>
                  <th>Group</th>
                  <th>Options</th>
                  <th>Created</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {data.polls.map((p) => (
                  <tr key={p.poll_message_id}>
                    <td>{p.poll_title}</td>
                    <td>{p.group_name ?? p.group_jid}</td>
                    <td className="muted">{p.poll_options.length}</td>
                    <td className="muted">{new Date(p.poll_created_at).toLocaleString()}</td>
                    <td>
                      <Link href={`/groups/${encodeURIComponent(p.group_jid)}/polls/${encodeURIComponent(p.poll_message_id)}`}>
                        View →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {data && totalPages > 1 && (
          <div className="pagination">
            <button className="secondary" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
              ← Previous
            </button>
            <span className="muted">Page {page} of {totalPages}</span>
            <button className="secondary" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
              Next →
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
