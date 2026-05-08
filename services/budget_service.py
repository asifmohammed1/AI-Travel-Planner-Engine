"""
Budget Service — validates and enriches budget allocation.
"""
from __future__ import annotations
from typing import Any, Dict


# Allocation ratios vary by travel style
_STYLE_RATIOS: Dict[str, Dict[str, float]] = {
    "budget":   {"accommodation": 0.30, "food": 0.30, "transportation": 0.20, "activities": 0.10, "shopping": 0.05, "emergency": 0.05},
    "mid":      {"accommodation": 0.38, "food": 0.25, "transportation": 0.15, "activities": 0.12, "shopping": 0.05, "emergency": 0.05},
    "luxury":   {"accommodation": 0.45, "food": 0.20, "transportation": 0.12, "activities": 0.13, "shopping": 0.07, "emergency": 0.03},
}


def classify_budget(total: float, days: int, travelers: int) -> str:
    """Classify trip as budget / mid / luxury based on daily per-person spend."""
    per_person_per_day = total / (days * travelers)
    if per_person_per_day < 80:
        return "budget"
    if per_person_per_day < 250:
        return "mid"
    return "luxury"


def compute_budget_breakdown(
    total: float, days: int, travelers: int
) -> Dict[str, Any]:
    """
    Compute a recommended budget breakdown.
    Overrides Gemini output if the totals don't add up.
    """
    style = classify_budget(total, days, travelers)
    ratios = _STYLE_RATIOS[style]

    breakdown: Dict[str, Any] = {}
    allocated = 0.0
    items = list(ratios.items())

    for i, (category, ratio) in enumerate(items[:-1]):
        amount = round(total * ratio, 2)
        breakdown[category] = amount
        allocated += amount

    # Last category absorbs rounding residual
    last_key = items[-1][0]
    breakdown[last_key] = round(total - allocated, 2)

    breakdown["total"] = total
    breakdown["per_person"] = round(total / travelers, 2)
    breakdown["currency"] = "USD"
    breakdown["style"] = style
    breakdown["per_person_per_day"] = round(total / (days * travelers), 2)

    return breakdown


def validate_and_enrich_breakdown(
    ai_breakdown: Dict[str, Any],
    total_budget: float,
    days: int,
    travelers: int,
) -> Dict[str, Any]:
    """Validate AI-generated breakdown and replace if figures are inconsistent."""
    try:
        categories = ["accommodation", "food", "transportation", "activities", "shopping", "emergency"]
        actual_total = sum(float(ai_breakdown.get(c, 0)) for c in categories)
        tolerance = total_budget * 0.05  # 5% tolerance

        if abs(actual_total - total_budget) > tolerance:
            return compute_budget_breakdown(total_budget, days, travelers)

        # Enrich with metadata
        ai_breakdown["style"] = classify_budget(total_budget, days, travelers)
        ai_breakdown["per_person_per_day"] = round(total_budget / (days * travelers), 2)
        return ai_breakdown
    except Exception:
        return compute_budget_breakdown(total_budget, days, travelers)
