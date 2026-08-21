'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getToken } from '@/lib/auth';

/** Redirects to /login if there's no stored token. Returns true once the check has passed,
 * so callers can avoid rendering (and firing authenticated fetches) before that. */
export function useRequireAuth(): boolean {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!getToken()) {
      router.replace('/login');
      return;
    }
    setReady(true);
  }, [router]);

  return ready;
}
