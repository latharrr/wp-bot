'use client';

import { hasFeature, useCurrentUser } from '@/lib/useCurrentUser';

/** Wraps a feature page so a 'user' account without that feature granted sees a clear message
 * instead of the page firing off API calls that will 403. The backend enforces this
 * independently (require_feature(...) on the router) -- this is just the friendly UI half. */
export function RequireFeature({ feature, children }: { feature: string; children: React.ReactNode }) {
  const { user, loading } = useCurrentUser();

  if (loading) return <p className="muted">Loading...</p>;
  if (!hasFeature(user, feature)) {
    return (
      <div className="card">
        <p>You don't have access to this feature. Ask your admin to enable it for your account.</p>
      </div>
    );
  }
  return <>{children}</>;
}
