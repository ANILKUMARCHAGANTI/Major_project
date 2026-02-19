"""
Feature Compute Service - 8 explainable metrics with transparent formulas.
All outputs are traceable; no black-box models.
Formula version: 1.0
"""
from dataclasses import dataclass, field
from typing import Any
import json
from datetime import date, timedelta


@dataclass
class MetricResult:
    """Single metric with full explainability."""
    name: str
    value: float
    formula: str
    inputs: dict[str, Any] = field(default_factory=dict)
    intermediate: dict[str, Any] = field(default_factory=dict)
    weight_contributions: dict[str, float] = field(default_factory=dict)


def _clip(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def compute_recovery_score(sleep_hours: float, soreness: float, mood: float) -> MetricResult:
    """
    Recovery Score (0-100).
    Formula: 0.4 * sleep_component + 0.35 * (10-soreness)/10*100 + 0.25 * mood/10*100
    Optimal sleep ~8h, soreness 0, mood 10.
    """
    sleep_component = _clip(sleep_hours / 10.0, 0, 1) * 100  # 10h = 100
    soreness_component = ((10 - soreness) / 10) * 100
    mood_component = (mood / 10) * 100
    score = 0.4 * sleep_component + 0.35 * soreness_component + 0.25 * mood_component
    return MetricResult(
        name="recovery_score",
        value=round(_clip(score, 0, 100), 1),
        formula="0.4 * (sleep/10*100) + 0.35 * ((10-soreness)/10*100) + 0.25 * (mood/10*100)",
        inputs={"sleep_hours": sleep_hours, "soreness": soreness, "mood": mood},
        intermediate={
            "sleep_component": sleep_component,
            "soreness_component": soreness_component,
            "mood_component": mood_component,
        },
        weight_contributions={"sleep": 0.4, "soreness": 0.35, "mood": 0.25},
    )


def compute_hydration_score(water_intake_L: float, sweat_loss_L: float) -> MetricResult:
    """
    Hydration Score (0-100).
    Formula: 100 - |deficit_pct| where deficit_pct = (sweat - intake)/sweat*100 (clipped).
    Perfect balance = 100. Deficit 20% -> score 80.
    """
    if sweat_loss_L <= 0:
        deficit_pct = 0.0
    else:
        deficit_pct = ((sweat_loss_L - water_intake_L) / sweat_loss_L) * 100
    deficit_pct = _clip(deficit_pct, -50, 80)  # Over-hydration cap
    score = 100 - abs(deficit_pct)
    return MetricResult(
        name="hydration_score",
        value=round(_clip(score, 0, 100), 1),
        formula="100 - |(sweat_loss - water_intake)/sweat_loss * 100|",
        inputs={"water_intake_L": water_intake_L, "sweat_loss_L": sweat_loss_L},
        intermediate={"deficit_pct": deficit_pct, "hydration_gap_L": sweat_loss_L - water_intake_L},
        weight_contributions={"intake_vs_sweat": 1.0},
    )


def compute_nutrition_score(calories_in: float, activity_calories: float, bmr: float) -> MetricResult:
    """
    Nutrition Index (0-100).
    Caloric balance = calories_in - (bmr + activity). Optimal balance near 0.
    Score: 100 at balance 0, decreases with |balance|.
    Formula: 100 - min(50, |balance|/50) for typical 2500 kcal/day scale.
    """
    total_expenditure = bmr + activity_calories
    caloric_balance = calories_in - total_expenditure
    # Balance within ±500 -> 100, outside decreases
    balance_score = 100 - min(50, abs(caloric_balance) / 10)  # ±500 = -50 from 100
    balance_score = _clip(balance_score, 0, 100)
    return MetricResult(
        name="nutrition_score",
        value=round(balance_score, 1),
        formula="100 - min(50, |calories_in - (bmr + activity_calories)| / 10)",
        inputs={"calories_in": calories_in, "activity_calories": activity_calories, "bmr": bmr},
        intermediate={
            "total_expenditure": total_expenditure,
            "caloric_balance": caloric_balance,
        },
        weight_contributions={"caloric_balance": 1.0},
    )


def compute_fatigue_index(
    sleep_hours: float, soreness: float, hydration_deficit_pct: float,
    caloric_balance: float
) -> MetricResult:
    """
    Fatigue Index (0-10).
    Based on hydration deficit, caloric balance, sleep, soreness.
    Formula from literature-inspired composite.
    """
    h_component = _clip(hydration_deficit_pct / 80, 0, 1) * 3.5  # hydration contributes up to 3.5
    c_component = (1 - _clip((caloric_balance + 800) / 800, 0, 1)) * 2.5  # deficit increases fatigue
    s_component = (1 - _clip(sleep_hours / 10, 0, 1)) * 2.0  # poor sleep
    sor_component = (soreness / 10) * 2.0  # soreness
    fatigue = h_component + c_component + s_component + sor_component
    return MetricResult(
        name="fatigue_index",
        value=round(_clip(fatigue, 0, 10), 1),
        formula="hydration_component + caloric_component + sleep_component + soreness_component",
        inputs={
            "sleep_hours": sleep_hours,
            "soreness": soreness,
            "hydration_deficit_pct": hydration_deficit_pct,
            "caloric_balance": caloric_balance,
        },
        intermediate={
            "h_component": h_component,
            "c_component": c_component,
            "s_component": s_component,
            "sor_component": sor_component,
        },
        weight_contributions={"hydration": 0.35, "nutrition": 0.25, "sleep": 0.2, "soreness": 0.2},
    )


def compute_acute_chronic(
    acute_load: float, chronic_load: float
) -> tuple[MetricResult, MetricResult]:
    """
    Acute load (7-day), Chronic load (28-day), Acute:Chronic ratio.
    Training load = session_mins * intensity (session-level).
    """
    ratio = acute_chronic_ratio = acute_load / chronic_load if chronic_load > 0 else 1.0
    ratio = _clip(ratio, 0.3, 3.0)
    # Training Load Balance: 100 when ratio ~1.0 (sweet spot), decreases as ratio deviates
    # Optimal range 0.8-1.3
    if 0.8 <= ratio <= 1.3:
        balance = 100.0
    elif ratio < 0.8:
        balance = 100 - (0.8 - ratio) * 150  # under-training
    else:
        balance = 100 - (ratio - 1.3) * 100  # over-training
    balance = _clip(balance, 0, 100)
    return (
        MetricResult(
            name="acute_chronic",
            value=round(ratio, 2),
            formula="acute_load_7d / chronic_load_28d",
            inputs={"acute_load": acute_load, "chronic_load": chronic_load},
            intermediate={},
            weight_contributions={},
        ),
        MetricResult(
            name="training_load_balance",
            value=round(balance, 1),
            formula="100 when ratio in [0.8,1.3], else penalty by deviation",
            inputs={"acute_chronic_ratio": ratio},
            intermediate={"acute_load": acute_load, "chronic_load": chronic_load},
            weight_contributions={},
        ),
    )


def compute_consistency_score(session_count_7d: int, session_count_14d: int) -> MetricResult:
    """
    Consistency (0-100): regularity of training.
    Assumes 3-5 sessions/week is ideal. More or less = lower consistency.
    """
    if session_count_14d == 0:
        return MetricResult(
            name="consistency_score",
            value=50.0,  # no data = neutral
            formula="neutral when no sessions",
            inputs={"session_count_7d": session_count_7d, "session_count_14d": session_count_14d},
            intermediate={},
            weight_contributions={},
        )
    sessions_per_week = session_count_14d / 2
    # Ideal 4 sessions/week
    deviation = abs(sessions_per_week - 4)
    score = 100 - deviation * 15  # -15 per session deviation
    return MetricResult(
        name="consistency_score",
        value=round(_clip(score, 0, 100), 1),
        formula="100 - |sessions_per_week - 4| * 15",
        inputs={"session_count_7d": session_count_7d, "session_count_14d": session_count_14d},
        intermediate={"sessions_per_week": sessions_per_week, "deviation": deviation},
        weight_contributions={},
    )


def compute_readiness_score(
    recovery: float, hydration: float, nutrition: float,
    fatigue: float, consistency: float, load_balance: float
) -> MetricResult:
    """
    Readiness Score (0-100): weighted composite.
    Weights: Recovery 25%, Hydration 20%, Nutrition 20%, Fatigue (inverse) 15%, Consistency 10%, Load Balance 10%.
    """
    fatigue_inverse = 100 - (fatigue / 10) * 100  # 0 fatigue -> 100, 10 fatigue -> 0
    score = (
        0.25 * recovery +
        0.20 * hydration +
        0.20 * nutrition +
        0.15 * fatigue_inverse +
        0.10 * consistency +
        0.10 * load_balance
    )
    return MetricResult(
        name="readiness_score",
        value=round(_clip(score, 0, 100), 1),
        formula="0.25*recovery + 0.20*hydration + 0.20*nutrition + 0.15*(100-fatigue*10) + 0.10*consistency + 0.10*load_balance",
        inputs={
            "recovery": recovery, "hydration": hydration, "nutrition": nutrition,
            "fatigue": fatigue, "consistency": consistency, "load_balance": load_balance,
        },
        weight_contributions={
            "recovery": 0.25, "hydration": 0.20, "nutrition": 0.20,
            "fatigue": 0.15, "consistency": 0.10, "load_balance": 0.10,
        },
    )


def compute_all_metrics(
    log_date: date,
    sleep_hours: float, soreness: float, mood: float,
    water_intake_L: float, sweat_loss_L: float,
    calories_in: float, activity_calories: float, bmr: float,
    acute_load: float, chronic_load: float,
    session_count_7d: int, session_count_14d: int,
    temp_c: float = 22.0, humidity: float = 0.5,
) -> dict:
    """Compute all 8 metrics with full explainability."""
    # Derived
    hydration_deficit_pct = 0.0
    if sweat_loss_L > 0:
        hydration_deficit_pct = ((sweat_loss_L - water_intake_L) / sweat_loss_L) * 100
    hydration_deficit_pct = _clip(hydration_deficit_pct, -30, 80)
    caloric_balance = calories_in - (bmr + activity_calories)

    recovery = compute_recovery_score(sleep_hours, soreness, mood)
    hydration = compute_hydration_score(water_intake_L, sweat_loss_L)
    nutrition = compute_nutrition_score(calories_in, activity_calories, bmr)
    fatigue = compute_fatigue_index(sleep_hours, soreness, hydration_deficit_pct, caloric_balance)
    ac_result, load_balance = compute_acute_chronic(acute_load, chronic_load)
    consistency = compute_consistency_score(session_count_7d, session_count_14d)
    readiness = compute_readiness_score(
        recovery.value, hydration.value, nutrition.value,
        fatigue.value, consistency.value, load_balance.value,
    )

    def _to_dict(m: MetricResult) -> dict:
        return {
            "name": m.name,
            "value": m.value,
            "formula": m.formula,
            "inputs": m.inputs,
            "intermediate": m.intermediate,
            "weight_contributions": m.weight_contributions,
        }

    breakdown = {
        "readiness": _to_dict(readiness),
        "fatigue_index": _to_dict(fatigue),
        "recovery": _to_dict(recovery),
        "hydration": _to_dict(hydration),
        "nutrition": _to_dict(nutrition),
        "consistency": _to_dict(consistency),
        "acute_chronic": _to_dict(ac_result),
        "training_load_balance": _to_dict(load_balance),
    }

    return {
        "readiness_score": readiness.value,
        "fatigue_index": fatigue.value,
        "recovery_score": recovery.value,
        "hydration_score": hydration.value,
        "nutrition_score": nutrition.value,
        "consistency_score": consistency.value,
        "acute_load": acute_load,
        "chronic_load": chronic_load,
        "acute_chronic_ratio": ac_result.value,
        "training_load_balance": load_balance.value,
        "breakdown": breakdown,
        "formula_version": "1.0",
    }
