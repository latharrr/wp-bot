export function ConnectionStatusBadge({ status }: { status: string }) {
  return <span className={`badge ${status}`}>{status.replace('_', ' ')}</span>;
}
