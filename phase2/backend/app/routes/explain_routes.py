"""Explainability routes: formula breakdowns, audit export."""
from datetime import date
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import Athlete, DailyLog, MetricSnapshot
from app.auth import get_current_athlete

router = APIRouter(prefix="/explain", tags=["explainability"])


@router.get("/breakdown/{log_date}")
async def get_explainability_breakdown(
    log_date: date,
    athlete: Athlete = Depends(get_current_athlete),
    db: AsyncSession = Depends(get_db),
):
    """Get full formula breakdown for a given date (reproducibility, audit)."""
    q = await db.execute(
        select(DailyLog, MetricSnapshot)
        .join(MetricSnapshot, MetricSnapshot.daily_log_id == DailyLog.id)
        .where(DailyLog.athlete_id == athlete.id, DailyLog.log_date == log_date)
    )
    row = q.first()
    if not row:
        raise HTTPException(status_code=404, detail="No data for this date")
    daily, snap = row
    breakdown = json.loads(snap.breakdown_json) if snap.breakdown_json else {}
    return {
        "log_date": str(log_date),
        "formula_version": snap.formula_version,
        "inputs": {
            "sleep_hours": daily.sleep_hours,
            "soreness": daily.soreness,
            "mood": daily.mood,
            "water_intake_L": daily.water_intake_L,
            "sweat_loss_L": daily.sweat_loss_L,
            "calories_in": daily.calories_in,
            "activity_calories": daily.activity_calories,
            "caloric_balance": daily.caloric_balance,
            "temp_c": daily.temp_c,
            "humidity": daily.humidity,
        },
        "metrics": {
            "readiness_score": snap.readiness_score,
            "fatigue_index": snap.fatigue_index,
            "recovery_score": snap.recovery_score,
            "hydration_score": snap.hydration_score,
            "nutrition_score": snap.nutrition_score,
            "consistency_score": snap.consistency_score,
            "acute_chronic_ratio": snap.acute_chronic_ratio,
            "training_load_balance": snap.training_load_balance,
        },
        "breakdown": breakdown,
    }


@router.get("/formulas")
async def get_formula_documentation():
    """Return formula documentation for reproducibility (Obj 6)."""
    return {
        "version": "1.0",
        "formulas": {
            "readiness_score": "0.25*recovery + 0.20*hydration + 0.20*nutrition + 0.15*(100-fatigue*10) + 0.10*consistency + 0.10*load_balance",
            "fatigue_index": "hydration_component + caloric_component + sleep_component + soreness_component (0-10 scale)",
            "recovery_score": "0.4 * (sleep/10*100) + 0.35 * ((10-soreness)/10*100) + 0.25 * (mood/10*100)",
            "hydration_score": "100 - |(sweat_loss - water_intake)/sweat_loss * 100|",
            "nutrition_score": "100 - min(50, |calories_in - (bmr + activity_calories)| / 10)",
            "consistency_score": "100 - |sessions_per_week - 4| * 15",
            "acute_chronic_ratio": "acute_load_7d / chronic_load_28d (session_mins * intensity/10)",
            "training_load_balance": "100 when ratio in [0.8,1.3], else penalty by deviation",
        },
        "references": "Self-reported inputs only. No external ML models.",
    }
