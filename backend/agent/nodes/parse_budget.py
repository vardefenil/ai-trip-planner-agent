"""
Stage 1: Parse free-text trip request and allocate budget by category.
"""
import json
from agent.state import TravelAgentState, ParsedTrip, BudgetAllocation
from agent.tools.gemini_client import gemini_generate_json

# Budget allocation ratios per destination type
BUDGET_RATIOS = {
    "beach": {
        "stay": 0.35,
        "transport": 0.25,
        "food": 0.20,
        "local_rental": 0.15,
        "buffer": 0.05,
    },
    "mountain": {
        "stay": 0.40,
        "transport": 0.30,
        "food": 0.15,
        "local_rental": 0.10,
        "buffer": 0.05,
    },
    "city": {
        "stay": 0.30,
        "transport": 0.20,
        "food": 0.30,
        "local_rental": 0.15,
        "buffer": 0.05,
    },
    "adventure": {
        "stay": 0.30,
        "transport": 0.25,
        "food": 0.15,
        "local_rental": 0.25,
        "buffer": 0.05,
    },
    "relaxed": {
        "stay": 0.40,
        "transport": 0.20,
        "food": 0.25,
        "local_rental": 0.10,
        "buffer": 0.05,
    },
}

# Map vibe to destination type for budget ratios
VIBE_TO_DEST_TYPE = {
    "beach": "beach",
    "mountain": "mountain",
    "city": "city",
    "adventure": "adventure",
    "relaxed": "relaxed",
    "goa": "beach",
    "kerala": "beach",
    "manali": "mountain",
    "himachal": "mountain",
    "delhi": "city",
    "mumbai": "city",
    "rajasthan": "city",
}


async def parse_and_allocate_budget(state: TravelAgentState) -> TravelAgentState:
    """
    LangGraph node: Parse the user's raw query into a structured trip plan,
    then allocate the budget across categories.
    """
    state.current_stage = "parsing_request"
    state.stage_logs.append("🔍 Parsing your trip request...")

    prompt = f"""
Parse the following Indian travel trip request and extract structured information.

Trip Request: "{state.raw_query}"

Return a JSON object with these fields:
{{
  "origin": "city/state they are travelling from (e.g. Mumbai, Delhi). Use 'Not specified' if unclear",
  "destination": "primary destination (e.g. Goa, Manali, Kerala, Rajasthan)",
  "budget_total": <total budget in INR as a number, e.g. 30000>,
  "duration_days": <number of days as integer>,
  "traveler_count": <number of travelers as integer, default 1>,
  "vibe": "one of: beach | mountain | city | adventure | relaxed",
  "travel_dates": "travel dates if mentioned, else null"
}}

Rules:
- If budget is mentioned in 'k' (e.g. 30k), convert to full number (30000)
- If budget is in lakhs, convert accordingly
- Infer vibe from destination if not explicitly stated
- Goa → beach, Manali/Himachal/Ladakh → mountain, Delhi/Mumbai/Jaipur → city
- Default duration: 5 days, default travelers: 1
"""

    try:
        parsed_data = await gemini_generate_json(prompt)
        parsed_trip = ParsedTrip(**parsed_data)
        state.parsed_trip = parsed_trip
        state.stage_logs.append(
            f"✅ Parsed: {parsed_trip.destination} | "
            f"₹{parsed_trip.budget_total:,.0f} | "
            f"{parsed_trip.duration_days} days | "
            f"{parsed_trip.traveler_count} traveler(s)"
        )
    except Exception as e:
        state.error = f"Failed to parse trip: {str(e)}"
        state.stage_logs.append(f"❌ Parse error: {str(e)}")
        # Set defaults
        state.parsed_trip = ParsedTrip(
            destination="Goa",
            budget_total=30000,
            duration_days=5,
            traveler_count=1,
            vibe="beach",
        )

    # Allocate budget
    state.current_stage = "allocating_budget"
    state.stage_logs.append("💰 Allocating budget across categories...")

    trip = state.parsed_trip
    vibe = trip.vibe.lower()
    dest_lower = trip.destination.lower()

    # Determine destination type
    dest_type = VIBE_TO_DEST_TYPE.get(vibe, VIBE_TO_DEST_TYPE.get(dest_lower, "relaxed"))
    ratios = BUDGET_RATIOS.get(dest_type, BUDGET_RATIOS["relaxed"])

    budget = trip.budget_total
    allocation = BudgetAllocation(
        stay=round(budget * ratios["stay"]),
        transport=round(budget * ratios["transport"]),
        food=round(budget * ratios["food"]),
        local_rental=round(budget * ratios["local_rental"]),
        buffer=round(budget * ratios["buffer"]),
        destination_type=dest_type,
    )
    state.budget_allocation = allocation
    state.stage_logs.append(
        f"✅ Budget split — Stay: ₹{allocation.stay:,.0f} | "
        f"Transport: ₹{allocation.transport:,.0f} | "
        f"Food: ₹{allocation.food:,.0f} | "
        f"Rentals: ₹{allocation.local_rental:,.0f}"
    )

    return state
