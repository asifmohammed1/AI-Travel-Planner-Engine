"""
Itinerary Service — orchestrates all sub-services and returns a complete plan.
No database — pure in-memory operation.
Weather and Maps API calls run concurrently for maximum efficiency.
"""
from __future__ import annotations
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from schemas import TripPlanResponse, TripRequest
from services import gemini_service, maps_service, weather_service, budget_service

logger = logging.getLogger(__name__)

# Shared thread pool for concurrent I/O-bound service calls
_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="travel-io")


def _fetch_weather(destination: str) -> Optional[Dict[str, Any]]:
    """Fetch weather data — runs concurrently with Maps fetch."""
    try:
        return weather_service.get_weather_info(destination)
    except Exception as exc:
        logger.warning(f"Weather fetch failed: {exc}")
        return None


def _fetch_nearby(destination: str) -> List[Dict[str, Any]]:
    """Fetch nearby places — runs concurrently with Weather fetch."""
    try:
        return maps_service.search_nearby_places(
            destination, "tourist_attraction", max_results=8
        )
    except EnvironmentError:
        logger.info("Maps API key not configured — skipping nearby places.")
        return []
    except Exception as exc:
        logger.warning(f"Maps search error: {exc}")
        return []


def _fetch_parallel(destination: str) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Run weather + Maps requests concurrently using a thread pool.
    Returns (weather_info, nearby_places) tuple.
    Reduces total latency from sum(t1+t2) → max(t1,t2).
    """
    future_weather = _executor.submit(_fetch_weather, destination)
    future_nearby  = _executor.submit(_fetch_nearby, destination)

    weather = None
    nearby: List[Dict[str, Any]] = []

    for future in as_completed([future_weather, future_nearby], timeout=12):
        if future is future_weather:
            weather = future.result()
        else:
            nearby = future.result()

    return weather, nearby


def create_trip_plan(request: TripRequest) -> TripPlanResponse:
    """
    Full orchestration pipeline:
      1. Call Gemini for AI travel plan (blocking — LLM call)
      2. Concurrently fetch weather + nearby places (parallel I/O)
      3. Validate & enrich budget breakdown
      4. Return assembled in-memory response

    Concurrency model: weather & Maps calls run in parallel threads,
    reducing external API wait time significantly.
    """
    destination = request.destination
    logger.info(
        f"Planning trip | destination={destination} days={request.days} "
        f"budget={request.budget} travelers={request.travelers} "
        f"interests={request.interests}"
    )

    # --- Step 1: AI-generated itinerary (Gemini) ---
    ai_plan = gemini_service.generate_itinerary(
        destination=destination,
        days=request.days,
        budget=request.budget,
        travelers=request.travelers,
        interests=request.interests,
    )

    # --- Step 2: Concurrent Weather + Maps fetch ---
    weather, nearby = _fetch_parallel(destination)

    # Fallback to AI-provided weather if external fetch failed
    if not weather:
        weather = ai_plan.get("weather_info")

    # --- Step 3: Budget validation + enrichment ---
    budget_breakdown = budget_service.validate_and_enrich_breakdown(
        ai_breakdown=ai_plan.get("budget_breakdown", {}),
        total_budget=request.budget,
        days=request.days,
        travelers=request.travelers,
    )

    logger.info(f"Trip plan assembled | destination={destination}")

    return TripPlanResponse(
        destination=destination,
        days=request.days,
        budget=request.budget,
        travelers=request.travelers,
        interests=request.interests,
        itinerary=ai_plan.get("itinerary", []),
        attractions=ai_plan.get("attractions", []),
        food_suggestions=ai_plan.get("food_suggestions", []),
        hidden_gems=ai_plan.get("hidden_gems", []),
        travel_tips=ai_plan.get("travel_tips", []),
        budget_breakdown=budget_breakdown,
        weather_info=weather,
        nearby_places=nearby,
        generated_at=datetime.utcnow(),
    )
