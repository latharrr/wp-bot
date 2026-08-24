'use client';

import { useEffect, useState, type FormEvent } from 'react';
import { api } from '@/lib/apiClient';
import { ExportButton } from '@/components/ExportButton';
import { RequireFeature } from '@/components/RequireFeature';
import { KeywordWatchlist } from '@/components/KeywordWatchlist';

type SearchResult = {
  keyword: string;
  hidden_match_count: number;
  results: { group_name: string | null; sender_name: string | null; sender_phone: string | null; message: string; message_date: string }[];
};

type Tab = 'search' | 'watchlist';

export default function KeywordSearchPage() {
  return (
    <RequireFeature feature="keyword_search">
      <KeywordSearchPageContent />
    </RequireFeature>
  );
}

function KeywordSearchPageContent() {
  const [tab, setTab] = useState<Tab>('search');
  const [query, setQuery] = useState('');
  const [result, setResult] = useState<SearchResult | null>(null);
  const [recent, setRecent] = useState<{ keyword: string }[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.get<{ keyword: string }[]>('/api/v1/keywords/recent').then(setRecent);
  }, []);

  async function search(term: string) {
    setLoading(true);
    try {
      const res = await api.get<SearchResult>(`/api/v1/keywords/search?q=${encodeURIComponent(term)}`);
      setResult(res);
    } finally {
      setLoading(false);
    }
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (query.trim()) search(query.trim());
  }

  return (
    <div>
      <h2>Keyword search</h2>
      <p className="muted">Finds every message containing this term across your consented groups, with sender name/phone.</p>

      <div className="tabs">
        <a className={tab === 'search' ? 'active' : ''} onClick={() => setTab('search')}>Search</a>
        <a className={tab === 'watchlist' ? 'active' : ''} onClick={() => setTab('watchlist')}>Watched keywords</a>
      </div>

      {tab === 'watchlist' && <KeywordWatchlist />}

      {tab === 'search' && (
        <>
          <form className="card row" onSubmit={onSubmit}>
            <input placeholder="e.g. pg" value={query} onChange={(e) => setQuery(e.target.value)} style={{ flex: 1 }} />
            <button type="submit" disabled={loading || !query.trim()}>{loading ? 'Searching...' : 'Search'}</button>
          </form>

          {recent.length > 0 && !result && (
            <div className="row" style={{ flexWrap: 'wrap', marginBottom: 16 }}>
              {recent.map((r) => (
                <button key={r.keyword} className="secondary" onClick={() => { setQuery(r.keyword); search(r.keyword); }}>
                  {r.keyword}
                </button>
              ))}
            </div>
          )}

          {result && (
            <div className="card">
              <div className="row" style={{ justifyContent: 'space-between' }}>
                <div>
                  <strong>{result.results.length}</strong> exportable match(es) for "{result.keyword}"
                  {result.hidden_match_count > 0 && (
                    <div className="muted">
                      +{result.hidden_match_count} more match(es) exist in groups that aren't marked consented yet
                    </div>
                  )}
                </div>
                <ExportButton
                  path={`/api/v1/keywords/search/export?q=${encodeURIComponent(result.keyword)}`}
                  filename={`keyword_${result.keyword}.xlsx`}
                  locked={result.results.length === 0}
                  lockedReason={result.results.length === 0 ? 'No consented matches to export yet' : undefined}
                />
              </div>

              <div className="table-scroll">
                <table style={{ marginTop: 14 }}>
                  <thead><tr><th>Group</th><th>Sender</th><th>Phone</th><th>Message</th><th>Date</th></tr></thead>
                  <tbody>
                    {result.results.map((r, i) => (
                      <tr key={i}>
                        <td>{r.group_name}</td>
                        <td>{r.sender_name ?? '—'}</td>
                        <td>{r.sender_phone}</td>
                        <td>{r.message}</td>
                        <td className="muted">{new Date(r.message_date).toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
