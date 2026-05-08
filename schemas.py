"""
Pydantic schemas for request validation and response serialization.
No database dependency — pure in-memory models.
"""
from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_INTERESTS = {
    "culture", "adventure", "food", "nature", "history",
    "shopping", "nightlife", "art", "wellness", "photography",
    "beaches", "mountains", "family", "budget", "luxury",
}


# ---------------------------------------------------------------------------
# Request Schemas
# ---------------------------------------------------------------------------

class TripRequest(BaseModel):
    """Validated input for trip planning."""

    destination: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="City or country to visit",
        examples=["Paris, France"],
    )
    days: int = Field(..., ge=1, le=30, description="Duration in days")
    budget: float = Field(..., gt=0, le=1_000_000, description="Total budget in USD")
    travelers: int = Field(default=1, ge=1, le=50, description="Number of travelers")
    interests: List[str] = Field(
        default=["culture", "food"],
        min_length=1,
        max_length=10,
        description="List of interest categories",
    )

    @field_validator("destination")
    @classmethod
    def sanitize_destination(cls, v: str) -> str:
        return v.strip().title()

    @field_validator("interests")
    @classmethod
    def validate_interests(cls, v: List[str]) -> List[str]:
        normalized = [i.lower().strip() for i in v]
        invalid = set(normalized) - VALID_INTERESTS
        if invalid:
            raise ValueError(
                f"Invalid interests: {invalid}. "
                f"Choose from: {sorted(VALID_INTERESTS)}"
            )
        return normalized

    model_config = {"json_schema_extra": {
        "example": {
            "destination": "Kyoto, Japan",
            "days": 5,
            "budget": 2000,
            "travelers": 2,
            "interests": ["culture", "food", "history"],
        }
    }}


# ---------------------------------------------------------------------------
# Response Schemas
# ---------------------------------------------------------------------------

class TripPlanResponse(BaseModel):
    """Full trip plan response — no DB fields."""
    destination: str
    days: int
    budget: float
    travelers: int
    interests: List[str]
    itinerary: List[Dict[str, Any]]
    attractions: List[Dict[str, Any]]
    food_suggestions: List[Dict[str, Any]]
    hidden_gems: List[Dict[str, Any]]
    travel_tips: List[str]
    budget_breakdown: Dict[str, Any]
    weather_info: Optional[Dict[str, Any]] = None
    nearby_places: Optional[List[Dict[str, Any]]] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime


class ErrorResponse(BaseModel):
    detail: str
    code: Optional[str] = None
