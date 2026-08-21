export function ConsentStatusBadge({ status }: { status: string }) {
  const label = status === 'consented' ? 'Consented' : status === 'revoked' ? 'Revoked' : 'Not consented';
  return <span className={`badge ${status}`}>{label}</span>;
}
