"""
Stage 2c: Local Rentals Search — bikes and scooters via Google Places.
"""
from agent.state import TravelAgentState, RentalOption
from agent.tools.google_places import search_local_rentals
from agent.tools.gemini_client import gemini_generate_json


async def local_rentals_search(state: TravelAgentState) -> TravelAgentState:
    """LangGraph node: Search for local bike/scooter rental options."""
    state.current_stage = "rental_search"
    state.stage_logs.append("🛵 Searching for local rentals...")

    trip = state.parsed_trip
    budget_alloc = state.budget_allocation

    if not trip or not budget_alloc:
        state.stage_logs.append("⚠️ No parsed trip data, skipping rental search.")
        return state

    rental_budget = budget_alloc.local_rental
    days = trip.duration_days

    try:
        raw_results = await search_local_rentals(trip.destination)
    except Exception as e:
        state.stage_logs.append(f"⚠️ Google Places rental search failed: {e}. Using AI fallback.")
        raw_results = []

    rental_options: list[RentalOption] = []

    if raw_results:
        for place in raw_results[:5]:
            daily_rate = _estimate_daily_rate(place, rental_budget, days)
            maps_url = (
                f"https://www.google.com/maps/place/?q=place_id:{place.get('place_id', '')}"
                if place.get("place_id")
                else None
            )
            rental_options.append(RentalOption(
                name=place.get("name", "Local Rentals"),
                type=_infer_rental_type(place),
                price_per_day=daily_rate,
                total_rental_cost=daily_rate * days,
                rating=float(place.get("rating", 4.0)),
                address=place.get("vicinity", place.get("formatted_address", trip.destination)),
                phone=None,
                maps_url=maps_url,
            ))
    else:
        rental_options = await _gemini_fallback_rentals(trip.destination, rental_budget, days)

    state.rental_options = rental_options
    state.stage_logs.append(
        f"✅ Found {len(rental_options)} rental options in {trip.destination}"
    )
    return state


def _estimate_daily_rate(place: dict, budget: float, days: int) -> float:
    """Estimate daily rental rate from budget or price level."""
    price_level = place.get("price_level", 1)
    rate_map = {0: 150, 1: 300, 2: 600, 3: 1200}
    return rate_map.get(price_level, budget / max(days, 1))


def _infer_rental_type(place: dict) -> str:
    name = place.get("name", "").lower()
    types = place.get("types", [])
    if "motorcycle" in name or "bike" in name:
        return "motorcycle"
    if "scooter" in name or "scooty" in name:
        return "scooter"
    if "bicycle" in types or "cycle" in name:
        return "bicycle"
    return "scooter"


async def _gemini_fallback_rentals(
    destination: str, rental_budget: float, days: int
) -> list[RentalOption]:
    """Ask Gemini to generate realistic rental options for the destination."""
    prompt = f"""
Generate 4 realistic bike/scooter rental options in {destination}, India.
Total rental budget: ₹{rental_budget:,.0f} for {days} days.

Return a JSON array:
[
  {{
    "name": "Rental shop name",
    "type": "scooter | motorcycle | bicycle",
    "price_per_day": <INR per day>,
    "rating": <3.5 to 4.8>,
    "address": "area in {destination}",
    "phone": "+91-XXXXXXXXXX"
  }}
]

Include 1 bicycle (cheapest), 2 scooters (Honda Activa / TVS Jupiter style), 1 motorcycle (Royal Enfield).
Use realistic local shop names for {destination}.
"""
    try:
        data = await gemini_generate_json(prompt)
        results = []
        for item in data[:4]:
            ppd = float(item.get("price_per_day", rental_budget / max(days, 1)))
            results.append(RentalOption(
                name=item.get("name", f"Rentals {destination}"),
                type=item.get("type", "scooter"),
                price_per_day=ppd,
                total_rental_cost=ppd * days,
                rating=float(item.get("rating", 4.0)),
                address=item.get("address", destination),
                phone=item.get("phone"),
                maps_url=f"https://www.google.com/maps/search/bike+rental+{destination}",
            ))
        return results
    except Exception:
        budget_per_day = rental_budget / max(days, 1)
        return [
            RentalOption(
                name=f"GoRentals {destination}",
                type="scooter",
                price_per_day=min(budget_per_day, 400),
                total_rental_cost=min(budget_per_day, 400) * days,
                rating=4.2,
                address=f"Tourist Area, {destination}",
                maps_url=f"https://www.google.com/maps/search/scooter+rental+{destination}",
            ),
            RentalOption(
                name=f"Bullet Bikes {destination}",
                type="motorcycle",
                price_per_day=min(budget_per_day * 1.5, 800),
                total_rental_cost=min(budget_per_day * 1.5, 800) * days,
                rating=4.4,
                address=f"Main Market, {destination}",
                maps_url=f"https://www.google.com/maps/search/motorcycle+rental+{destination}",
            ),
        ]
