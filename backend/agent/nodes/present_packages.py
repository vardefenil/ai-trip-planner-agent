"""
Stage 4: Present 5 packages + handle user modify/confirm loop.
"""
from agent.state import TravelAgentState
from agent.tools.gemini_client import gemini_generate_json


async def present_packages(state: TravelAgentState) -> TravelAgentState:
    """
    LangGraph node: Presents the 5 packages (pass-through with possible modifications).
    If a user modification request is present, re-rank and adjust packages.
    """
    state.current_stage = "presenting_packages"
    state.stage_logs.append("📦 Finalising trip packages...")

    packages = state.ranked_packages

    if not packages:
        state.stage_logs.append("⚠️ No packages to present.")
        state.presented_packages = []
        return state

    # If user has requested a modification
    if state.user_modification_request and state.modification_count < 3:
        state.stage_logs.append(
            f"🔄 Applying modification: '{state.user_modification_request}'"
        )
        packages = await _apply_modification(state)
        state.modification_count += 1
        state.user_modification_request = None  # Clear after applying

    state.presented_packages = packages
    state.stage_logs.append(f"✅ Ready to show {len(packages)} packages")
    return state


async def _apply_modification(state: TravelAgentState) -> list:
    """
    Ask Gemini to modify the packages based on user feedback.
    E.g., "make it cheaper", "more adventure", "remove rentals"
    """
    trip = state.parsed_trip
    budget = state.budget_allocation
    mod_request = state.user_modification_request

    packages_summary = []
    for pkg in state.ranked_packages[:5]:
        packages_summary.append({
            "id": pkg.package_id,
            "title": pkg.title,
            "tier": pkg.tier,
            "total_cost": pkg.total_cost,
            "stay": pkg.stay.name,
            "transport": pkg.transport.provider,
        })

    prompt = f"""
A user has reviewed 5 trip packages for {trip.destination if trip else 'their destination'} and requested the following modification:
"{mod_request}"

Current packages:
{packages_summary}

User's total budget: ₹{trip.budget_total if trip else 30000:,.0f}

Based on the modification request, adjust the packages. For example:
- "cheaper" → reduce costs, pick budget stays/transport
- "more premium" → upgrade stays
- "no rental" → remove bike/scooter rentals
- "more days" → extend duration (if they provide new day count)
- "different destination" → note that destination change requires replanning

Return a JSON object:
{{
  "action": "modify | replan | confirm",
  "adjustments": "Brief description of what you changed",
  "modified_ids": [list of package IDs that should be adjusted],
  "budget_change": <new total budget if applicable, else null>,
  "new_duration": <new duration in days if applicable, else null>
}}

If the request is to confirm/book a specific package, set action to "confirm" and note which package.
"""
    try:
        result = await gemini_generate_json(prompt)
        # For now, just re-sort/filter based on action
        action = result.get("action", "modify")
        if action == "confirm":
            return state.ranked_packages

        # Simple adjustments: sort by cost direction
        mod_lower = (mod_request or "").lower()
        packages = list(state.ranked_packages)
        if any(w in mod_lower for w in ["cheap", "budget", "less", "affordable", "save"]):
            packages.sort(key=lambda p: p.total_cost)
        elif any(w in mod_lower for w in ["premium", "luxury", "best", "upgrade"]):
            packages.sort(key=lambda p: p.total_cost, reverse=True)

        return packages
    except Exception:
        return state.ranked_packages
