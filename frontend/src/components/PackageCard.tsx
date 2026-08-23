'use client';

import { TripPackage } from '@/types/travel';
import { useState } from 'react';

interface PackageCardProps {
  pkg: TripPackage;
  isSelected?: boolean;
  onSelect?: (pkg: TripPackage) => void;
  onBook?: (pkg: TripPackage) => void;
}

const TIER_COLORS: Record<string, string> = {
  budget: 'tier-budget',
  'mid-range': 'tier-mid',
  premium: 'tier-premium',
  adventure: 'tier-adventure',
  unique: 'tier-unique',
};

const TRANSPORT_ICONS: Record<string, string> = {
  train: '🚂',
  flight: '✈️',
  bus: '🚌',
  car: '🚗',
};

const RENTAL_ICONS: Record<string, string> = {
  scooter: '🛵',
  motorcycle: '🏍️',
  bicycle: '🚲',
};

export function PackageCard({ pkg, isSelected, onSelect, onBook }: PackageCardProps) {
  const [expandedDay, setExpandedDay] = useState<number | null>(null);
  const tierClass = TIER_COLORS[pkg.tier] || 'tier-mid';

  return (
    <div
      className={`package-card ${tierClass} ${isSelected ? 'selected' : ''}`}
      onClick={() => onSelect?.(pkg)}
    >
      {/* Header */}
      <div className="card-header">
        <div className="card-tier-badge">{pkg.tier.toUpperCase()}</div>
        <div className="card-id">Package #{pkg.package_id}</div>
      </div>

      <h3 className="card-title">{pkg.title}</h3>
      <p className="card-tagline">{pkg.tagline}</p>

      {/* Cost */}
      <div className="card-cost">
        <span className="cost-amount">₹{pkg.total_cost.toLocaleString('en-IN')}</span>
        <span className="cost-label">total cost</span>
        <div className="budget-bar">
          <div
            className="budget-fill"
            style={{ width: `${Math.min(pkg.budget_utilisation_pct, 100)}%` }}
          />
        </div>
        <span className="budget-pct">{pkg.budget_utilisation_pct}% of budget</span>
      </div>

      {/* Stay */}
      <div className="card-section">
        <div className="section-title">🏨 Stay</div>
        <div className="section-content">
          <div className="option-name">{pkg.stay.name}</div>
          <div className="option-meta">
            <span className="rating">⭐ {pkg.stay.rating}</span>
            <span className="price">₹{pkg.stay.price_per_night.toLocaleString('en-IN')}/night</span>
            <span className="type-badge">{pkg.stay.type}</span>
          </div>
          <div className="option-address">📍 {pkg.stay.address}</div>
          {pkg.stay.amenities.length > 0 && (
            <div className="amenities">
              {pkg.stay.amenities.slice(0, 3).map((a) => (
                <span key={a} className="amenity-tag">{a}</span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Transport */}
      <div className="card-section">
        <div className="section-title">
          {TRANSPORT_ICONS[pkg.transport.mode] || '🚗'} Transport
        </div>
        <div className="section-content">
          <div className="option-name">{pkg.transport.provider}</div>
          <div className="option-meta">
            <span className="price">₹{pkg.transport.total_transport_cost.toLocaleString('en-IN')}</span>
            <span className="duration">⏱ {pkg.transport.duration}</span>
          </div>
          {pkg.transport.departure_time && (
            <div className="option-address">🕐 Departure: {pkg.transport.departure_time}</div>
          )}
        </div>
      </div>

      {/* Rental */}
      {pkg.rental && (
        <div className="card-section">
          <div className="section-title">
            {RENTAL_ICONS[pkg.rental.type] || '🛵'} Local Rental
          </div>
          <div className="section-content">
            <div className="option-name">{pkg.rental.name}</div>
            <div className="option-meta">
              <span className="rating">⭐ {pkg.rental.rating}</span>
              <span className="price">₹{pkg.rental.price_per_day}/day</span>
            </div>
          </div>
        </div>
      )}

      {/* Highlights */}
      {pkg.highlights.length > 0 && (
        <div className="card-highlights">
          {pkg.highlights.map((h) => (
            <span key={h} className="highlight-tag">✨ {h}</span>
          ))}
        </div>
      )}

      {/* Why this one */}
      <div className="why-this-one">
        <span className="why-icon">💡</span>
        <p>{pkg.why_this_one}</p>
      </div>

      {/* Itinerary Accordion */}
      <div className="itinerary-section">
        <div className="itinerary-title">📅 Day-by-Day Itinerary</div>
        {pkg.itinerary.map((day) => (
          <div key={day.day} className="day-item">
            <button
              className="day-header"
              onClick={(e) => {
                e.stopPropagation();
                setExpandedDay(expandedDay === day.day ? null : day.day);
              }}
            >
              <span className="day-num">Day {day.day}</span>
              <span className="day-title-text">{day.title}</span>
              <span className="day-cost">₹{day.estimated_cost.toLocaleString('en-IN')}</span>
              <span className="day-chevron">{expandedDay === day.day ? '▲' : '▼'}</span>
            </button>
            {expandedDay === day.day && (
              <div className="day-details">
                <div className="day-activities">
                  {day.activities.map((act, i) => (
                    <div key={i} className="activity">🎯 {act}</div>
                  ))}
                </div>
                <div className="day-meals">
                  {day.meals.map((meal, i) => (
                    <div key={i} className="meal">🍽️ {meal}</div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Book Button */}
      <button
        className="book-btn"
        onClick={(e) => {
          e.stopPropagation();
          onBook?.(pkg);
        }}
      >
        🎉 View Booking Details
      </button>
    </div>
  );
}
