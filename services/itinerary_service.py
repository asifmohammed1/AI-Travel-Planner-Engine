"""
Itinerary Service — orchestrates all sub-services and returns a complete plan.
No database — pure in-memory operation.
"""
from __future__ import annotations
import logging
from datetime import datetime
from typing import Any, Dict, List

from schemas import TripPlanResponse, TripRequest
from services import gemini_service, maps_service, weather_service, budget_service

logger = logging.getLogger(__name__)


def create_trip_plan(request: TripRequest) -> TripPlanResponse:
    """
    Full orchestration pipeline:
      1. Call Gemini for AI travel plan
      2. Fetch real weather data (Open-Meteo, free)
      3. Fetch nearby places via Google Maps API
      4. Validate & enrich budget breakdown
      5. Return assembled response
    """
    destination = request.destination
    logger.info(f"Planning trip to {destination} for {request.days} days")

    # --- Step 1: AI-generated itinerary ---
    ai_plan = gemini_service.generate_itinerary(
        destination=destination,
        days=request.days,
        budget=request.budget,
        travelers=request.travelers,
        interests=request.interests,
    )

    # --- Step 2: Weather (non-blocking fallback) ---
    weather = weather_service.get_weather_info(destination)
    if not weather:
        weather = ai_plan.get("weather_info")

    # --- Step 3: Nearby places via Maps (non-blocking) ---
    nearby: List[Dict[str, Any]] = []
    try:
        nearby = maps_service.search_nearby_places(
            destination, "tourist_attraction", max_results=8
        )
    except EnvironmentError:
        logger.info("Maps API key not configured — skipping nearby places.")
    except Exception as exc:
        logger.warning(f"Maps search error: {exc}")

    # --- Step 4: Budget validation ---
    budget_breakdown = budget_service.validate_and_enrich_breakdown(
        ai_breakdown=ai_plan.get("budget_breakdown", {}),
        total_budget=request.budget,
        days=request.days,
        travelers=request.travelers,
    )

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
