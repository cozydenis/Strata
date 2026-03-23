import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-sans',
});

export const metadata: Metadata = {
  title: 'Strata',
  description: 'Spatial intelligence platform for the Zurich housing market',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="de-CH" className={inter.variable}>
      <body className="h-screen w-screen overflow-hidden">{children}</body>
    </html>
  );
}
