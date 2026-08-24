'use client';

import { useEffect, useState } from 'react';
import { api, ApiError } from '@/lib/apiClient';
import { useCurrentUser } from '@/lib/useCurrentUser';

type WatchedKeyword = { id: string; keyword: string; is_active: boolean; search_count: number };

/** The managed, continuously-matched keyword list -- every incoming message is checked against
 * every active entry here, independent of whether anyone has ever run an ad-hoc search for it.
 * Ported from poison-br09/whatsapp-propensity-scoring's Keywords admin page. */
export function KeywordWatchlist() {
  const { user } = useCurrentUser();
  const isSuperAdmin = user?.role === 'super_admin';

  const [keywords, setKeywords] = useState<WatchedKeyword[] | null>(null);
  const [newKeywords, setNewKeywords] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    try {
      setKeywords(await api.get<WatchedKeyword[]>('/api/v1/keywords/watchlist'));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to load watched keywords');
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function addKeywords() {
    const list = newKeywords
      .split(',')
      .map((k) => k.trim())
      .filter(Boolean);
    if (list.length === 0) return;
    setBusy(true);
    setError(null);
    try {
      await api.post('/api/v1/keywords/watchlist', { keywords: list });
      setNewKeywords('');
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to add keywords');
    } finally {
      setBusy(false);
    }
  }

  async function toggleEnabled(keyword: string, enabled: boolean) {
    setBusy(true);
    setError(null);
    try {
      await api.patch('/api/v1/keywords/watchlist', { keywords: [keyword], enabled });
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to update keyword');
    } finally {
      setBusy(false);
    }
  }

  async function remove(keyword: string) {
    setBusy(true);
    setError(null);
    try {
      await api.delete('/api/v1/keywords/watchlist', { keywords: [keyword] });
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to delete keyword');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="card">
      <h3 style={{ marginTop: 0 }}>Watched keywords</h3>
      <p className="muted" style={{ marginTop: -4 }}>
        Every incoming message is continuously checked against active keywords below — you don't need to search for a
        term first for it to be tracked.
      </p>

      <div className="row" style={{ marginTop: 12 }}>
        <input
          placeholder="flat, rent, pg"
          value={newKeywords}
          onChange={(e) => setNewKeywords(e.target.value)}
          style={{ flex: 1 }}
        />
        <button onClick={addKeywords} disabled={busy || !newKeywords.trim()}>
          Add
        </button>
      </div>
      {error && <div className="error" style={{ marginTop: 10 }}>{error}</div>}

      {keywords && keywords.length > 0 && (
        <div className="table-scroll">
          <table style={{ marginTop: 16 }}>
            <thead>
              <tr>
                <th>Keyword</th>
                <th>Status</th>
                <th>Times searched</th>
                {isSuperAdmin && <th></th>}
              </tr>
            </thead>
            <tbody>
              {keywords.map((k) => (
                <tr key={k.id}>
                  <td>{k.keyword}</td>
                  <td>
                    <span className={`badge ${k.is_active ? 'connected' : 'none'}`}>
                      {k.is_active ? 'Active' : 'Disabled'}
                    </span>
                  </td>
                  <td className="muted">{k.search_count}</td>
                  {isSuperAdmin && (
                    <td>
                      <div className="row">
                        <button className="secondary" disabled={busy} onClick={() => toggleEnabled(k.keyword, !k.is_active)}>
                          {k.is_active ? 'Disable' : 'Enable'}
                        </button>
                        <button className="danger" disabled={busy} onClick={() => remove(k.keyword)}>
                          Delete
                        </button>
                      </div>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {keywords && keywords.length === 0 && <p className="muted" style={{ marginTop: 14 }}>No keywords watched yet.</p>}
    </div>
  );
}
