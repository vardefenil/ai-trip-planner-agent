'use client';

import { BookingSummary } from '@/types/travel';

interface BookingSummaryProps {
  summary: BookingSummary;
}

const PROVIDER_ICONS: Record<string, string> = {
  'Booking.com':        '🏨',
  MakeMyTrip:           '✈️',
  IRCTC:                '🚂',
  RailYatri:            '🚂',
  'MakeMyTrip Flights': '✈️',
  RedBus:               '🚌',
  'Google Maps':        '📍',
  TripAdvisor:          '🌟',
  Skyscanner:           '✈️',
};

export function BookingSummaryView({ summary }: BookingSummaryProps) {
  const pkg = summary.selected_package;

  return (
    <div className="booking-summary">
      {/* Header */}
      <div className="booking-header">
        <div className="booking-emoji">🎉</div>
        <h2 className="booking-title">Your Trip is Ready!</h2>
        <p className="booking-message">{summary.confirmation_message}</p>
      </div>

      {/* Package Snapshot */}
      <div className="booking-package-summary">
        <h3 className="summary-pkg-name">{pkg.title}</h3>
        <div className="summary-stats">
          <div className="stat">
            <span className="stat-label">Total Cost</span>
            <span className="stat-value" style={{ color: 'var(--teal)', fontFamily: 'Outfit, sans-serif', fontSize: '18px', fontWeight: 800 }}>
              ₹{pkg.total_cost.toLocaleString('en-IN')}
            </span>
          </div>
          <div className="stat">
            <span className="stat-label">Stay</span>
            <span className="stat-value">{pkg.stay.name}</span>
          </div>
          <div className="stat">
            <span className="stat-label">Transport</span>
            <span className="stat-value">{pkg.transport.provider}</span>
          </div>
          <div className="stat">
            <span className="stat-label">Duration</span>
            <span className="stat-value">{pkg.itinerary.length} Days</span>
          </div>
          {pkg.rental && (
            <div className="stat">
              <span className="stat-label">Local Rental</span>
              <span className="stat-value">{pkg.rental.name}</span>
            </div>
          )}
        </div>
      </div>

      {/* Booking Links */}
      <div className="booking-links-section">
        <h3 className="links-title">🔗 Book Now</h3>
        <div className="links-grid">
          {summary.booking_links.map((link, i) => (
            <a
              key={i}
              href={link.url}
              target="_blank"
              rel="noopener noreferrer"
              className="booking-link-card"
            >
              <span className="link-provider-icon">
                {PROVIDER_ICONS[link.provider] ?? '🔗'}
              </span>
              <div className="link-info">
                <div className="link-label">{link.label}</div>
                <div className="link-provider">{link.provider}</div>
              </div>
              <span className="link-arrow">→</span>
            </a>
          ))}
        </div>
      </div>

      {/* Travel Tips */}
      {summary.tips?.length > 0 && (
        <div className="travel-tips">
          <h3 className="tips-title">💡 Travel Tips</h3>
          <div className="tips-list">
            {summary.tips.map((tip, i) => (
              <div key={i} className="tip-item">{tip}</div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
