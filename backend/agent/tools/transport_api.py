"""
Transport search — covers trains (IRCTC-style), buses, and flights.
Uses mock data for trains/buses (no public API), Amadeus for flights if configured.
"""
import os
import random
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# ────────────────────────────────────────────────────────────
# Mock transport data (trains + buses in India)
# ────────────────────────────────────────────────────────────

TRAIN_DATA = {
    # (origin_keyword, destination_keyword): [options]
    ("mumbai", "goa"): [
        {"name": "Konkan Kanya Express", "number": "10111", "duration": "9h 30m", "base_price": 450},
        {"name": "Mandovi Express", "number": "10103", "duration": "9h 15m", "base_price": 520},
        {"name": "Tejas Express", "number": "22119", "duration": "7h 45m", "base_price": 1200},
    ],
    ("delhi", "goa"): [
        {"name": "Goa Express", "number": "12779", "duration": "26h 00m", "base_price": 850},
        {"name": "Rajdhani Express", "number": "12431", "duration": "24h 30m", "base_price": 2200},
    ],
    ("delhi", "manali"): [
        {"name": "Kalka Shatabdi", "number": "12011", "duration": "4h (+ bus)", "base_price": 650},
        {"name": "Himachal Express", "number": "14553", "duration": "8h (to Ambala)", "base_price": 350},
    ],
    ("mumbai", "kerala"): [
        {"name": "Kerala Express", "number": "12625", "duration": "26h 45m", "base_price": 900},
        {"name": "Netravati Express", "number": "16345", "duration": "25h 30m", "base_price": 750},
    ],
    ("default", "default"): [
        {"name": "Rajdhani Express", "number": "12301", "duration": "16h 00m", "base_price": 1500},
        {"name": "Shatabdi Express", "number": "12001", "duration": "8h 00m", "base_price": 800},
        {"name": "Jan Shatabdi", "number": "12051", "duration": "10h 00m", "base_price": 450},
    ],
}

BUS_DATA = {
    "default": [
        {"name": "Volvo AC Sleeper", "operator": "MSRTC", "duration": "12h", "base_price": 700},
        {"name": "AC Semi-Sleeper", "operator": "RedBus Partner", "duration": "14h", "base_price": 500},
        {"name": "Non-AC Sleeper", "operator": "State Transport", "duration": "15h", "base_price": 300},
    ]
}


def _get_train_options(origin: str, destination: str) -> list[dict]:
    """Match train options from mock data."""
    o = origin.lower()
    d = destination.lower()

    for (ko, kd), trains in TRAIN_DATA.items():
        if ko == "default":
            continue
        if ko in o and kd in d:
            return trains

    return TRAIN_DATA[("default", "default")]


async def search_transport(
    origin: str,
    destination: str,
    budget_transport: float,
    traveler_count: int = 1,
    travel_dates: Optional[str] = None,
) -> list[dict]:
    """
    Search for transport options between origin and destination.
    Returns a list of transport option dicts.
    """
    options = []

    # --- Train options ---
    trains = _get_train_options(origin, destination)
    for train in trains[:2]:
        price = train["base_price"] * traveler_count
        options.append({
            "mode": "train",
            "provider": train["name"],
            "train_number": train.get("number", ""),
            "from_city": origin,
            "to_city": destination,
            "price_per_person": train["base_price"],
            "total_cost": price,
            "duration": train["duration"],
            "booking_url": (
                f"https://www.irctc.co.in/nget/train-search"
                f"?from={origin.upper()[:3]}&to={destination.upper()[:3]}"
            ),
            "departure_time": f"{random.randint(5, 22):02d}:{random.choice(['00', '15', '30', '45'])}",
        })

    # --- Bus options ---
    buses = BUS_DATA["default"]
    for bus in buses[:1]:
        price = bus["base_price"] * traveler_count
        options.append({
            "mode": "bus",
            "provider": f"{bus['name']} — {bus['operator']}",
            "from_city": origin,
            "to_city": destination,
            "price_per_person": bus["base_price"],
            "total_cost": price,
            "duration": bus["duration"],
            "booking_url": (
                f"https://www.redbus.in/bus-tickets/{origin.lower().replace(' ', '-')}-to-"
                f"{destination.lower().replace(' ', '-')}"
            ),
            "departure_time": f"{random.randint(18, 23):02d}:00",
        })

    # --- Flight (Amadeus or MakeMyTrip fallback) ---
    amadeus_key = os.getenv("AMADEUS_API_KEY")
    if amadeus_key:
        flight_options = await _search_amadeus_flights(origin, destination, traveler_count, travel_dates)
        options.extend(flight_options)
    else:
        # Mock flight
        flight_price = int(budget_transport * 0.8)
        options.append({
            "mode": "flight",
            "provider": "IndiGo / Air India",
            "from_city": origin,
            "to_city": destination,
            "price_per_person": flight_price // traveler_count,
            "total_cost": flight_price,
            "duration": f"{random.randint(1, 3)}h {random.choice(['00', '15', '30', '45'])}m",
            "booking_url": (
                f"https://www.makemytrip.com/flight/search?itinerary="
                f"{origin.upper()[:3]}-{destination.upper()[:3]}-{travel_dates or 'anytime'}"
                f"&tripType=O&paxType=A-{traveler_count}_C-0_I-0"
            ),
            "departure_time": f"{random.randint(6, 20):02d}:00",
        })

    return options


async def _search_amadeus_flights(
    origin: str,
    destination: str,
    traveler_count: int,
    travel_dates: Optional[str],
) -> list[dict]:
    """Real Amadeus flight search (if API key available)."""
    try:
        import httpx
        amadeus_key = os.getenv("AMADEUS_API_KEY")
        amadeus_secret = os.getenv("AMADEUS_API_SECRET")

        # Get access token
        async with httpx.AsyncClient() as client:
            token_resp = await client.post(
                "https://test.api.amadeus.com/v1/security/oauth2/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": amadeus_key,
                    "client_secret": amadeus_secret,
                },
            )
            token = token_resp.json().get("access_token")
            if not token:
                return []

            # IATA codes (simplified mapping for Indian cities)
            iata_map = {
                "goa": "GOI", "mumbai": "BOM", "delhi": "DEL",
                "bangalore": "BLR", "bengaluru": "BLR", "chennai": "MAA",
                "kolkata": "CCU", "hyderabad": "HYD", "kochi": "COK",
                "jaipur": "JAI", "ahmedabad": "AMD", "pune": "PNQ",
            }
            origin_code = iata_map.get(origin.lower(), origin.upper()[:3])
            dest_code = iata_map.get(destination.lower(), destination.upper()[:3])
            date = travel_dates or "2025-01-15"

            resp = await client.get(
                "https://test.api.amadeus.com/v2/shopping/flight-offers",
                headers={"Authorization": f"Bearer {token}"},
                params={
                    "originLocationCode": origin_code,
                    "destinationLocationCode": dest_code,
                    "departureDate": date,
                    "adults": traveler_count,
                    "currencyCode": "INR",
                    "max": 3,
                },
            )
            offers = resp.json().get("data", [])

        results = []
        for offer in offers[:2]:
            price = float(offer["price"]["total"])
            itinerary = offer["itineraries"][0]
            segment = itinerary["segments"][0]
            results.append({
                "mode": "flight",
                "provider": segment["carrierCode"],
                "from_city": origin,
                "to_city": destination,
                "price_per_person": price / traveler_count,
                "total_cost": price,
                "duration": itinerary["duration"].replace("PT", "").lower(),
                "booking_url": f"https://www.makemytrip.com/flight/search",
                "departure_time": segment["departure"]["at"][11:16],
            })
        return results

    except Exception:
        return []
