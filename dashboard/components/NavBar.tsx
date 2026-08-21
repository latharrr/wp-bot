'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { clearToken } from '@/lib/auth';

const LINKS = [
  { href: '/', label: 'Connection' },
  { href: '/groups', label: 'Groups' },
  { href: '/keyword-search', label: 'Keyword Search' },
  { href: '/scoring', label: 'CSV Scoring' },
  { href: '/exports', label: 'Export Log' },
];

export function NavBar() {
  const pathname = usePathname();
  const router = useRouter();

  return (
    <aside className="sidebar">
      <h1>wp-bot</h1>
      <nav>
        {LINKS.map((link) => (
          <Link key={link.href} href={link.href} style={pathname === link.href ? { background: 'var(--panel)', fontWeight: 600 } : undefined}>
            {link.label}
          </Link>
        ))}
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
