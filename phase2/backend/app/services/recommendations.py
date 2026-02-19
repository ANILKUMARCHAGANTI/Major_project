"""
Context-Aware Recommendation Engine - non-medical, athlete-friendly guidance.
Adapts to training load, fatigue, recovery, hydration, nutrition context.
"""
from dataclasses import dataclass
from typing import Any
from app.services.alerts import Alert


@dataclass
class Recommendation:
    category: str  # hydration, nutrition, recovery, training
    priority: int  # higher = show first
    message: str
    context_used: dict[str, Any]


# Priority order: hydration > recovery > nutrition > training
PRIORITY_MAP = {"hydration": 40, "recovery": 30, "nutrition": 20, "training": 10}


def alert_to_recommendations(alerts: list[Alert]) -> list[Recommendation]:
    """Convert alerts to recommendations (alerts already contain contextual messages)."""
    recs = []
    for a in alerts:
        recs.append(Recommendation(
            category=a.alert_type if a.alert_type != "nutrition_mismatch" else "nutrition",
            priority=PRIORITY_MAP.get(
                "hydration" if a.alert_type == "hydration" else
                "recovery" if a.alert_type == "recovery" else
                "nutrition" if a.alert_type == "nutrition_mismatch" else "training",
                10,
            ) + (20 if a.severity == "high" else 0),
            message=a.message,
            context_used=a.triggered_by,
        ))
    return recs


def generate_contextual_recommendations(
    metrics: dict,
    alerts: list[Alert],
    temp_c: float,
    humidity: float,
    session_mins: float,
    intensity: float,
) -> list[Recommendation]:
    """
    Generate context-aware recommendations from alerts and current state.
    Adds proactive guidance when no alert fired but context suggests improvement.
    """
    recs = alert_to_recommendations(alerts)
    alert_types = {a.alert_type for a in alerts}

    # Proactive: hydration in hot conditions even if no alert
    if "hydration" not in alert_types and temp_c > 28 and metrics.get("hydration_score", 80) < 85:
        recs.append(Recommendation(
            category="hydration",
            priority=15,
            message="Hot conditions detected. Pre-hydrate with 0.3–0.5 L before your next session and consider electrolytes if session > 60 min.",
            context_used={"temp_c": temp_c, "hydration_score": metrics.get("hydration_score")},
        ))

    # Proactive: recovery after hard week
    if "recovery" not in alert_types and metrics.get("acute_chronic_ratio", 1.0) > 1.2:
        recs.append(Recommendation(
            category="recovery",
            priority=12,
            message="Training load is elevated. Ensure adequate sleep (7–9 h) and consider a light day or rest to optimize adaptation.",
            context_used={"acute_chronic_ratio": metrics.get("acute_chronic_ratio")},
        ))

    # Proactive: nutrition for long sessions
    if "nutrition_mismatch" not in alert_types and session_mins > 90 and intensity > 6:
        recs.append(Recommendation(
            category="nutrition",
            priority=8,
            message="Long, intense session. Refuel within 30–60 min with carbs and protein to support recovery.",
            context_used={"session_mins": session_mins, "intensity": intensity},
        ))

    recs.sort(key=lambda r: -r.priority)
    return recs[:5]  # Top 5
