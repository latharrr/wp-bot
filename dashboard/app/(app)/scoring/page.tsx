'use client';

import { useState, type ChangeEvent } from 'react';
import { getToken } from '@/lib/auth';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://127.0.0.1:8000';

export default function ScoringPage() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<{ aboveThreshold: number; rowCount: number } | null>(null);

  function onFileChange(e: ChangeEvent<HTMLInputElement>) {
    setFile(e.target.files?.[0] ?? null);
    setSummary(null);
    setError(null);
  }

  async function onScore() {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const form = new FormData();
      form.append('file', file);
      const response = await fetch(`${API_BASE_URL}/api/v1/polls/score`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${getToken()}` },
        body: form,
      });
      if (!response.ok) {
        const detail = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(detail.detail ?? response.statusText);
      }
      const aboveThreshold = Number(response.headers.get('X-Above-Threshold-Count') ?? 0);
      const rowCount = Number(response.headers.get('X-Row-Count') ?? 0);
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'scored.csv';
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      setSummary({ aboveThreshold, rowCount });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Scoring failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h2>CSV propensity scoring</h2>
      <p className="muted">
        Upload a poll CSV (columns: mobile, product_name, poll_date, vote) to score each voter's purchase propensity
        against Supabase history.
      </p>
      <div className="card">
        <div className="row">
          <input type="file" accept=".csv" onChange={onFileChange} />
          <button onClick={onScore} disabled={!file || loading}>{loading ? 'Scoring...' : 'Score & download'}</button>
        </div>
        {error && <div className="error">{error}</div>}
        {summary && (
          <div className="muted" style={{ marginTop: 12 }}>
            Scored {summary.rowCount} row(s) — {summary.aboveThreshold} above threshold.
          </div>
        )}
      </div>
    </div>
  );
}
