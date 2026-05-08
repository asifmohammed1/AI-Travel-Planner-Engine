"""
Gemini AI Service — generates all travel intelligence.
Uses google-generativeai SDK with structured JSON prompting.
"""
from __future__ import annotations
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

_GEMINI_MODEL = "gemini-1.5-flash"


def _get_client() -> genai.GenerativeModel:
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key or api_key == "your_gemini_api_key_here":
        raise EnvironmentError(
            "GEMINI_API_KEY is not configured. "
            "Set it in your .env file."
        )
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(_GEMINI_MODEL)


def _extract_json(text: str) -> Any:
    """Robustly extract a JSON object or array from model output."""
    # Strip markdown code fences if present
    text = re.sub(r"```(?:json)?", "", text).strip().rstrip("```").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find first JSON structure
        match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        raise ValueError(f"Cannot parse JSON from model response: {text[:200]}")


def generate_itinerary(
    destination: str,
    days: int,
    budget: float,
    travelers: int,
    interests: List[str],
) -> Dict[str, Any]:
    """
    Call Gemini to generate a complete, structured travel plan.

    Returns a dict with keys:
      itinerary, attractions, food_suggestions, hidden_gems,
      travel_tips, budget_breakdown, weather_info
    """
    interests_str = ", ".join(interests)
    budget_per_person = budget / travelers

    prompt = f"""
You are an expert AI travel planner. Generate a comprehensive travel plan in strict JSON.

Trip Details:
- Destination: {destination}
- Duration: {days} days
- Total Budget: ${budget} USD
- Travelers: {travelers} people
- Budget per person: ${budget_per_person:.0f}
- Interests: {interests_str}

Return ONLY valid JSON (no markdown, no explanation) matching this exact schema:
{{
  "itinerary": [
    {{
      "day": 1,
      "theme": "string – theme for the day",
      "activities": [
        {{
          "time": "9:00 AM",
          "activity": "string",
          "location": "string",
          "estimated_cost": 0.0,
          "tips": "string"
        }}
      ],
      "meals": ["Breakfast: ...", "Lunch: ...", "Dinner: ..."]
    }}
  ],
  "attractions": [
    {{
      "name": "string",
      "description": "string",
      "category": "string",
      "estimated_cost": 0.0,
      "rating": 4.5
    }}
  ],
  "food_suggestions": [
    {{
      "name": "string",
      "cuisine_type": "string",
      "description": "string",
      "price_range": "$10-$20",
      "must_try": "string"
    }}
  ],
  "hidden_gems": [
    {{
      "name": "string",
      "description": "string",
      "why_special": "string",
      "best_time_to_visit": "string"
    }}
  ],
  "travel_tips": ["tip1", "tip2", "tip3", "tip4", "tip5"],
  "budget_breakdown": {{
    "accommodation": 0.0,
    "food": 0.0,
    "transportation": 0.0,
    "activities": 0.0,
    "shopping": 0.0,
    "emergency": 0.0,
    "total": {budget},
    "per_person": {budget_per_person:.2f},
    "currency": "USD"
  }},
  "weather_info": {{
    "temperature_range": "string",
    "condition": "string",
    "best_time": "string",
    "packing_suggestions": ["item1", "item2", "item3"]
  }}
}}

Rules:
- Include exactly {days} day objects in itinerary.
- Each day must have at least 4 activities.
- Include at least 6 attractions, 5 food suggestions, 4 hidden gems, 5 travel tips.
- Budget breakdown must sum to exactly {budget}.
- Tailor everything to the interests: {interests_str}.
- Be specific, realistic, and locally authentic.
"""

    try:
        model = _get_client()
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=8192,
            ),
        )
        return _extract_json(response.text)
    except EnvironmentError:
        raise
    except Exception as exc:
        logger.error(f"Gemini generation failed: {exc}")
        return _fallback_plan(destination, days, budget, travelers, interests)


def _fallback_plan(
    destination: str,
    days: int,
    budget: float,
    travelers: int,
    interests: List[str],
) -> Dict[str, Any]:
    """Return a deterministic mock plan when Gemini is unavailable (dev mode)."""
    logger.warning("Using fallback travel plan (Gemini API not available).")
    accom = round(budget * 0.40, 2)
    food = round(budget * 0.25, 2)
    transport = round(budget * 0.15, 2)
    activities = round(budget * 0.12, 2)
    shopping = round(budget * 0.05, 2)
    emergency = round(budget - accom - food - transport - activities - shopping, 2)

    itinerary = []
    for d in range(1, days + 1):
        itinerary.append({
            "day": d,
            "theme": f"Day {d} – Explore {destination}",
            "activities": [
                {"time": "9:00 AM",  "activity": "Morning city walk",         "location": f"{destination} city center", "estimated_cost": 0,   "tips": "Start early to beat crowds."},
                {"time": "11:00 AM", "activity": "Visit main landmark",        "location": f"{destination} landmark",    "estimated_cost": 15,  "tips": "Book tickets online."},
                {"time": "1:00 PM",  "activity": "Local lunch",                "location": "Local restaurant",           "estimated_cost": 20,  "tips": "Try the local specialty."},
                {"time": "3:00 PM",  "activity": "Cultural museum",            "location": f"{destination} museum",      "estimated_cost": 10,  "tips": "Audio guide recommended."},
                {"time": "6:00 PM",  "activity": "Sunset viewpoint",           "location": "Scenic overlook",            "estimated_cost": 0,   "tips": "Arrive 30 min early."},
                {"time": "8:00 PM",  "activity": "Dinner at local eatery",     "location": "Old town district",          "estimated_cost": 30,  "tips": "Make a reservation."},
            ],
            "meals": ["Breakfast: Hotel breakfast or local café", "Lunch: Local cuisine restaurant", "Dinner: Traditional dining experience"],
        })

    return {
        "itinerary": itinerary,
        "attractions": [
            {"name": f"{destination} Historic District",  "description": "A charming area with rich history and architecture.", "category": "Culture",     "estimated_cost": 0,  "rating": 4.7},
            {"name": f"{destination} Central Museum",     "description": "World-class exhibits on local history and art.",      "category": "Museum",      "estimated_cost": 15, "rating": 4.5},
            {"name": f"{destination} Nature Park",        "description": "Stunning natural landscapes perfect for hiking.",     "category": "Nature",      "estimated_cost": 5,  "rating": 4.8},
            {"name": f"{destination} Food Market",        "description": "Vibrant market with street food and local produce.",  "category": "Food",        "estimated_cost": 20, "rating": 4.6},
            {"name": f"{destination} Art Gallery",        "description": "Contemporary and classical art in stunning setting.", "category": "Art",         "estimated_cost": 10, "rating": 4.4},
            {"name": f"{destination} Harbor/Waterfront",  "description": "Beautiful waterfront promenade with amazing views.",  "category": "Sightseeing", "estimated_cost": 0,  "rating": 4.9},
        ],
        "food_suggestions": [
            {"name": "Traditional Local Dish",    "cuisine_type": "Local",        "description": f"The signature dish of {destination}.",    "price_range": "$10-$20", "must_try": "Best paired with local beverage."},
            {"name": "Street Food Tour",          "cuisine_type": "Street Food",  "description": "Sample a variety of local street snacks.",   "price_range": "$5-$15",  "must_try": "Try the grilled skewers."},
            {"name": "Fine Dining Experience",    "cuisine_type": "Fusion",       "description": "Upscale restaurant with modern twists.",      "price_range": "$50-$100","must_try": "Tasting menu is worth it."},
            {"name": "Local Breakfast Café",      "cuisine_type": "Café",         "description": "Cozy café with authentic morning flavors.",   "price_range": "$5-$12",  "must_try": "Fresh-baked pastries."},
            {"name": "Seafood / Regional Staple", "cuisine_type": "Regional",     "description": "Must-try regional specialty.",               "price_range": "$15-$30", "must_try": "Order the catch of the day."},
        ],
        "hidden_gems": [
            {"name": "Secret Garden",       "description": "A tucked-away garden unknown to most tourists.",    "why_special": "Tranquil atmosphere and rare plants.",          "best_time_to_visit": "Morning"},
            {"name": "Local Artisan Market","description": "Small market run by local craftspeople.",           "why_special": "Authentic souvenirs and local art.",            "best_time_to_visit": "Weekends"},
            {"name": "Rooftop Café",        "description": "Hidden café with panoramic city views.",           "why_special": "Best views in the city, few tourists know it.", "best_time_to_visit": "Sunset"},
            {"name": "Underground Tour",    "description": "Explore the historic underground passages.",        "why_special": "Unique historical experience.",                 "best_time_to_visit": "Afternoon"},
        ],
        "travel_tips": [
            "Book popular attractions in advance to avoid long queues.",
            f"Use public transportation in {destination} — it's efficient and affordable.",
            "Carry a reusable water bottle and stay hydrated.",
            "Learn a few phrases in the local language — locals appreciate it.",
            "Keep digital and physical copies of all important documents.",
            "Exchange some currency locally for better rates at small shops.",
        ],
        "budget_breakdown": {
            "accommodation": accom,
            "food": food,
            "transportation": transport,
            "activities": activities,
            "shopping": shopping,
            "emergency": emergency,
            "total": budget,
            "per_person": round(budget / travelers, 2),
            "currency": "USD",
        },
        "weather_info": {
            "temperature_range": "18°C – 28°C (64°F – 82°F)",
            "condition": "Partly cloudy with occasional sunshine",
            "best_time": "Spring (March–May) and Autumn (Sept–Nov)",
            "packing_suggestions": [
                "Light layers for temperature changes",
                "Comfortable walking shoes",
                "Rain jacket or compact umbrella",
                "Sunscreen and sunglasses",
            ],
        },
    }
