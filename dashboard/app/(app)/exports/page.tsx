'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/apiClient';

type ExportLogEntry = {
  actor: string;
  export_type: string;
  group_jid: string | null;
  keyword: string | null;
  row_count: number;
  filename: string;
  created_at: string;
};

export default function ExportsPage() {
  const [entries, setEntries] = useState<ExportLogEntry[] | null>(null);

  useEffect(() => {
    api.get<ExportLogEntry[]>('/api/v1/export-log').then(setEntries);
  }, []);

  return (
    <div>
      <h2>Export log</h2>
      <p className="muted">Every export (contacts, poll, keyword search) is recorded here, regardless of who ran it.</p>
      <div className="card">
        {!entries ? (
          <p className="muted">Loading...</p>
        ) : entries.length === 0 ? (
          <p className="muted">No exports yet.</p>
        ) : (
          <table>
            <thead><tr><th>When</th><th>Actor</th><th>Type</th><th>Rows</th><th>File</th></tr></thead>
            <tbody>
              {entries.map((e, i) => (
                <tr key={i}>
                  <td className="muted">{new Date(e.created_at).toLocaleString()}</td>
                  <td>{e.actor}</td>
                  <td>{e.export_type}{e.keyword ? ` (${e.keyword})` : ''}</td>
                  <td>{e.row_count}</td>
                  <td>{e.filename}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
