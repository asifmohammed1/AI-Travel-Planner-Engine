"""
SQLAlchemy ORM models for the Travel Planner Engine.
"""
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Text, DateTime, JSON, ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class TripPlan(Base):
    """Stores a complete AI-generated trip plan."""

    __tablename__ = "trip_plans"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    destination = Column(String(255), nullable=False, index=True)
    days = Column(Integer, nullable=False)
    budget = Column(Float, nullable=False)
    travelers = Column(Integer, nullable=False, default=1)
    interests = Column(JSON, nullable=False, default=list)  # list of strings

    # AI-generated content (stored as JSON blobs)
    itinerary = Column(JSON, nullable=True)          # day-wise plan
    attractions = Column(JSON, nullable=True)        # recommended spots
    food_suggestions = Column(JSON, nullable=True)   # local food
    hidden_gems = Column(JSON, nullable=True)        # off-beaten-path places
    travel_tips = Column(JSON, nullable=True)        # practical tips
    budget_breakdown = Column(JSON, nullable=True)   # cost allocation

    # External data
    weather_info = Column(JSON, nullable=True)       # weather snapshot
    nearby_places = Column(JSON, nullable=True)      # Maps Places API result

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<TripPlan id={self.id} destination={self.destination}>"
