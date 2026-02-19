"""Dashboard routes: metrics overview, latest readiness."""
from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database import get_db
from app.models import Athlete, DailyLog, MetricSnapshot
from app.auth import get_current_athlete

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/latest")
async def get_latest_metrics(
    athlete: Athlete = Depends(get_current_athlete),
    db: AsyncSession = Depends(get_db),
):
    """Get latest metrics for the athlete (per-athlete isolation)."""
    q = await db.execute(
        select(DailyLog, MetricSnapshot)
        .join(MetricSnapshot, MetricSnapshot.daily_log_id == DailyLog.id)
        .where(DailyLog.athlete_id == athlete.id)
        .order_by(desc(DailyLog.log_date))
        .limit(1)
    )
    row = q.first()
    if not row:
        return {"message": "No data yet", "metrics": None}
    daily, snap = row
    import json
    return {
        "log_date": str(daily.log_date),
        "metrics": {
            "readiness_score": snap.readiness_score,
            "fatigue_index": snap.fatigue_index,
            "recovery_score": snap.recovery_score,
            "hydration_score": snap.hydration_score,
            "nutrition_score": snap.nutrition_score,
            "consistency_score": snap.consistency_score,
            "acute_chronic_ratio": snap.acute_chronic_ratio,
            "training_load_balance": snap.training_load_balance,
            "acute_load": snap.acute_load,
            "chronic_load": snap.chronic_load,
        },
        "breakdown": json.loads(snap.breakdown_json) if snap.breakdown_json else {},
    }


@router.get("/history")
async def get_metric_history(
    days: int = Query(30, ge=7, le=90),
    athlete: Athlete = Depends(get_current_athlete),
    db: AsyncSession = Depends(get_db),
):
    """Get metric history for trends (per-athlete isolation)."""
    cutoff = date.today() - timedelta(days=days)
    q = await db.execute(
        select(DailyLog.log_date, MetricSnapshot)
        .join(MetricSnapshot, MetricSnapshot.daily_log_id == DailyLog.id)
        .where(DailyLog.athlete_id == athlete.id, DailyLog.log_date >= cutoff)
        .order_by(DailyLog.log_date)
    )
    rows = q.all()
    return {
        "history": [
            {
                "date": str(r[0]),
                "readiness_score": r[1].readiness_score,
                "fatigue_index": r[1].fatigue_index,
                "recovery_score": r[1].recovery_score,
                "hydration_score": r[1].hydration_score,
                "nutrition_score": r[1].nutrition_score,
                "acute_chronic_ratio": r[1].acute_chronic_ratio,
            }
            for r in rows
        ],
    }
