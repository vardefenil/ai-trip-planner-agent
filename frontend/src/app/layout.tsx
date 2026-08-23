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
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400&family=Playfair+Display:wght@700;800&family=Outfit:wght@400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
