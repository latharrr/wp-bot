'use client';

import { useMemo, useState } from 'react';
import { ExportButton } from '@/components/ExportButton';

type Voter = { voter_name: string | null; voter_phone: string | null; selected_options: string[]; last_vote_timestamp: string };

type PollDetail = {
  poll_title: string;
  poll_options: string[];
  exportable: boolean;
  voters?: Voter[];
  aggregate_counts?: Record<string, number>;
};

export function PollVoterTable({ groupJid, pollMessageId, poll }: { groupJid: string; pollMessageId: string; poll: PollDetail }) {
  const [filter, setFilter] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const filteredVoters = useMemo(() => {
    if (!poll.voters) return [];
    if (!filter) return poll.voters;
    return poll.voters.filter((v) => v.selected_options.includes(filter));
  }, [poll.voters, filter]);

  async function copyPhones() {
    const phones = filteredVoters.map((v) => v.voter_phone).filter(Boolean).join('\n');
    await navigator.clipboard.writeText(phones);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  const exportPath = `/api/v1/groups/${encodeURIComponent(groupJid)}/polls/${encodeURIComponent(pollMessageId)}/export${
    filter ? `?option=${encodeURIComponent(filter)}` : ''
  }`;

  return (
    <div className="card">
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <h3 style={{ margin: 0 }}>{poll.poll_title}</h3>
        <ExportButton path={exportPath} filename={filter ? `poll_${filter}.xlsx` : 'poll.xlsx'} label={filter ? `Export "${filter}"` : 'Export'} />
      </div>

      {!poll.exportable && (
        <div className="locked-banner" style={{ marginTop: 14 }}>
          This group isn't marked consented, so individual voters aren't shown here — only aggregate counts.
        </div>
      )}

      {poll.exportable && poll.voters ? (
        <>
          <div className="row" style={{ marginTop: 14, flexWrap: 'wrap' }}>
            <button className={filter === null ? '' : 'secondary'} onClick={() => setFilter(null)}>
              All ({poll.voters.length})
            </button>
            {poll.poll_options.map((option) => {
              const count = poll.voters!.filter((v) => v.selected_options.includes(option)).length;
              return (
                <button key={option} className={filter === option ? '' : 'secondary'} onClick={() => setFilter(option)}>
                  {option} ({count})
                </button>
              );
            })}
          </div>

          <div className="row" style={{ marginTop: 10, justifyContent: 'space-between' }}>
            <div className="muted">
              {filter ? `${filteredVoters.length} voter(s) picked "${filter}"` : `${filteredVoters.length} voter(s) total`}
            </div>
            <button className="secondary" onClick={copyPhones} disabled={filteredVoters.length === 0}>
              {copied ? 'Copied!' : 'Copy phone numbers'}
            </button>
          </div>

          <table style={{ marginTop: 14 }}>
            <thead><tr><th>Voter</th><th>Phone</th><th>Selected</th><th>Voted at</th></tr></thead>
            <tbody>
              {filteredVoters.map((v) => (
                <tr key={v.voter_phone}>
                  <td>{v.voter_name ?? '—'}</td>
                  <td>{v.voter_phone}</td>
                  <td>{v.selected_options.join(', ')}</td>
                  <td className="muted">{new Date(v.last_vote_timestamp).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      ) : (
        <table style={{ marginTop: 14 }}>
          <thead><tr><th>Option</th><th>Votes</th></tr></thead>
          <tbody>
            {Object.entries(poll.aggregate_counts ?? {}).map(([option, count]) => (
              <tr key={option}><td>{option}</td><td>{count}</td></tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
