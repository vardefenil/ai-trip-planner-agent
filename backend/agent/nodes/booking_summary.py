"""
Stage 5: Booking Summary — deep-links and confirmation.
"""
from agent.state import TravelAgentState, BookingSummary as BookingSummaryModel, TripPackage, BookingLink
from agent.tools.gemini_client import gemini_generate


async def generate_booking_summary(state: TravelAgentState) -> TravelAgentState:
    """
    LangGraph node: Generate booking summary with deep-links for the selected/first package.
    """
    state.current_stage = "booking_summary"
    state.stage_logs.append("🎉 Generating booking summary...")

    packages = state.presented_packages or state.ranked_packages
    if not packages:
        state.stage_logs.append("⚠️ No packages to summarise.")
        return state

    # Use the first (highest-ranked / user-selected) package
    selected = packages[0]
    trip = state.parsed_trip

    # Generate confirmation message with Gemini
    prompt = f"""
Generate an enthusiastic, warm booking confirmation message for this trip:
- Destination: {trip.destination if trip else 'destination'}
- Package: {selected.title}
- Stay: {selected.stay.name}
- Transport: {selected.transport.provider} ({selected.transport.mode})
- Duration: {trip.duration_days if trip else 5} days
- Total Cost: ₹{selected.total_cost:,.0f}
- Travellers: {trip.traveler_count if trip else 1}

Write 2-3 sentences that:
1. Congratulate the user on a great choice
2. Highlight the best aspect of this package
3. Wish them an amazing trip

Keep it warm, conversational, and Indian in tone. Mention the destination name.
"""
    try:
        confirmation_msg = await gemini_generate(prompt)
    except Exception:
        confirmation_msg = (
            f"🎉 Fantastic choice! Your {selected.title} to {trip.destination if trip else 'your destination'} "
            f"is all set. {selected.why_this_one} Have an amazing trip! 🌟"
        )

    # Build booking links
    booking_links = _build_booking_links(selected, trip)

    # Travel tips
    tips = _get_travel_tips(trip.destination if trip else "India", trip.vibe if trip else "relaxed")

    summary = BookingSummaryModel(
        selected_package=selected,
        confirmation_message=confirmation_msg,
        booking_links=booking_links,
        tips=tips,
    )
    state.booking_summary = summary
    state.stage_logs.append("✅ Booking summary generated with deep-links")
    return state


def _build_booking_links(pkg: TripPackage, trip) -> list[BookingLink]:
    """Build all booking deep-links for the package."""
    links = []
    destination = trip.destination if trip else "Goa"
    checkin = trip.travel_dates or "2025-01-15"
    adults = trip.traveler_count if trip else 1

    # Hotel booking
    links.append(BookingLink(
        label=f"Book {pkg.stay.name}",
        url=pkg.stay.booking_url or f"https://www.booking.com/searchresults.html?ss={destination}&group_adults={adults}",
        provider="Booking.com",
    ))

    # Alternate hotel search
    dest_slug = destination.lower().replace(" ", "-")
    links.append(BookingLink(
        label=f"Search Hotels in {destination} on MakeMyTrip",
        url=f"https://www.makemytrip.com/hotels/{dest_slug}-hotels.html",
        provider="MakeMyTrip",
    ))

    # Transport booking
    if pkg.transport.mode == "train":
        links.append(BookingLink(
            label=f"Book {pkg.transport.provider} on IRCTC",
            url=pkg.transport.booking_url or "https://www.irctc.co.in/nget/train-search",
            provider="IRCTC",
        ))
        links.append(BookingLink(
            label="Check train availability on RailYatri",
            url=f"https://www.railyatri.in/trains-between-stations",
            provider="RailYatri",
        ))
    elif pkg.transport.mode == "flight":
        links.append(BookingLink(
            label=f"Book flights to {destination}",
            url=pkg.transport.booking_url or f"https://www.makemytrip.com/flights/",
            provider="MakeMyTrip Flights",
        ))
        links.append(BookingLink(
            label="Compare flight prices on Skyscanner",
            url=f"https://www.skyscanner.co.in/flights/{destination.upper()[:3]}",
            provider="Skyscanner",
        ))
    elif pkg.transport.mode == "bus":
        links.append(BookingLink(
            label="Book bus tickets on RedBus",
            url=pkg.transport.booking_url or "https://www.redbus.in",
            provider="RedBus",
        ))

    # Local rental
    if pkg.rental:
        links.append(BookingLink(
            label=f"Find {pkg.rental.name} on Google Maps",
            url=pkg.rental.maps_url or f"https://www.google.com/maps/search/bike+rental+{destination}",
            provider="Google Maps",
        ))

    # Activity
    links.append(BookingLink(
        label=f"Explore activities in {destination}",
        url=f"https://www.tripadvisor.in/Attractions-g{destination.lower()}.html",
        provider="TripAdvisor",
    ))

    return links


def _get_travel_tips(destination: str, vibe: str) -> list[str]:
    """Return destination and vibe-specific travel tips."""
    dest_lower = destination.lower()
    tips = []

    # Generic tips
    tips.extend([
        "📋 Book hotels and trains at least 2-4 weeks in advance, especially during peak season.",
        "💳 Carry both cash and cards — some local vendors in tourist areas only accept cash.",
        "🌐 Download Google Maps offline for the destination area before you go.",
        "📱 Save important numbers: local police (100), ambulance (108), tourist helpline (1363).",
    ])

    # Destination-specific
    if "goa" in dest_lower:
        tips.extend([
            "🏖️ Best beaches: Palolem (south, peaceful), Anjuna (north, party scene), Arambol (hippie vibe).",
            "🛵 Renting a scooter is the best way to explore Goa. Activa costs ₹300-400/day.",
            "🐟 Must-try food: Fish curry rice, Prawn balchão, Bebinca dessert.",
            "☀️ Avoid peak summer (May-June) — stick to Oct-March for best weather.",
        ])
    elif "manali" in dest_lower or "himachal" in dest_lower:
        tips.extend([
            "🧥 Pack warm layers even in summer — temperatures drop sharply at night.",
            "🏔️ Rohtang Pass requires a permit — book online at himachalpr.gov.in.",
            "🚗 Road to Spiti/Lahaul can be closed in winter. Check road conditions.",
            "🫁 Acclimatise for 1-2 days before attempting high-altitude activities.",
        ])
    elif "kerala" in dest_lower:
        tips.extend([
            "🚢 Book your houseboat (Alleppey backwaters) at least a week in advance.",
            "🍌 Must try: Kerala sadya (banana leaf meal), appam with stew, puttu-kadala.",
            "🌿 Munnar tea estate visits are best in the morning before clouds roll in.",
            "🌧️ Kerala has two monsoon seasons — June-Aug and Oct-Nov. Plan accordingly.",
        ])
    elif "rajasthan" in dest_lower or "jaipur" in dest_lower:
        tips.extend([
            "🐪 Camel safaris in Jaisalmer — book through a reputable tour operator.",
            "🏰 Heritage hotels (havelis) offer a unique stay experience in Jaipur and Jodhpur.",
            "🌡️ Avoid peak summer (April-June) — temperatures can reach 45°C+.",
            "🛍️ Bargain at local markets — always negotiate the price down by 30-50%.",
        ])

    if vibe == "adventure":
        tips.append("🧗 Adventure activities like paragliding, white-water rafting must be done through certified operators. Check ATOAI certification.")

    return tips[:6]  # Return top 6 tips
