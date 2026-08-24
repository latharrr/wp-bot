'use client';

import { useEffect, useState } from 'react';

/**
 * A small dismissible explainer bubble for first-time users. Hidden by default (both on the
 * server and on the very first client paint) so there's no hydration flash, then reveals itself
 * on mount if this id hasn't been dismissed before. Dismissal is per-browser (localStorage), not
 * per-account, so it's a "seen this before" hint rather than an onboarding gate.
 */
export function OnboardingTip({ id, children }: { id: string; children: React.ReactNode }) {
  const storageKey = `wp-bot-tip-dismissed:${id}`;
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    try {
      if (localStorage.getItem(storageKey) !== '1') setVisible(true);
    } catch {
      setVisible(true);
    }
  }, [storageKey]);

  if (!visible) return null;

  function dismiss() {
    try {
      localStorage.setItem(storageKey, '1');
    } catch {
      // ignore -- worst case the tip reappears next visit
    }
    setVisible(false);
  }

  return (
    <div className="onboarding-tip">
      <span>{children}</span>
      <button className="secondary" onClick={dismiss}>Got it</button>
    </div>
  );
}
