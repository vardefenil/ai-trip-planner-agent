import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Yatra AI — India Travel Planner',
  description: 'AI-powered travel planning agent for India. Get 5 personalised trip packages with hotels, transport, and day-by-day itineraries.',
  keywords: ['travel', 'India', 'trip planner', 'AI', 'Goa', 'Manali', 'Kerala'],
  openGraph: {
    title: 'Yatra AI — India Travel Planner',
    description: 'AI-powered Indian travel planning assistant',
    type: 'website',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body>{children}</body>
    </html>
  );
}
