"""
Stage 2b: Transport Search — trains, buses, and flights.
"""
from agent.state import TravelAgentState, TransportOption
from agent.tools.transport_api import search_transport


async def transport_search(state: TravelAgentState) -> TravelAgentState:
    """LangGraph node: Search for transport options."""
    state.current_stage = "transport_search"
    state.stage_logs.append("🚂 Searching for transport options...")

    trip = state.parsed_trip
    budget_alloc = state.budget_allocation

    if not trip or not budget_alloc:
        state.stage_logs.append("⚠️ No parsed trip data, skipping transport search.")
        return state

    origin = trip.origin if trip.origin != "Not specified" else "Mumbai"

    try:
        raw_options = await search_transport(
            origin=origin,
            destination=trip.destination,
            budget_transport=budget_alloc.transport,
            traveler_count=trip.traveler_count,
            travel_dates=trip.travel_dates,
        )
    except Exception as e:
        state.stage_logs.append(f"⚠️ Transport search error: {e}")
        raw_options = []

    transport_options: list[TransportOption] = []
    for opt in raw_options:
        transport_options.append(TransportOption(
            mode=opt["mode"],
            provider=opt["provider"],
            from_city=opt["from_city"],
            to_city=opt["to_city"],
            price_per_person=opt.get("price_per_person", 0),
            total_transport_cost=opt.get("total_cost", 0),
            duration=opt.get("duration", "N/A"),
            booking_url=opt.get("booking_url", "#"),
            departure_time=opt.get("departure_time"),
        ))

    # Sort by cost
    transport_options.sort(key=lambda x: x.total_transport_cost)
    state.transport_options = transport_options
    state.stage_logs.append(
        f"✅ Found {len(transport_options)} transport options "
        f"(train, bus, flight)"
    )
    return state
