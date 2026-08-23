"""
Stage 2a: Stay Search — Hotels, resorts, guesthouses via Google Places.
"""
import asyncio
from agent.state import TravelAgentState, StayOption
from agent.tools.google_places import search_hotels, get_place_details, get_place_photo_url
from agent.tools.gemini_client import gemini_generate_json

# Price level to estimated nightly rate (INR)
PRICE_LEVEL_MAP = {
    0: 800,    # Free / very cheap
    1: 1500,   # Budget
    2: 3500,   # Moderate
    3: 7000,   # Upscale
    4: 15000,  # Luxury
}

BOOKING_URL_TEMPLATES = {
    "booking": "https://www.booking.com/searchresults.html?ss={destination}&checkin={checkin}&checkout={checkout}&group_adults={adults}",
    "makemytrip": "https://www.makemytrip.com/hotels/{destination_slug}-hotels.html",
    "goibibo": "https://www.goibibo.com/hotels/hotels-in-{destination_slug}/",
}


async def stay_search(state: TravelAgentState) -> TravelAgentState:
    """LangGraph node: Search for stay options in the destination."""
    state.current_stage = "stay_search"
    state.stage_logs.append("🏨 Searching for stays...")

    trip = state.parsed_trip
    budget_alloc = state.budget_allocation

    if not trip or not budget_alloc:
        state.stage_logs.append("⚠️ No parsed trip data, skipping stay search.")
        return state

    stay_budget = budget_alloc.stay
    nights = trip.duration_days - 1 or 1
    budget_per_night = stay_budget / nights

    try:
        raw_results = await search_hotels(trip.destination, budget_per_night)
    except Exception as e:
        state.stage_logs.append(f"⚠️ Google Places unavailable: {e}. Using AI-generated stays.")
        raw_results = []

    stay_options: list[StayOption] = []

    if raw_results:
        # Process real Places results
        for place in raw_results[:6]:
            price_level = place.get("price_level", 2)
            est_price_per_night = PRICE_LEVEL_MAP.get(price_level, 3000)
            total = est_price_per_night * nights
            rating = place.get("rating", 4.0)

            # Get photo URL if available
            photo_url = None
            photos = place.get("photos", [])
            if photos:
                photo_ref = photos[0].get("photo_reference", "")
                if photo_ref:
                    photo_url = await get_place_photo_url(photo_ref)

            dest_slug = trip.destination.lower().replace(" ", "-")
            booking_url = BOOKING_URL_TEMPLATES["booking"].format(
                destination=trip.destination,
                checkin=trip.travel_dates or "2025-01-15",
                checkout=trip.travel_dates or "2025-01-20",
                adults=trip.traveler_count,
            )

            stay_options.append(StayOption(
                name=place.get("name", ""),
                type=_infer_stay_type(place),
                price_per_night=est_price_per_night,
                total_stay_cost=total,
                rating=rating,
                address=place.get("formatted_address", place.get("vicinity", "")),
                booking_url=booking_url,
                image_url=photo_url,
                amenities=_infer_amenities(place),
                review_summary=None,
            ))

    else:
        # Fallback: Gemini generates realistic stay options
        stay_options = await _gemini_fallback_stays(trip.destination, stay_budget, nights, trip.traveler_count)

    # Filter by budget (keep options within 1.5x budget for variety)
    affordable = [s for s in stay_options if s.total_stay_cost <= stay_budget * 1.5]
    state.stay_options = affordable or stay_options[:5]
    state.stage_logs.append(f"✅ Found {len(state.stay_options)} stay options in {trip.destination}")
    return state


def _infer_stay_type(place: dict) -> str:
    types = place.get("types", [])
    name = place.get("name", "").lower()
    if "resort" in name:
        return "resort"
    if "hostel" in name or "backpacker" in name:
        return "hostel"
    if "airbnb" in name or "villa" in name or "homestay" in name:
        return "airbnb"
    if "lodge" in name:
        return "lodge"
    return "hotel"


def _infer_amenities(place: dict) -> list[str]:
    amenities = []
    name = place.get("name", "").lower()
    rating = place.get("rating", 0)
    if rating >= 4.0:
        amenities.append("WiFi")
        amenities.append("AC")
    if "pool" in name or "resort" in name:
        amenities.append("Swimming Pool")
    if "beach" in name:
        amenities.append("Beach Access")
    if "spa" in name:
        amenities.append("Spa")
    if not amenities:
        amenities = ["WiFi", "AC", "24/7 Reception"]
    return amenities


async def _gemini_fallback_stays(
    destination: str,
    stay_budget: float,
    nights: int,
    traveler_count: int,
) -> list[StayOption]:
    """Ask Gemini to generate realistic stay options when Places API is unavailable."""
    prompt = f"""
Generate 5 realistic hotel/stay options for a trip to {destination}, India.
Budget for stay: ₹{stay_budget:,.0f} total for {nights} nights, {traveler_count} traveler(s).

Return a JSON array of 5 objects:
[
  {{
    "name": "Hotel name",
    "type": "hotel | resort | hostel | airbnb | lodge",
    "price_per_night": <INR per night>,
    "rating": <4.0 to 4.8>,
    "address": "area, {destination}",
    "amenities": ["WiFi", "AC", "Pool"],
    "review_summary": "One sentence why travellers love it"
  }}
]

Make the options diverse: 1 budget, 2 mid-range, 1 premium, 1 unique (homestay/airbnb).
Use real-sounding names for {destination}.
"""
    try:
        data = await gemini_generate_json(prompt)
        results = []
        for item in data[:5]:
            pn = float(item.get("price_per_night", stay_budget / (nights or 1)))
            dest_slug = destination.lower().replace(" ", "-")
            results.append(StayOption(
                name=item.get("name", f"Hotel in {destination}"),
                type=item.get("type", "hotel"),
                price_per_night=pn,
                total_stay_cost=pn * nights,
                rating=float(item.get("rating", 4.0)),
                address=item.get("address", destination),
                booking_url=f"https://www.booking.com/searchresults.html?ss={destination}",
                amenities=item.get("amenities", ["WiFi", "AC"]),
                review_summary=item.get("review_summary"),
            ))
        return results
    except Exception:
        # Hard fallback
        budget_per_night = stay_budget / (nights or 1)
        return [
            StayOption(
                name=f"Premium Hotel {destination}",
                type="hotel",
                price_per_night=budget_per_night * 1.2,
                total_stay_cost=budget_per_night * 1.2 * nights,
                rating=4.5,
                address=f"City Centre, {destination}",
                booking_url=f"https://www.booking.com/searchresults.html?ss={destination}",
                amenities=["WiFi", "AC", "Room Service"],
            ),
            StayOption(
                name=f"Budget Guesthouse {destination}",
                type="hostel",
                price_per_night=budget_per_night * 0.5,
                total_stay_cost=budget_per_night * 0.5 * nights,
                rating=4.0,
                address=f"Market Area, {destination}",
                booking_url=f"https://www.booking.com/searchresults.html?ss={destination}",
                amenities=["WiFi", "Shared Kitchen"],
            ),
        ]
