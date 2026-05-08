"""
Google Maps Service — Places, Geocoding, Distance Matrix.
All calls are async-friendly wrappers around the REST APIs.
"""
from __future__ import annotations
import logging
import os
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

_PLACES_URL      = "https://maps.googleapis.com/maps/api/place/textsearch/json"
_GEOCODE_URL     = "https://maps.googleapis.com/maps/api/geocode/json"
_DISTANCE_URL    = "https://maps.googleapis.com/maps/api/distancematrix/json"
_PHOTO_BASE_URL  = "https://maps.googleapis.com/maps/api/place/photo"

TIMEOUT = httpx.Timeout(10.0, connect=5.0)


def _api_key() -> str:
    key = os.getenv("GOOGLE_MAPS_API_KEY", "")
    if not key or key == "your_google_maps_api_key_here":
        raise EnvironmentError(
            "GOOGLE_MAPS_API_KEY is not configured. Set it in your .env file."
        )
    return key


def geocode_destination(destination: str) -> Optional[Dict[str, Any]]:
    """Convert a destination string to lat/lng coordinates."""
    try:
        resp = httpx.get(
            _GEOCODE_URL,
            params={"address": destination, "key": _api_key()},
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") == "OK" and data.get("results"):
            result = data["results"][0]
            return {
                "formatted_address": result.get("formatted_address"),
                "lat": result["geometry"]["location"]["lat"],
                "lng": result["geometry"]["location"]["lng"],
                "place_id": result.get("place_id"),
            }
    except EnvironmentError:
        raise
    except Exception as exc:
        logger.warning(f"Geocoding failed for '{destination}': {exc}")
    return None


def search_nearby_places(
    destination: str,
    place_type: str = "tourist_attraction",
    max_results: int = 10,
) -> List[Dict[str, Any]]:
    """Search for places near a destination using Places Text Search."""
    try:
        query = f"{place_type} in {destination}"
        resp = httpx.get(
            _PLACES_URL,
            params={"query": query, "key": _api_key()},
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()

        places: List[Dict[str, Any]] = []
        for place in data.get("results", [])[:max_results]:
            photo_ref = None
            if place.get("photos"):
                photo_ref = place["photos"][0].get("photo_reference")

            places.append({
                "name": place.get("name"),
                "address": place.get("formatted_address", ""),
                "rating": place.get("rating"),
                "user_ratings_total": place.get("user_ratings_total"),
                "types": place.get("types", []),
                "price_level": place.get("price_level"),
                "business_status": place.get("business_status"),
                "lat": place.get("geometry", {}).get("location", {}).get("lat"),
                "lng": place.get("geometry", {}).get("location", {}).get("lng"),
                "place_id": place.get("place_id"),
                "photo_url": (
                    f"{_PHOTO_BASE_URL}?maxwidth=400"
                    f"&photo_reference={photo_ref}&key={_api_key()}"
                    if photo_ref else None
                ),
            })
        return places

    except EnvironmentError:
        raise
    except Exception as exc:
        logger.warning(f"Places search failed: {exc}")
        return []


def get_distances(
    origin: str, destinations: List[str]
) -> Optional[Dict[str, Any]]:
    """Get travel distances and durations from origin to multiple destinations."""
    if not destinations:
        return None
    try:
        resp = httpx.get(
            _DISTANCE_URL,
            params={
                "origins": origin,
                "destinations": "|".join(destinations),
                "key": _api_key(),
                "mode": "driving",
                "units": "metric",
            },
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") == "OK":
            rows = data.get("rows", [])
            if rows:
                return {
                    "origin": origin,
                    "destinations": destinations,
                    "elements": [
                        {
                            "destination": dest,
                            "distance": elem.get("distance", {}).get("text"),
                            "duration": elem.get("duration", {}).get("text"),
                            "status": elem.get("status"),
                        }
                        for dest, elem in zip(
                            destinations, rows[0].get("elements", [])
                        )
                    ],
                }
    except EnvironmentError:
        raise
    except Exception as exc:
        logger.warning(f"Distance Matrix failed: {exc}")
    return None


def get_nearby_restaurants(
    destination: str, max_results: int = 8
) -> List[Dict[str, Any]]:
    """Specialised search for restaurants."""
    return search_nearby_places(destination, "restaurant", max_results)


def get_nearby_hotels(
    destination: str, max_results: int = 6
) -> List[Dict[str, Any]]:
    """Specialised search for hotels."""
    return search_nearby_places(destination, "hotel", max_results)
