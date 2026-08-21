'use client';

import { useState, type FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { api, ApiError } from '@/lib/apiClient';
import { setToken } from '@/lib/auth';

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const { access_token } = await api.post<{ access_token: string }>('/api/v1/auth/login', { username, password });
      setToken(access_token);
      router.push('/');
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh', alignItems: 'center', justifyContent: 'center' }}>
      <form onSubmit={onSubmit} className="card" style={{ width: 320 }}>
        <h2>wp-bot</h2>
        <p className="muted" style={{ marginTop: -8 }}>Operator sign-in</p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 16 }}>
          <input placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} autoFocus />
          <input placeholder="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          <button type="submit" disabled={loading}>{loading ? 'Signing in...' : 'Sign in'}</button>
          {error && <div className="error">{error}</div>}
        </div>
      </form>
    </div>
  );
}
