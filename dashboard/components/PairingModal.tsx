'use client';

import { useEffect, useRef, useState } from 'react';
import { api, ApiError } from '@/lib/apiClient';

const QR_POLL_INTERVAL_MS = 3000;

export function PairingModal({ onPaired }: { onPaired: () => void }) {
  const [qrDataUrl, setQrDataUrl] = useState<string | null>(null);
  const [qrError, setQrError] = useState<string | null>(null);
  const [qrLoading, setQrLoading] = useState(false);
  const generatedAtRef = useRef(0);

  const [showPhoneFallback, setShowPhoneFallback] = useState(false);
  const [phone, setPhone] = useState('');
  const [code, setCode] = useState<string | null>(null);
  const [phoneLoading, setPhoneLoading] = useState(false);
  const [phoneError, setPhoneError] = useState<string | null>(null);

  async function startQr() {
    setQrLoading(true);
    setQrError(null);
    try {
      const res = await api.post<{ qr_data_url: string; generated_at: number }>('/api/v1/session/qr-login');
      setQrDataUrl(res.qr_data_url);
      generatedAtRef.current = res.generated_at;
    } catch (err) {
      setQrError(err instanceof ApiError ? err.message : 'Failed to get a QR code');
    } finally {
      setQrLoading(false);
    }
  }

  useEffect(() => {
    startQr();
    // The QR rotates roughly every 20s while unscanned -- keep polling for a newer one so a
    // stale, already-expired code doesn't sit on screen.
    const interval = setInterval(async () => {
      try {
        const res = await api.get<{ qr_data_url: string; generated_at: number }>('/api/v1/session/qr-code');
        if (res.generated_at !== generatedAtRef.current) {
          generatedAtRef.current = res.generated_at;
          setQrDataUrl(res.qr_data_url);
        }
      } catch {
        // no QR yet, or the bridge is between connections -- next poll will pick it up
      }
    }, QR_POLL_INTERVAL_MS);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function requestCode() {
    setPhoneLoading(true);
    setPhoneError(null);
    setCode(null);
    try {
      const res = await api.post<{ pairing_code: string }>('/api/v1/session/pairing-code', { phone_number: phone });
      setCode(res.pairing_code);
      onPaired();
    } catch (err) {
      setPhoneError(err instanceof ApiError ? err.message : 'Failed to get pairing code');
    } finally {
      setPhoneLoading(false);
    }
  }

  return (
    <div className="card" style={{ maxWidth: 420 }}>
      <h3 style={{ marginTop: 0 }}>Connect WhatsApp</h3>
      <p className="muted">
        Open WhatsApp on the business phone: Settings → Linked Devices → Link a Device, then scan this code.
      </p>

      <div className="card" style={{ marginTop: 12, textAlign: 'center', background: '#1e222b' }}>
        {qrDataUrl ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={qrDataUrl} alt="WhatsApp linking QR code" width={240} height={240} style={{ borderRadius: 8 }} />
        ) : (
          <div className="muted" style={{ padding: 40 }}>{qrLoading ? 'Generating QR code...' : 'No QR code yet'}</div>
        )}
      </div>
      {qrError && <div className="error">{qrError}</div>}
      <button className="secondary" style={{ marginTop: 10 }} onClick={startQr} disabled={qrLoading}>
        {qrLoading ? 'Refreshing...' : 'Get a new QR code'}
      </button>

      <div style={{ marginTop: 18 }}>
        <a onClick={() => setShowPhoneFallback((v) => !v)} style={{ cursor: 'pointer' }}>
          {showPhoneFallback ? 'Hide' : 'Pair with a phone number instead'}
        </a>
      </div>

      {showPhoneFallback && (
        <div style={{ marginTop: 10 }}>
          <p className="muted">
            Note: phone-number pairing codes have been unreliable against WhatsApp's current servers in testing --
            prefer the QR code above if you can.
          </p>
          <div className="row">
            <input placeholder="919876543210" value={phone} onChange={(e) => setPhone(e.target.value)} />
            <button onClick={requestCode} disabled={phoneLoading || !phone}>
              {phoneLoading ? 'Requesting...' : 'Get pairing code'}
            </button>
          </div>
          {code && (
            <div className="card" style={{ marginTop: 14, textAlign: 'center', background: '#1e222b' }}>
              <div className="muted">Pairing code</div>
              <div style={{ fontSize: 28, fontWeight: 700, letterSpacing: 4 }}>{code}</div>
            </div>
          )}
          {phoneError && <div className="error">{phoneError}</div>}
        </div>
      )}
    </div>
  );
}
