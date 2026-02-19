"""Recommendations routes."""
from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database import get_db
from app.models import Athlete, DailyLog, Recommendation
from app.auth import get_current_athlete
from app.schemas import RecommendationResponse

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("", response_model=list[RecommendationResponse])
async def list_recommendations(
    days: int = Query(7, ge=1, le=30),
    athlete: Athlete = Depends(get_current_athlete),
    db: AsyncSession = Depends(get_db),
):
    """List recommendations for the athlete (per-athlete isolation)."""
    cutoff = date.today() - timedelta(days=days)
    q = await db.execute(
        select(Recommendation, DailyLog.log_date)
        .join(DailyLog, Recommendation.daily_log_id == DailyLog.id)
        .where(DailyLog.athlete_id == athlete.id, DailyLog.log_date >= cutoff)
        .order_by(desc(Recommendation.priority), desc(DailyLog.log_date))
        .limit(20)
    )
    rows = q.all()
    return [
        RecommendationResponse(id=r.id, category=r.category, priority=r.priority, message=r.message, created_at=r.created_at)
        for r, _ in rows
    ]
