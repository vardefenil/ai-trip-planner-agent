'use client';

import { TripPackage } from '@/types/travel';
import { useState, useEffect, useRef } from 'react';
import Image from 'next/image';

interface PackageCardProps {
  pkg: TripPackage;
  index?: number;
  isSelected?: boolean;
  onSelect?: (pkg: TripPackage) => void;
  onBook?: (pkg: TripPackage) => void;
}

const TIER_CLASSES: Record<string, string> = {
  budget:    'tier-budget',
  'mid-range': 'tier-mid',
  premium:   'tier-premium',
  adventure: 'tier-adventure',
  unique:    'tier-unique',
};

const TRANSPORT_ICONS: Record<string, string> = {
  train: '🚂', flight: '✈️', bus: '🚌', car: '🚗', cab: '🚕',
};

const RENTAL_ICONS: Record<string, string> = {
  scooter: '🛵', motorcycle: '🏍️', bicycle: '🚲', car: '🚗',
};

// Curated Unsplash destination hero images (landscape, travel-grade)
const DESTINATION_HERO: Record<string, string> = {
  goa:       'https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?w=800&q=80',
  manali:    'https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?w=800&q=80',
  kerala:    'https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?w=800&q=80',
  rajasthan: 'https://images.unsplash.com/photo-1477587458883-47145ed94245?w=800&q=80',
  ladakh:    'https://images.unsplash.com/photo-1571401835393-8c5f35328320?w=800&q=80',
  andaman:   'https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=800&q=80',
  shimla:    'https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?w=800&q=80',
  ooty:      'https://images.unsplash.com/photo-1502082553048-f009c37129b9?w=800&q=80',
  varanasi:  'https://images.unsplash.com/photo-1561361058-c24e01c735db?w=800&q=80',
  agra:      'https://images.unsplash.com/photo-1564507592333-c60657eea523?w=800&q=80',
  mumbai:    'https://images.unsplash.com/photo-1570168007204-dfb528c6958f?w=800&q=80',
  delhi:     'https://images.unsplash.com/photo-1587474260584-136574528ed5?w=800&q=80',
  jaipur:    'https://images.unsplash.com/photo-1477587458883-47145ed94245?w=800&q=80',
  beach:     'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=800&q=80',
  mountain:  'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&q=80',
  default:   'https://images.unsplash.com/photo-1524492412937-b28074a5d7da?w=800&q=80',
};

// Hotel/stay images from Unsplash
const STAY_IMAGES: Record<string, string> = {
  resort:  'https://images.unsplash.com/photo-1571003123894-1f0594d2b5d9?w=600&q=80',
  hotel:   'https://images.unsplash.com/photo-1455587734955-081b22074882?w=600&q=80',
  hostel:  'https://images.unsplash.com/photo-1555854877-bab0e564b8d5?w=600&q=80',
  airbnb:  'https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=600&q=80',
  lodge:   'https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?w=600&q=80',
  default: 'https://images.unsplash.com/photo-1564501049412-61c2a3083791?w=600&q=80',
};

function getDestinationImage(destination: string, vibe: string): string {
  const key = destination?.toLowerCase().split(' ')[0];
  if (key && DESTINATION_HERO[key]) return DESTINATION_HERO[key];
  if (vibe && DESTINATION_HERO[vibe.toLowerCase()]) return DESTINATION_HERO[vibe.toLowerCase()];
  return DESTINATION_HERO.default;
}

function getStayImage(stayType: string): string {
  return STAY_IMAGES[stayType?.toLowerCase()] ?? STAY_IMAGES.default;
}

function StarRating({ rating }: { rating: number }) {
  return (
    <div className="stars-wrap">
      {[1, 2, 3, 4, 5].map((i) => (
        <span key={i} className={`star ${i <= Math.round(rating) ? 'filled' : 'empty'}`}>★</span>
      ))}
      <span style={{ fontSize: '10px', color: 'var(--text-3)', marginLeft: 4 }}>{rating.toFixed(1)}</span>
    </div>
  );
}

function BudgetRing({ pct, tierClass }: { pct: number; tierClass: string }) {
  const r = 20;
  const circ = 2 * Math.PI * r;
  const offset = circ - (Math.min(pct, 100) / 100) * circ;

  return (
    <div className="budget-ring-wrap">
      <svg viewBox="0 0 52 52">
        <circle cx="26" cy="26" r={r} className="budget-ring-bg" />
        <circle
          cx="26" cy="26" r={r}
          className={`budget-ring-fill ${tierClass}`}
          strokeDasharray={circ}
          strokeDashoffset={offset}
        />
      </svg>
      <div className="budget-pct-center">{Math.round(pct)}%</div>
    </div>
  );
}

export function PackageCard({ pkg, index = 0, isSelected, onSelect, onBook }: PackageCardProps) {
  const [expandedDay, setExpandedDay] = useState<number | null>(null);
  const [isVisible, setIsVisible] = useState(false);
  const cardRef = useRef<HTMLDivElement>(null);
  const tierClass = TIER_CLASSES[pkg.tier] ?? 'tier-mid';

  // IntersectionObserver for scroll-triggered animation
  useEffect(() => {
    const el = cardRef.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.disconnect();
        }
      },
      { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  const heroImg = getDestinationImage(pkg.stay?.address ?? '', pkg.tier);
  const stayImg = getStayImage(pkg.stay?.type ?? 'hotel');

  return (
    <div
      ref={cardRef}
      className={`package-card ${tierClass} ${isSelected ? 'selected' : ''} ${isVisible ? 'card-visible' : ''} stagger-${index % 5}`}
      onClick={() => onSelect?.(pkg)}
    >
      {/* Hero Image */}
      <div className="card-hero">
        <img
          src={heroImg}
          alt={`${pkg.title} destination`}
          className="card-hero-img"
          loading="lazy"
        />
        <div className="card-hero-overlay" />
        <div className="card-hero-badges">
          <div className="card-tier-badge">{pkg.tier.toUpperCase()}</div>
          <div className="card-pkg-num">#{pkg.package_id}</div>
        </div>
        <div className="card-hero-bottom">
          <h3 className="card-title">{pkg.title}</h3>
          <p className="card-tagline">{pkg.tagline}</p>
        </div>
      </div>

      {/* Card Body */}
      <div className="card-body">
        {/* Cost */}
        <div className="card-cost">
          <div className="cost-left">
            <div className="cost-amount">₹{pkg.total_cost.toLocaleString('en-IN')}</div>
            <div className="cost-label">Total Trip Cost</div>
          </div>
          <BudgetRing pct={pkg.budget_utilisation_pct} tierClass={tierClass} />
        </div>

        {/* Stay */}
        <div className="card-section">
          <div className="section-header">
            <div className="section-icon stay">🏨</div>
            <span className="section-label">Stay</span>
          </div>
          <div className="section-body">
            {/* Stay image */}
            <div className="stay-img-wrap">
              <img
                src={stayImg}
                alt={pkg.stay.name}
                className="stay-img"
                loading="lazy"
              />
            </div>
            <div className="option-name">{pkg.stay.name}</div>
            <div className="option-meta">
              <StarRating rating={pkg.stay.rating} />
              <span className="price-tag">₹{pkg.stay.price_per_night.toLocaleString('en-IN')}/night</span>
              <span className="type-chip">{pkg.stay.type}</span>
            </div>
            <div className="option-address">📍 {pkg.stay.address}</div>
            {pkg.stay.amenities.length > 0 && (
              <div className="amenities">
                {pkg.stay.amenities.slice(0, 4).map((a) => (
                  <span key={a} className="amenity-tag">{a}</span>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Transport */}
        <div className="card-section">
          <div className="section-header">
            <div className="section-icon transport">{TRANSPORT_ICONS[pkg.transport.mode] ?? '🚗'}</div>
            <span className="section-label">Transport</span>
          </div>
          <div className="section-body">
            <div className="option-name">{pkg.transport.provider}</div>
            <div className="option-meta">
              <span className="price-tag">₹{pkg.transport.total_transport_cost.toLocaleString('en-IN')}</span>
              <span style={{ fontSize: '11px', color: 'var(--text-3)' }}>⏱ {pkg.transport.duration}</span>
            </div>
            {pkg.transport.departure_time && (
              <div className="option-address">🕐 {pkg.transport.departure_time}</div>
            )}
          </div>
        </div>

        {/* Rental */}
        {pkg.rental && (
          <div className="card-section">
            <div className="section-header">
              <div className="section-icon rental">{RENTAL_ICONS[pkg.rental.type] ?? '🛵'}</div>
              <span className="section-label">Local Rental</span>
            </div>
            <div className="section-body">
              <div className="option-name">{pkg.rental.name}</div>
              <div className="option-meta">
                <StarRating rating={pkg.rental.rating} />
                <span className="price-tag">₹{pkg.rental.price_per_day}/day</span>
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

        {/* Itinerary */}
        <div className="itinerary-section">
          <div className="itinerary-header">
            <span className="itinerary-label">📅 Day-by-Day Itinerary</span>
          </div>
          {pkg.itinerary.map((day) => (
            <div key={day.day} className={`day-item ${expandedDay === day.day ? 'expanded' : ''}`}>
              <button
                className="day-header"
                onClick={(e) => {
                  e.stopPropagation();
                  setExpandedDay(expandedDay === day.day ? null : day.day);
                }}
              >
                <span className="day-badge">Day {day.day}</span>
                <span className="day-title-text">{day.title}</span>
                <span className="day-cost">₹{day.estimated_cost.toLocaleString('en-IN')}</span>
                <span className={`day-chevron ${expandedDay === day.day ? 'open' : ''}`}>▼</span>
              </button>
              {/* Smooth CSS transition accordion */}
              <div className={`day-details ${expandedDay === day.day ? 'open' : ''}`}>
                <div className="day-details-inner">
                  <div className="day-activities-list">
                    <div className="day-section-label">Activities</div>
                    {day.activities.map((act, i) => (
                      <div key={i} className="activity-item">
                        <span className="activity-dot" />
                        {act}
                      </div>
                    ))}
                  </div>
                  <div className="day-meals-list">
                    <div className="day-section-label">Meals</div>
                    {day.meals.map((meal, i) => (
                      <div key={i} className="meal-item">
                        <span className="meal-dot" />
                        {meal}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
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
    </div>
  );
}
