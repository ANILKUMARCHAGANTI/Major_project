"""
Rule-based Alert Engine - detects overtraining, hydration risk, recovery, nutrition mismatch.
All rules are transparent and traceable.
"""
from dataclasses import dataclass
from typing import Any


@dataclass
class Alert:
    alert_type: str
    severity: str  # low, medium, high
    message: str
    triggered_by: dict[str, Any]


# Global thresholds (per scope - adaptive per-athlete deferred)
THRESHOLDS = {
    "overtraining": {
        "acute_chronic_min": 1.5,
        "recovery_max": 50,
        "fatigue_min": 6.0,
    },
    "hydration": {
        "hydration_score_max": 70,
        "deficit_pct_min": 10,
        "sweat_intake_ratio_min": 1.2,  # sweat > 1.2 * intake
    },
    "recovery": {
        "recovery_score_max": 50,
        "sleep_hours_max": 6.5,
        "soreness_min": 6.0,
    },
    "nutrition_mismatch": {
        "nutrition_score_max": 70,
        "deficit_kcal_min": 400,
        "surplus_kcal_min": 500,
        "activity_calories_min": 600,  # hard session but low intake
    },
}


def check_overtraining(
    acute_chronic_ratio: float,
    recovery_score: float,
    fatigue_index: float,
) -> list[Alert]:
    """Detect overtraining risk: high AC ratio + low recovery + high fatigue."""
    alerts = []
    t = THRESHOLDS["overtraining"]
    conditions = []
    if acute_chronic_ratio >= t["acute_chronic_min"]:
        conditions.append(f"acute:chronic={acute_chronic_ratio:.2f} >= {t['acute_chronic_min']}")
    if recovery_score <= t["recovery_max"]:
        conditions.append(f"recovery={recovery_score:.1f} <= {t['recovery_max']}")
    if fatigue_index >= t["fatigue_min"]:
        conditions.append(f"fatigue={fatigue_index:.1f} >= {t['fatigue_min']}")
    if len(conditions) >= 2:
        msg = "Overtraining risk: training load may be too high relative to recovery. "
        msg += "Consider a rest day or reduced intensity."
        alerts.append(Alert(
            alert_type="overtraining",
            severity="high" if len(conditions) == 3 else "medium",
            message=msg,
            triggered_by={"conditions": conditions, "acute_chronic_ratio": acute_chronic_ratio},
        ))
    return alerts


def check_hydration(
    hydration_score: float,
    water_intake_L: float,
    sweat_loss_L: float,
    temp_c: float,
) -> list[Alert]:
    """Detect hydration risk: low score, high sweat vs intake."""
    alerts = []
    t = THRESHOLDS["hydration"]
    conditions = []
    if hydration_score <= t["hydration_score_max"]:
        conditions.append(f"hydration_score={hydration_score:.1f} <= {t['hydration_score_max']}")
    if sweat_loss_L > 0 and water_intake_L > 0 and sweat_loss_L / water_intake_L >= t["sweat_intake_ratio_min"]:
        conditions.append(f"sweat/intake ratio={sweat_loss_L/water_intake_L:.2f}")
    if conditions:
        deficit = sweat_loss_L - water_intake_L if sweat_loss_L > 0 else 0
        msg = "Hydration risk: fluid intake may be insufficient. "
        if temp_c > 28:
            msg += "In hot conditions, consider increasing water by 0.3–0.5 L and monitoring sweat loss."
        else:
            msg += "Consider increasing water intake before and during your next session."
        alerts.append(Alert(
            alert_type="hydration",
            severity="high" if hydration_score <= 50 else "medium",
            message=msg,
            triggered_by={"conditions": conditions, "deficit_L": deficit},
        ))
    return alerts


def check_recovery(
    recovery_score: float,
    sleep_hours: float,
    soreness: float,
) -> list[Alert]:
    """Detect insufficient recovery."""
    alerts = []
    t = THRESHOLDS["recovery"]
    conditions = []
    if recovery_score <= t["recovery_score_max"]:
        conditions.append(f"recovery_score={recovery_score:.1f} <= {t['recovery_score_max']}")
    if sleep_hours <= t["sleep_hours_max"]:
        conditions.append(f"sleep={sleep_hours:.1f}h <= {t['sleep_hours_max']}h")
    if soreness >= t["soreness_min"]:
        conditions.append(f"soreness={soreness:.1f} >= {t['soreness_min']}")
    if conditions:
        msg = "Insufficient recovery detected. "
        if sleep_hours < 7:
            msg += "Aim for at least 7.5 hours of sleep tonight."
        elif soreness >= 6:
            msg += "Consider active recovery (light walk, mobility) or a rest day."
        else:
            msg += "Prioritize sleep and light activity to support recovery."
        alerts.append(Alert(
            alert_type="recovery",
            severity="high" if recovery_score <= 40 else "medium",
            message=msg,
            triggered_by={"conditions": conditions},
        ))
    return alerts


def check_nutrition_mismatch(
    nutrition_score: float,
    caloric_balance: float,
    activity_calories: float,
    session_mins: float,
) -> list[Alert]:
    """Detect nutrition–training mismatch: hard session with inadequate fuel."""
    alerts = []
    t = THRESHOLDS["nutrition_mismatch"]
    conditions = []
    if nutrition_score <= t["nutrition_score_max"]:
        conditions.append(f"nutrition_score={nutrition_score:.1f} <= {t['nutrition_score_max']}")
    if caloric_balance <= -t["deficit_kcal_min"]:
        conditions.append(f"caloric_deficit={abs(caloric_balance):.0f} kcal")
    if activity_calories >= t["activity_calories_min"] and caloric_balance < -200:
        conditions.append("high_activity_with_deficit")
    if conditions:
        msg = "Nutrition–training mismatch: energy intake may not match your activity. "
        if caloric_balance < -400:
            msg += "Consider a nutrient-dense recovery meal (approx. 400–500 kcal) to support adaptation."
        else:
            msg += "Monitor your caloric balance to ensure adequate fuel for training."
        alerts.append(Alert(
            alert_type="nutrition_mismatch",
            severity="high" if abs(caloric_balance) > 600 else "medium",
            message=msg,
            triggered_by={"conditions": conditions, "caloric_balance": caloric_balance},
        ))
    return alerts


def evaluate_all_alerts(
    metrics: dict,
    sleep_hours: float,
    soreness: float,
    water_intake_L: float,
    sweat_loss_L: float,
    calories_in: float,
    activity_calories: float,
    bmr: float,
    session_mins: float,
    temp_c: float,
) -> list[Alert]:
    """Run all alert rules and return list of triggered alerts."""
    caloric_balance = calories_in - (bmr + activity_calories)
    all_alerts = []
    all_alerts.extend(check_overtraining(
        metrics.get("acute_chronic_ratio", 1.0),
        metrics.get("recovery_score", 70),
        metrics.get("fatigue_index", 4.0),
    ))
    all_alerts.extend(check_hydration(
        metrics.get("hydration_score", 80),
        water_intake_L,
        sweat_loss_L,
        temp_c,
    ))
    all_alerts.extend(check_recovery(
        metrics.get("recovery_score", 70),
        sleep_hours,
        soreness,
    ))
    all_alerts.extend(check_nutrition_mismatch(
        metrics.get("nutrition_score", 75),
        caloric_balance,
        activity_calories,
        session_mins,
    ))
    return all_alerts
