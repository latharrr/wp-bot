'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/apiClient';

export type CurrentUser = {
  username: string;
  role: 'super_admin' | 'user';
  allowed_features: string[];
};

/** Fetched once per page load from /auth/me -- the backend independently enforces every
 * feature via require_feature(...) regardless of what this returns; this is purely so the
 * dashboard can show the right nav links and avoid sending a request it knows will 403. */
export function useCurrentUser(): { user: CurrentUser | null; loading: boolean } {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<CurrentUser>('/api/v1/auth/me')
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  return { user, loading };
}

export function hasFeature(user: CurrentUser | null, feature: string): boolean {
  if (!user) return false;
  return user.role === 'super_admin' || user.allowed_features.includes(feature);
}
