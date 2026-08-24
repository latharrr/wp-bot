import { ExportButton } from '@/components/ExportButton';

type ContactsResponse = {
  member_count: number;
  exportable: boolean;
  members: { display_name: string | null; phone: string | null }[];
};

export function ContactsTable({ groupJid, contacts }: { groupJid: string; contacts: ContactsResponse }) {
  return (
    <div className="card">
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <div className="muted">{contacts.member_count} member(s) in this group</div>
        <ExportButton
          path={`/api/v1/groups/${encodeURIComponent(groupJid)}/contacts/export`}
          filename="contacts.xlsx"
          label="Export contacts"
          locked={!contacts.exportable}
          lockedReason={!contacts.exportable ? 'Mark this group consented (and get members opted in) to unlock export' : undefined}
        />
      </div>

      {!contacts.exportable && (
        <div className="locked-banner" style={{ marginTop: 14 }}>
          This group isn't marked consented yet, so member names/numbers aren't shown here. Only aggregate counts are visible.
        </div>
      )}

      {contacts.exportable && (
        <div className="table-scroll">
          <table style={{ marginTop: 14 }}>
            <thead><tr><th>Name</th><th>Phone</th></tr></thead>
            <tbody>
              {contacts.members.map((m) => (
                <tr key={m.phone}><td>{m.display_name ?? '—'}</td><td>{m.phone}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
