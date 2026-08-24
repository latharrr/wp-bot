'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { clearToken } from '@/lib/auth';
import { hasFeature, useCurrentUser } from '@/lib/useCurrentUser';

const LINKS = [
  { href: '/', label: 'Connection', feature: 'connection' },
  { href: '/groups', label: 'Groups', feature: 'groups' },
  { href: '/polls', label: 'All Polls', feature: 'groups' },
  { href: '/keyword-search', label: 'Keyword Search', feature: 'keyword_search' },
  { href: '/scoring', label: 'CSV Scoring', feature: 'csv_scoring' },
  { href: '/exports', label: 'Export Log', feature: 'export_log' },
];

export function NavBar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user } = useCurrentUser();

  const links = LINKS.filter((link) => hasFeature(user, link.feature));

  return (
    <aside className="sidebar">
      <h1>wp-bot</h1>
      <nav>
        {links.map((link) => (
          <Link key={link.href} href={link.href} className={pathname === link.href ? 'active' : undefined}>
            {link.label}
          </Link>
        ))}
        {user?.role === 'super_admin' && (
          <Link href="/admin" className={pathname === '/admin' ? 'active' : undefined}>
            Admin
          </Link>
        )}
        <button
          className="secondary"
          style={{ marginTop: 20 }}
          onClick={() => {
            clearToken();
            router.push('/login');
          }}
        >
          Log out
        </button>
      </nav>
    </aside>
  );
}
