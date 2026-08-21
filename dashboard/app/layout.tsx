import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'wp-bot dashboard',
  description: 'WhatsApp community dashboard: bridge, polls, consent-gated contacts, keyword search',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
