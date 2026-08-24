'use client';

import { useEffect, useState } from 'react';
import { api, ApiError } from '@/lib/apiClient';
import { useCurrentUser } from '@/lib/useCurrentUser';
import { FeatureTogglesPanel } from '@/components/FeatureTogglesPanel';

type User = { username: string; role: 'super_admin' | 'user'; allowed_features: string[]; created_at: string };

const FEATURE_LABELS: Record<string, string> = {
  connection: 'Connection',
  groups: 'Groups',
  keyword_search: 'Keyword Search',
  csv_scoring: 'CSV Scoring',
  export_log: 'Export Log',
};

export default function AdminPage() {
  const { user, loading: userLoading } = useCurrentUser();

  if (userLoading) return <p className="muted">Loading...</p>;
  if (user?.role !== 'super_admin') {
    return (
      <div className="card">
        <p>Only the super admin can manage users.</p>
      </div>
    );
  }
  return <AdminPageContent />;
}

function AdminPageContent() {
  const [users, setUsers] = useState<User[] | null>(null);
  const [features, setFeatures] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const [newUsername, setNewUsername] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newFeatures, setNewFeatures] = useState<Set<string>>(new Set());

  function refresh() {
    return Promise.all([
      api.get<User[]>('/api/v1/admin/users'),
      api.get<string[]>('/api/v1/admin/users/features'),
    ]).then(([u, f]) => {
      setUsers(u);
      setFeatures(f);
    });
  }

  useEffect(() => {
    refresh();
  }, []);

  function toggleNewFeature(feature: string) {
    setNewFeatures((prev) => {
      const next = new Set(prev);
      if (next.has(feature)) next.delete(feature);
      else next.add(feature);
      return next;
    });
  }

  async function createUser() {
    if (!newUsername.trim() || !newPassword.trim()) return;
    setBusy(true);
    setError(null);
    try {
      await api.post('/api/v1/admin/users', {
        username: newUsername.trim(),
        password: newPassword,
        allowed_features: Array.from(newFeatures),
      });
      setNewUsername('');
      setNewPassword('');
      setNewFeatures(new Set());
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to create user');
    } finally {
      setBusy(false);
    }
  }

  async function toggleUserFeature(targetUser: User, feature: string) {
    const next = new Set(targetUser.allowed_features);
    if (next.has(feature)) next.delete(feature);
    else next.add(feature);
    setBusy(true);
    setError(null);
    try {
      await api.patch(`/api/v1/admin/users/${encodeURIComponent(targetUser.username)}/features`, {
        allowed_features: Array.from(next),
      });
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to update features');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <h2>Admin</h2>
      <p className="muted">Create new dashboard users and choose which features each one can see.</p>

      <FeatureTogglesPanel />

      <div className="card">
        <h3 style={{ marginTop: 0 }}>Create user</h3>
        <div className="row" style={{ flexWrap: 'wrap' }}>
          <input placeholder="Username" value={newUsername} onChange={(e) => setNewUsername(e.target.value)} />
          <input
            placeholder="Password"
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
          />
        </div>
        <div className="row" style={{ flexWrap: 'wrap', marginTop: 10 }}>
          {features.map((feature) => (
            <label key={feature} className="row" style={{ gap: 6 }}>
              <input type="checkbox" checked={newFeatures.has(feature)} onChange={() => toggleNewFeature(feature)} />
              {FEATURE_LABELS[feature] ?? feature}
            </label>
          ))}
        </div>
        <button
          style={{ marginTop: 12 }}
          disabled={busy || !newUsername.trim() || !newPassword.trim()}
          onClick={createUser}
        >
          {busy ? 'Working...' : 'Create user'}
        </button>
        {error && <div className="error" style={{ marginTop: 8 }}>{error}</div>}
      </div>

      <div className="card" style={{ marginTop: 16 }}>
        <h3 style={{ marginTop: 0 }}>Users</h3>
        {!users ? (
          <p className="muted">Loading...</p>
        ) : (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Username</th>
                  <th>Role</th>
                  <th>Features</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.username}>
                    <td>{u.username}</td>
                    <td className="muted">{u.role}</td>
                    <td>
                      {u.role === 'super_admin' ? (
                        <span className="muted">All (super admin)</span>
                      ) : (
                        <div className="row" style={{ flexWrap: 'wrap' }}>
                          {features.map((feature) => (
                            <label key={feature} className="row" style={{ gap: 4 }}>
                              <input
                                type="checkbox"
                                checked={u.allowed_features.includes(feature)}
                                disabled={busy}
                                onChange={() => toggleUserFeature(u, feature)}
                              />
                              {FEATURE_LABELS[feature] ?? feature}
                            </label>
                          ))}
                        </div>
                      )}
                    </td>
                    <td>
                      {u.role !== 'super_admin' && (
                        <DeleteUserButton username={u.username} busy={busy} setBusy={setBusy} setError={setError} onDeleted={refresh} />
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function DeleteUserButton({
  username,
  busy,
  setBusy,
  setError,
  onDeleted,
}: {
  username: string;
  busy: boolean;
  setBusy: (b: boolean) => void;
  setError: (e: string | null) => void;
  onDeleted: () => void;
}) {
  const [confirming, setConfirming] = useState(false);

  async function doDelete() {
    setBusy(true);
    setError(null);
    try {
      await api.delete(`/api/v1/admin/users/${encodeURIComponent(username)}`);
      onDeleted();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to delete user');
    } finally {
      setBusy(false);
      setConfirming(false);
    }
  }

  if (confirming) {
    return (
      <span className="row">
        <button className="danger" disabled={busy} onClick={doDelete}>Confirm delete</button>
        <button className="secondary" disabled={busy} onClick={() => setConfirming(false)}>Cancel</button>
      </span>
    );
  }
  return (
    <button className="danger" disabled={busy} onClick={() => setConfirming(true)}>
      Delete
    </button>
  );
}
