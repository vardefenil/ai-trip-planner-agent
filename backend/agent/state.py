"""
Pydantic State Schema for the LangGraph Travel Planner pipeline.
"""
from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


# ────────────────────────────────────────────────────────────
# Input / Request models
# ────────────────────────────────────────────────────────────

class TripRequest(BaseModel):
    raw_query: str = Field(..., description="Free-text trip request from the user")
    session_id: Optional[str] = None


# ────────────────────────────────────────────────────────────
# Parsed & structured trip details
# ────────────────────────────────────────────────────────────

class ParsedTrip(BaseModel):
    origin: str = Field(default="Not specified")
    destination: str
    budget_total: float = Field(..., description="Total budget in INR")
    duration_days: int
    traveler_count: int = Field(default=1)
    vibe: str = Field(
        default="relaxed",
        description="beach | mountain | city | adventure | relaxed",
    )
    travel_dates: Optional[str] = None


class BudgetAllocation(BaseModel):
    stay: float
    transport: float
    food: float
    local_rental: float
    buffer: float
    destination_type: str  # beach | mountain | city


# ────────────────────────────────────────────────────────────
# Search result models
# ────────────────────────────────────────────────────────────

class StayOption(BaseModel):
    name: str
    type: str  # hotel | hostel | airbnb | resort
    price_per_night: float
    total_stay_cost: float
    rating: float
    address: str
    booking_url: str
    image_url: Optional[str] = None
    amenities: list[str] = []
    review_summary: Optional[str] = None


class TransportOption(BaseModel):
    mode: str  # train | flight | bus
    provider: str
    from_city: str
    to_city: str
    price_per_person: float
    total_transport_cost: float
    duration: str
    booking_url: str
    departure_time: Optional[str] = None


class RentalOption(BaseModel):
    name: str
    type: str  # bicycle | scooter | motorcycle
    price_per_day: float
    total_rental_cost: float
    rating: float
    address: str
    phone: Optional[str] = None
    maps_url: Optional[str] = None


# ────────────────────────────────────────────────────────────
# Itinerary & package models
# ────────────────────────────────────────────────────────────

class DayPlan(BaseModel):
    day: int
    title: str
    activities: list[str]
    meals: list[str]
    estimated_cost: float


class TripPackage(BaseModel):
    package_id: int
    title: str
    tagline: str
    stay: StayOption
    transport: TransportOption
    rental: Optional[RentalOption] = None
    itinerary: list[DayPlan]
    total_cost: float
    budget_utilisation_pct: float
    highlights: list[str]
    why_this_one: str
    tier: str  # budget | mid-range | premium


class BookingLink(BaseModel):
    label: str
    url: str
    provider: str


class BookingSummary(BaseModel):
    selected_package: TripPackage
    confirmation_message: str
    booking_links: list[BookingLink]
    tips: list[str]


# ────────────────────────────────────────────────────────────
# LangGraph Agent State
# ────────────────────────────────────────────────────────────

class TravelAgentState(BaseModel):
    """The shared state that flows through the LangGraph pipeline."""

    # Input
    raw_query: str = ""
    session_id: str = ""
    conversation_history: list[dict[str, str]] = []

    # Stage 1 outputs
    parsed_trip: Optional[ParsedTrip] = None
    budget_allocation: Optional[BudgetAllocation] = None

    # Stage 2 outputs
    stay_options: list[StayOption] = []
    transport_options: list[TransportOption] = []
    rental_options: list[RentalOption] = []

    # Stage 3 outputs
    ranked_packages: list[TripPackage] = []

    # Stage 4 state
    presented_packages: list[TripPackage] = []
    user_modification_request: Optional[str] = None
    modification_count: int = 0

    # Stage 5 output
    booking_summary: Optional[BookingSummary] = None

    # Pipeline metadata
    current_stage: str = "idle"
    error: Optional[str] = None
    stage_logs: list[str] = []

    class Config:
        arbitrary_types_allowed = True
