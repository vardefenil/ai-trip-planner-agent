"""
Google Places API wrapper for hotel search, rental search, and reviews.
"""
import os
import httpx
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

PLACES_BASE_URL = "https://maps.googleapis.com/maps/api/place"


def get_places_key() -> str:
    key = os.getenv("GOOGLE_PLACES_API_KEY")
    if not key:
        raise ValueError(
            "GOOGLE_PLACES_API_KEY not set. Please add it to your .env file."
        )
    return key


async def text_search_places(
    query: str,
    location: Optional[str] = None,
    radius_meters: int = 10000,
    place_type: Optional[str] = None,
) -> list[dict]:
    """
    Search for places using Google Places Text Search API.
    Returns a list of place dicts.
    """
    key = get_places_key()
    params = {
        "query": query,
        "key": key,
        "language": "en",
    }
    if location:
        params["location"] = location
        params["radius"] = radius_meters
    if place_type:
        params["type"] = place_type

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(f"{PLACES_BASE_URL}/textsearch/json", params=params)
        resp.raise_for_status()
        data = resp.json()

    if data.get("status") not in ("OK", "ZERO_RESULTS"):
        raise RuntimeError(f"Places API error: {data.get('status')} — {data.get('error_message', '')}")

    return data.get("results", [])


async def get_place_details(place_id: str) -> dict:
    """
    Fetch detailed info (reviews, phone, website) for a specific place.
    """
    key = get_places_key()
    params = {
        "place_id": place_id,
        "key": key,
        "fields": "name,rating,formatted_address,formatted_phone_number,website,reviews,photos,price_level,opening_hours,types",
        "language": "en",
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(f"{PLACES_BASE_URL}/details/json", params=params)
        resp.raise_for_status()
        data = resp.json()

    if data.get("status") != "OK":
        return {}

    return data.get("result", {})


async def get_place_photo_url(photo_reference: str, max_width: int = 800) -> str:
    """Returns the URL to fetch a place photo."""
    key = get_places_key()
    return (
        f"{PLACES_BASE_URL}/photo"
        f"?maxwidth={max_width}"
        f"&photoreference={photo_reference}"
        f"&key={key}"
    )


async def search_hotels(destination: str, budget_per_night: float) -> list[dict]:
    """
    Search for hotels/stays in a destination within budget.
    Returns raw Places API results.
    """
    query = f"hotels in {destination} India"
    results = await text_search_places(query, place_type="lodging")
    return results[:10]  # Top 10


async def search_local_rentals(destination: str) -> list[dict]:
    """
    Search for bike/scooter rental shops near a destination.
    """
    # Try bicycle_rental type first
    query = f"bike scooter rental {destination} India"
    results = await text_search_places(query, place_type="bicycle_rental")
    if not results:
        # Fallback: text search
        results = await text_search_places(query)
    return results[:8]


async def search_activities(destination: str, vibe: str) -> list[dict]:
    """Search for activities based on trip vibe."""
    vibe_map = {
        "beach": "beach activities water sports",
        "mountain": "trekking camping adventure sports",
        "city": "museums monuments cultural tours",
        "adventure": "adventure sports zip-lining rappelling",
        "relaxed": "spa wellness ayurveda retreat",
    }
    activity_query = vibe_map.get(vibe, "tourist attractions")
    query = f"{activity_query} {destination} India"
    results = await text_search_places(query, place_type="tourist_attraction")
    if not results:
        results = await text_search_places(query)
    return results[:6]
