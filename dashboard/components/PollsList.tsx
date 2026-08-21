import Link from 'next/link';

type Poll = {
  poll_message_id: string;
  poll_title: string;
  poll_created_at: string;
};

export function PollsList({ groupJid, polls }: { groupJid: string; polls: Poll[] }) {
  if (polls.length === 0) return <p className="muted">No polls seen in this group yet.</p>;

  return (
    <table>
      <thead><tr><th>Poll</th><th>Created</th><th></th></tr></thead>
      <tbody>
        {polls.map((p) => (
          <tr key={p.poll_message_id}>
            <td>{p.poll_title}</td>
            <td className="muted">{new Date(p.poll_created_at).toLocaleString()}</td>
            <td>
              <Link href={`/groups/${encodeURIComponent(groupJid)}/polls/${encodeURIComponent(p.poll_message_id)}`}>
                View voters →
              </Link>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
