import { ExportButton } from '@/components/ExportButton';

type PollDetail = {
  poll_title: string;
  poll_options: string[];
  exportable: boolean;
  voters?: { voter_name: string | null; voter_phone: string | null; selected_options: string[]; last_vote_timestamp: string }[];
  aggregate_counts?: Record<string, number>;
};

export function PollVoterTable({ groupJid, pollMessageId, poll }: { groupJid: string; pollMessageId: string; poll: PollDetail }) {
  return (
    <div className="card">
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <h3 style={{ margin: 0 }}>{poll.poll_title}</h3>
        <ExportButton
          path={`/api/v1/groups/${encodeURIComponent(groupJid)}/polls/${encodeURIComponent(pollMessageId)}/export`}
          filename="poll.xlsx"
          label="Export"
        />
      </div>

      {!poll.exportable && (
        <div className="locked-banner" style={{ marginTop: 14 }}>
          This group isn't marked consented, so individual voters aren't shown here — only aggregate counts.
        </div>
      )}

      {poll.exportable && poll.voters ? (
        <table style={{ marginTop: 14 }}>
          <thead><tr><th>Voter</th><th>Phone</th><th>Selected</th><th>Voted at</th></tr></thead>
          <tbody>
            {poll.voters.map((v) => (
              <tr key={v.voter_phone}>
                <td>{v.voter_name ?? '—'}</td>
                <td>{v.voter_phone}</td>
                <td>{v.selected_options.join(', ')}</td>
                <td className="muted">{new Date(v.last_vote_timestamp).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
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
