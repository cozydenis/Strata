import type { Metadata } from 'next';
import { IBM_Plex_Mono, Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-sans',
});

const plexMono = IBM_Plex_Mono({
  subsets: ['latin'],
  weight: ['400', '500'],
  variable: '--font-mono',
});

export const metadata: Metadata = {
  title: 'Strata',
  description: 'A living model of every home in Zürich. Spatial intelligence for the housing market.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="de-CH" className={`${inter.variable} ${plexMono.variable}`}>
      <body className="h-screen w-screen overflow-hidden">{children}</body>
    </html>
  );
}
