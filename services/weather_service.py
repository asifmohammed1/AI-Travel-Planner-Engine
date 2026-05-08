"""
Weather Service — lightweight weather context for travel planning.
Uses Open-Meteo (free, no API key) as primary source.
Falls back to Gemini-provided data if unavailable.
"""
from __future__ import annotations
import logging
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)

_GEOCODE_URL  = "https://geocoding-api.open-meteo.com/v1/search"
_WEATHER_URL  = "https://api.open-meteo.com/v1/forecast"
TIMEOUT = httpx.Timeout(8.0, connect=4.0)

_WMO_DESCRIPTIONS: Dict[int, str] = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Foggy", 48: "Icy fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail",
}


def _geocode(destination: str) -> Optional[Dict[str, float]]:
    try:
        resp = httpx.get(
            _GEOCODE_URL,
            params={"name": destination, "count": 1, "language": "en", "format": "json"},
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        if results:
            return {"lat": results[0]["latitude"], "lng": results[0]["longitude"]}
    except Exception as exc:
        logger.debug(f"Open-Meteo geocode failed: {exc}")
    return None


def get_weather_info(destination: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a 7-day weather forecast summary for the destination.
    Returns None if the service is unreachable.
    """
    coords = _geocode(destination)
    if not coords:
        return None

    try:
        resp = httpx.get(
            _WEATHER_URL,
            params={
                "latitude":  coords["lat"],
                "longitude": coords["lng"],
                "daily":     "temperature_2m_max,temperature_2m_min,weathercode",
                "timezone":  "auto",
                "forecast_days": 7,
            },
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        daily = resp.json().get("daily", {})

        temps_max = daily.get("temperature_2m_max", [])
        temps_min = daily.get("temperature_2m_min", [])
        codes     = daily.get("weathercode", [])

        if not temps_max:
            return None

        avg_max = round(sum(temps_max) / len(temps_max), 1)
        avg_min = round(sum(temps_min) / len(temps_min), 1)
        avg_max_f = round(avg_max * 9 / 5 + 32, 1)
        avg_min_f = round(avg_min * 9 / 5 + 32, 1)

        # Most common weather code
        dominant_code = max(set(codes), key=codes.count) if codes else 0
        condition = _WMO_DESCRIPTIONS.get(dominant_code, "Variable conditions")

        packing = _packing_suggestions(avg_min, avg_max, dominant_code)

        return {
            "temperature_range": f"{avg_min}°C – {avg_max}°C ({avg_min_f}°F – {avg_max_f}°F)",
            "condition": condition,
            "best_time": "Check local seasonal guides for optimal travel windows.",
            "packing_suggestions": packing,
            "forecast_days": 7,
            "source": "Open-Meteo",
        }

    except Exception as exc:
        logger.warning(f"Weather fetch failed for '{destination}': {exc}")
        return None


def _packing_suggestions(min_c: float, max_c: float, code: int) -> list:
    suggestions = []
    if min_c < 10:
        suggestions.append("Warm jacket or coat")
        suggestions.append("Thermal base layers")
    elif min_c < 18:
        suggestions.append("Light jacket or hoodie")
    else:
        suggestions.append("Light breathable clothing")

    if max_c > 28:
        suggestions.extend(["Sunscreen SPF 50+", "Sunglasses and hat"])

    if code in (51, 53, 55, 61, 63, 65, 80, 81, 82):
        suggestions.append("Compact umbrella or rain jacket")

    suggestions.append("Comfortable walking shoes")
    suggestions.append("Power adapter and portable charger")
    return suggestions[:6]
