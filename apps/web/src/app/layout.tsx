import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Strata',
  description: 'Spatial intelligence platform for the Zurich housing market',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="de-CH">
      <body className="h-screen w-screen overflow-hidden">{children}</body>
    </html>
  );
}
