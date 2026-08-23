'use client';

import { TripPackage } from '@/types/travel';
import { useState, useEffect, useRef } from 'react';
import { getPackageHeroPhoto, getDestinationPhotos, getStayPhoto, PlacePhoto } from '@/lib/images';

interface PackageCardProps {
  pkg: TripPackage;
  index?: number;
  isSelected?: boolean;
  onSelect?: (pkg: TripPackage) => void;
  onBook?: (pkg: TripPackage) => void;
}

const TIER_CLASSES: Record<string, string> = {
  budget:      'tier-budget',
  'mid-range': 'tier-mid',
  premium:     'tier-premium',
  adventure:   'tier-adventure',
  unique:      'tier-unique',
};

const TRANSPORT_ICONS: Record<string, string> = {
  train: '🚂', flight: '✈️', bus: '🚌', car: '🚗', cab: '🚕',
};

const RENTAL_ICONS: Record<string, string> = {
  scooter: '🛵', motorcycle: '🏍️', bicycle: '🚲', car: '🚗',
};

function StarRating({ rating }: { rating: number }) {
  return (
    <div className="stars-wrap">
      {[1, 2, 3, 4, 5].map((i) => (
        <span key={i} className={`star ${i <= Math.round(rating) ? 'filled' : 'empty'}`}>★</span>
      ))}
      <span className="rating-num">{rating.toFixed(1)}</span>
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
  const [photoIndex, setPhotoIndex] = useState<number>(index % 5);
  const [isVisible, setIsVisible] = useState(false);
  const cardRef = useRef<HTMLDivElement>(null);
  const tierClass = TIER_CLASSES[pkg.tier] ?? 'tier-mid';

  // Get gallery for destination
  const destinationGallery = getDestinationPhotos(
    `${pkg.stay?.address || ''} ${pkg.title} ${pkg.tagline}`,
    pkg.title
  );

  // Set default photo based on index
  const currentPhoto: PlacePhoto = destinationGallery[photoIndex % destinationGallery.length] ||
    getPackageHeroPhoto(pkg.stay?.address || '', index, pkg.title);

  const stayImg = getStayPhoto(pkg.stay?.type || '', pkg.stay?.name || '', index);

  // IntersectionObserver for scroll-triggered animation attached to the scrollable chat container
  useEffect(() => {
    const el = cardRef.current;
    if (!el) return;

    const scrollContainer = document.querySelector('.messages-container');

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
        }
      },
      {
        root: scrollContainer,
        threshold: 0.08,
        rootMargin: '50px 0px 50px 0px',
      }
    );

    observer.observe(el);
    // Trigger immediately if already in view
    const rect = el.getBoundingClientRect();
    if (rect.top < window.innerHeight && rect.bottom > 0) {
      setIsVisible(true);
    }

    return () => observer.disconnect();
  }, []);

  const handleNextPhoto = (e: React.MouseEvent) => {
    e.stopPropagation();
    setPhotoIndex((prev) => (prev + 1) % destinationGallery.length);
  };

  const handlePrevPhoto = (e: React.MouseEvent) => {
    e.stopPropagation();
    setPhotoIndex((prev) => (prev - 1 + destinationGallery.length) % destinationGallery.length);
  };

  return (
    <div
      ref={cardRef}
      className={`package-card ${tierClass} ${isSelected ? 'selected' : ''} ${isVisible ? 'card-visible' : ''} stagger-${index % 5}`}
      onClick={() => onSelect?.(pkg)}
    >
      {/* Hero Image & Place Gallery */}
      <div className="card-hero">
        <img
          key={currentPhoto.url}
          src={currentPhoto.url}
          alt={currentPhoto.caption}
          className="card-hero-img"
          loading="lazy"
        />
        <div className="card-hero-overlay" />

        {/* Badges */}
        <div className="card-hero-badges">
          <div className="card-tier-badge">{pkg.tier.toUpperCase()}</div>
          <div className="card-pkg-num">Option #{pkg.package_id}</div>
        </div>

        {/* Photo Gallery Navigation & Caption */}
        <div className="card-photo-controls">
          <button className="photo-nav-btn" onClick={handlePrevPhoto} title="Previous Place Photo">‹</button>
          <div className="photo-caption-pill">
            <span className="photo-pin">📍</span> {currentPhoto.caption}
          </div>
          <button className="photo-nav-btn" onClick={handleNextPhoto} title="Next Place Photo">›</button>
        </div>

        <div className="card-hero-bottom">
          <h3 className="card-title">{pkg.title}</h3>
          <p className="card-tagline">{pkg.tagline}</p>
        </div>
      </div>

      {/* Card Body */}
      <div className="card-body">
        {/* Cost & Budget Ring */}
        <div className="card-cost">
          <div className="cost-left">
            <div className="cost-amount">₹{pkg.total_cost.toLocaleString('en-IN')}</div>
            <div className="cost-label">Total Trip Cost</div>
          </div>
          <BudgetRing pct={pkg.budget_utilisation_pct} tierClass={tierClass} />
        </div>

        {/* Stay Section */}
        <div className="card-section">
          <div className="section-header">
            <div className="section-icon stay">🏨</div>
            <span className="section-label">Stay Option</span>
          </div>
          <div className="section-body">
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

        {/* Transport Section */}
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
              <div className="option-address">🕐 Departure: {pkg.transport.departure_time}</div>
            )}
          </div>
        </div>

        {/* Rental Section */}
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

        {/* Itinerary Accordion */}
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
                    <div className="day-section-label">Meals & Food</div>
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
