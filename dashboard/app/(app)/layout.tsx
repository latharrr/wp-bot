'use client';

import { NavBar } from '@/components/NavBar';
import { useRequireAuth } from '@/components/useRequireAuth';

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const ready = useRequireAuth();
  if (!ready) return null;

  return (
    <div className="shell">
      <NavBar />
      <main className="main">{children}</main>
    </div>
  );
}
