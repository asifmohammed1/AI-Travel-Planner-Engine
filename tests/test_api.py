"""
Backend API test suite — no database dependency.
Run with: pytest tests/ -v
"""
import os
import sys
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

os.environ.setdefault("GEMINI_API_KEY", "test-key")
os.environ.setdefault("GOOGLE_MAPS_API_KEY", "test-maps-key")

from main import app

client = TestClient(app)

# ─── Fixtures ────────────────────────────────────────────────────────────────
VALID_PAYLOAD = {
    "destination": "Kyoto, Japan",
    "days": 3,
    "budget": 1500.0,
    "travelers": 2,
    "interests": ["culture", "food"],
}

MOCK_AI_PLAN = {
    "itinerary": [
        {
            "day": i,
            "theme": f"Day {i} – Explore Kyoto",
            "activities": [
                {"time": "9:00 AM",  "activity": "Temple visit",  "location": "Fushimi", "estimated_cost": 0,  "tips": "Go early."},
                {"time": "12:00 PM", "activity": "Lunch",         "location": "Gion",    "estimated_cost": 20, "tips": "Try ramen."},
                {"time": "3:00 PM",  "activity": "Museum",        "location": "Downtown","estimated_cost": 10, "tips": None},
                {"time": "7:00 PM",  "activity": "Dinner",        "location": "Nishiki", "estimated_cost": 35, "tips": None},
            ],
            "meals": ["Breakfast: Hotel", "Lunch: Ramen", "Dinner: Kaiseki"],
        }
        for i in range(1, 4)
    ],
    "attractions":      [{"name": "Fushimi Inari", "description": "Iconic shrine", "category": "Culture", "estimated_cost": 0, "rating": 4.9}],
    "food_suggestions": [{"name": "Ramen", "cuisine_type": "Japanese", "description": "Noodle soup", "price_range": "$10-$20", "must_try": "Tonkotsu"}],
    "hidden_gems":      [{"name": "Philosopher's Path", "description": "Canal walk", "why_special": "Quiet beauty", "best_time_to_visit": "Morning"}],
    "travel_tips":      ["Book temples early", "Use IC card for transport"],
    "budget_breakdown": {
        "accommodation": 600, "food": 375, "transportation": 225,
        "activities": 180, "shopping": 75, "emergency": 45,
        "total": 1500, "per_person": 750, "currency": "USD",
    },
    "weather_info": {
        "temperature_range": "15°C – 24°C", "condition": "Partly cloudy",
        "best_time": "Spring", "packing_suggestions": ["Light jacket"],
    },
}


# ─── Health ───────────────────────────────────────────────────────────────────
class TestHealth:
    def test_health_returns_200(self):
        assert client.get("/health").status_code == 200

    def test_health_schema(self):
        data = client.get("/health").json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data


# ─── Frontend ─────────────────────────────────────────────────────────────────
class TestFrontend:
    def test_index_returns_html(self):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]

    def test_static_css(self):
        assert client.get("/static/style.css").status_code == 200

    def test_static_js(self):
        assert client.get("/static/script.js").status_code == 200


# ─── Plan Trip API ─────────────────────────────────────────────────────────────
class TestPlanTripAPI:
    @patch("services.gemini_service.generate_itinerary", return_value=MOCK_AI_PLAN)
    @patch("services.maps_service.search_nearby_places", return_value=[])
    @patch("services.weather_service.get_weather_info", return_value=None)
    def test_success(self, *_):
        resp = client.post("/api/plan-trip", json=VALID_PAYLOAD)
        assert resp.status_code == 200
        data = resp.json()
        assert data["destination"] == "Kyoto, Japan"
        assert data["days"] == 3
        assert "itinerary" in data
        assert "budget_breakdown" in data
        assert "generated_at" in data

    def test_missing_destination(self):
        assert client.post("/api/plan-trip", json={**VALID_PAYLOAD, "destination": ""}).status_code == 422

    def test_days_zero(self):
        assert client.post("/api/plan-trip", json={**VALID_PAYLOAD, "days": 0}).status_code == 422

    def test_days_over_limit(self):
        assert client.post("/api/plan-trip", json={**VALID_PAYLOAD, "days": 31}).status_code == 422

    def test_negative_budget(self):
        assert client.post("/api/plan-trip", json={**VALID_PAYLOAD, "budget": -100}).status_code == 422

    def test_invalid_interest(self):
        assert client.post("/api/plan-trip", json={**VALID_PAYLOAD, "interests": ["gambling"]}).status_code == 422

    def test_empty_interests(self):
        assert client.post("/api/plan-trip", json={**VALID_PAYLOAD, "interests": []}).status_code == 422

    def test_travelers_over_limit(self):
        assert client.post("/api/plan-trip", json={**VALID_PAYLOAD, "travelers": 51}).status_code == 422

    def test_destination_too_long(self):
        assert client.post("/api/plan-trip", json={**VALID_PAYLOAD, "destination": "A" * 101}).status_code == 422


# ─── Budget Service ───────────────────────────────────────────────────────────
class TestBudgetService:
    def test_classify_budget(self):
        from services.budget_service import classify_budget
        assert classify_budget(500, 7, 1) == "budget"
        assert classify_budget(1500, 5, 2) == "mid"
        assert classify_budget(5000, 5, 1) == "luxury"

    def test_breakdown_sums_correctly(self):
        from services.budget_service import compute_budget_breakdown
        bd = compute_budget_breakdown(2000, 5, 2)
        cats = ["accommodation", "food", "transportation", "activities", "shopping", "emergency"]
        assert abs(sum(bd[c] for c in cats) - 2000) < 0.05

    def test_validate_enriches(self):
        from services.budget_service import validate_and_enrich_breakdown
        bd = validate_and_enrich_breakdown(MOCK_AI_PLAN["budget_breakdown"], 1500, 3, 2)
        assert "style" in bd
        assert "per_person_per_day" in bd


# ─── OpenAPI ──────────────────────────────────────────────────────────────────
class TestOpenAPI:
    def test_schema_accessible(self):
        resp = client.get("/api/openapi.json")
        assert resp.status_code == 200
        assert "/api/plan-trip" in resp.json()["paths"]

    def test_docs_accessible(self):
        assert client.get("/api/docs").status_code == 200
