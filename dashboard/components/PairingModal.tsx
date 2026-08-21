'use client';

import { useState } from 'react';
import { api, ApiError } from '@/lib/apiClient';

export function PairingModal({ onPaired }: { onPaired: () => void }) {
  const [phone, setPhone] = useState('');
  const [code, setCode] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function requestCode() {
    setLoading(true);
    setError(null);
    setCode(null);
    try {
      const res = await api.post<{ pairing_code: string }>('/api/v1/session/pairing-code', { phone_number: phone });
      setCode(res.pairing_code);
      onPaired();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to get pairing code');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card" style={{ maxWidth: 420 }}>
      <h3 style={{ marginTop: 0 }}>Connect WhatsApp</h3>
      <p className="muted">
        Enter the business phone number in international format (e.g. 919876543210), then open WhatsApp
        on that phone: Settings → Linked Devices → Link with phone number instead, and enter the code below.
      </p>
      <div className="row" style={{ marginTop: 12 }}>
        <input placeholder="919876543210" value={phone} onChange={(e) => setPhone(e.target.value)} />
        <button onClick={requestCode} disabled={loading || !phone}>
          {loading ? 'Requesting...' : 'Get pairing code'}
        </button>
      </div>
      {code && (
        <div className="card" style={{ marginTop: 14, textAlign: 'center', background: '#1e222b' }}>
          <div className="muted">Pairing code</div>
          <div style={{ fontSize: 28, fontWeight: 700, letterSpacing: 4 }}>{code}</div>
        </div>
      )}
      {error && <div className="error">{error}</div>}
    </div>
  );
}
