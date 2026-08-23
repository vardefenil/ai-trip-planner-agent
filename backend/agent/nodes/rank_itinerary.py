"""
Stage 3: Rank options and build day-wise itinerary using Gemini.
"""
from agent.state import TravelAgentState, TripPackage, DayPlan, StayOption, TransportOption, RentalOption
from agent.tools.gemini_client import gemini_generate_json


TIER_MULTIPLIERS = {
    "budget": 0.6,
    "mid-range": 1.0,
    "premium": 1.4,
    "luxury": 1.8,
    "unique": 0.85,
}


async def rank_and_build_itinerary(state: TravelAgentState) -> TravelAgentState:
    """
    LangGraph node: Rank all search results and build 5 diverse trip packages
    with day-by-day itineraries using Gemini.
    """
    state.current_stage = "ranking_itinerary"
    state.stage_logs.append("🎯 Ranking options and building itineraries...")

    trip = state.parsed_trip
    budget = state.budget_allocation

    if not trip or not budget:
        state.stage_logs.append("⚠️ Missing trip data, cannot rank.")
        return state

    # Prepare summaries for Gemini
    stays_summary = _summarise_stays(state.stay_options)
    transport_summary = _summarise_transport(state.transport_options)
    rentals_summary = _summarise_rentals(state.rental_options)

    prompt = f"""
You are an expert Indian travel planner. Build 5 diverse trip packages for the following trip:

TRIP DETAILS:
- Destination: {trip.destination}
- Origin: {trip.origin}
- Budget: ₹{trip.budget_total:,.0f} total
- Duration: {trip.duration_days} days
- Travelers: {trip.traveler_count}
- Vibe: {trip.vibe}

BUDGET ALLOCATION:
- Stay: ₹{budget.stay:,.0f}
- Transport: ₹{budget.transport:,.0f}
- Food: ₹{budget.food:,.0f}
- Local Rental: ₹{budget.local_rental:,.0f}
- Buffer: ₹{budget.buffer:,.0f}

AVAILABLE STAYS:
{stays_summary}

AVAILABLE TRANSPORT:
{transport_summary}

AVAILABLE RENTALS:
{rentals_summary}

Create 5 DISTINCT packages (budget, mid-range, premium, adventure-focused, unique/local). 
Each package must use DIFFERENT combinations.

Return a JSON array of 5 package objects:
[
  {{
    "package_id": 1,
    "title": "Package name",
    "tagline": "One exciting line describing it",
    "tier": "budget | mid-range | premium | adventure | unique",
    "stay_index": <index from stays list, 0-based>,
    "transport_index": <index from transport list, 0-based>,
    "rental_index": <index from rentals list or null>,
    "itinerary": [
      {{
        "day": 1,
        "title": "Day title",
        "activities": ["Activity 1", "Activity 2", "Activity 3"],
        "meals": ["Breakfast at X", "Lunch at Y", "Dinner at Z"],
        "estimated_cost": <INR>
      }}
    ],
    "highlights": ["Highlight 1", "Highlight 2", "Highlight 3"],
    "why_this_one": "2-3 sentences explaining why this package stands out"
  }}
]

IMPORTANT:
- Each itinerary must have exactly {trip.duration_days} days
- Highlights should be specific to {trip.destination}
- Food suggestions should include local {trip.destination} cuisine
- why_this_one should mention the specific hotel and transport chosen
- Keep total_cost within ₹{trip.budget_total * 1.1:,.0f}
"""

    try:
        packages_data = await gemini_generate_json(prompt)
    except Exception as e:
        state.stage_logs.append(f"⚠️ Gemini ranking failed: {e}")
        state.ranked_packages = _build_fallback_packages(state)
        return state

    packages: list[TripPackage] = []
    stays = state.stay_options
    transports = state.transport_options
    rentals = state.rental_options

    for pkg_data in packages_data[:5]:
        try:
            stay_idx = pkg_data.get("stay_index", 0)
            transport_idx = pkg_data.get("transport_index", 0)
            rental_idx = pkg_data.get("rental_index")

            stay = stays[stay_idx] if stay_idx < len(stays) else stays[0]
            transport = transports[transport_idx] if transport_idx < len(transports) else transports[0]
            rental = rentals[rental_idx] if rental_idx is not None and rental_idx < len(rentals) else None

            # Build day plans
            day_plans = []
            for day_data in pkg_data.get("itinerary", []):
                day_plans.append(DayPlan(
                    day=day_data.get("day", 1),
                    title=day_data.get("title", f"Day {day_data.get('day', 1)}"),
                    activities=day_data.get("activities", []),
                    meals=day_data.get("meals", []),
                    estimated_cost=float(day_data.get("estimated_cost", budget.food / trip.duration_days)),
                ))

            # Calculate total cost
            total = (
                stay.total_stay_cost
                + transport.total_transport_cost
                + (rental.total_rental_cost if rental else 0)
                + budget.food
            )
            utilisation_pct = (total / trip.budget_total) * 100

            packages.append(TripPackage(
                package_id=pkg_data.get("package_id", len(packages) + 1),
                title=pkg_data.get("title", f"Package {len(packages)+1}"),
                tagline=pkg_data.get("tagline", ""),
                stay=stay,
                transport=transport,
                rental=rental,
                itinerary=day_plans,
                total_cost=round(total),
                budget_utilisation_pct=round(utilisation_pct, 1),
                highlights=pkg_data.get("highlights", []),
                why_this_one=pkg_data.get("why_this_one", ""),
                tier=pkg_data.get("tier", "mid-range"),
            ))
        except Exception as e:
            state.stage_logs.append(f"⚠️ Error building package {len(packages)+1}: {e}")
            continue

    state.ranked_packages = packages
    state.stage_logs.append(f"✅ Built {len(packages)} trip packages")
    return state


def _summarise_stays(stays: list[StayOption]) -> str:
    if not stays:
        return "No stays found."
    lines = []
    for i, s in enumerate(stays):
        lines.append(f"{i}. {s.name} ({s.type}) — ₹{s.price_per_night:,.0f}/night, Rating: {s.rating} — {s.address}")
    return "\n".join(lines)


def _summarise_transport(transports: list[TransportOption]) -> str:
    if not transports:
        return "No transport found."
    lines = []
    for i, t in enumerate(transports):
        lines.append(f"{i}. {t.mode.upper()}: {t.provider} — ₹{t.total_transport_cost:,.0f} total, {t.duration}")
    return "\n".join(lines)


def _summarise_rentals(rentals: list[RentalOption]) -> str:
    if not rentals:
        return "No rentals found."
    lines = []
    for i, r in enumerate(rentals):
        lines.append(f"{i}. {r.name} ({r.type}) — ₹{r.price_per_day:,.0f}/day, Rating: {r.rating}")
    return "\n".join(lines)


def _build_fallback_packages(state: TravelAgentState) -> list[TripPackage]:
    """Simple fallback: pair stays and transports directly."""
    trip = state.parsed_trip
    budget = state.budget_allocation
    packages = []
    stays = state.stay_options or []
    transports = state.transport_options or []
    rentals = state.rental_options or []

    if not stays or not transports:
        return []

    for i in range(min(3, len(stays), len(transports))):
        stay = stays[i]
        transport = transports[i % len(transports)]
        rental = rentals[i % len(rentals)] if rentals else None
        total = stay.total_stay_cost + transport.total_transport_cost + (rental.total_rental_cost if rental else 0) + (budget.food if budget else 0)

        packages.append(TripPackage(
            package_id=i + 1,
            title=f"Package {i+1}: {trip.destination if trip else 'Trip'}",
            tagline=f"A wonderful {trip.vibe if trip else 'relaxed'} experience",
            stay=stay,
            transport=transport,
            rental=rental,
            itinerary=[
                DayPlan(
                    day=d + 1,
                    title=f"Day {d+1} in {trip.destination if trip else 'destination'}",
                    activities=["Explore local attractions", "Rest and relax"],
                    meals=["Breakfast", "Lunch", "Dinner"],
                    estimated_cost=(budget.food / (trip.duration_days or 5)) if budget and trip else 500,
                )
                for d in range(trip.duration_days if trip else 3)
            ],
            total_cost=round(total),
            budget_utilisation_pct=round((total / trip.budget_total) * 100 if trip else 80, 1),
            highlights=["Local culture", "Great food", "Beautiful scenery"],
            why_this_one="A great value-for-money option for your trip.",
            tier=["budget", "mid-range", "premium"][i % 3],
        ))
    return packages
