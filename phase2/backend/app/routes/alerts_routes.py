"""Alerts routes: list and get alerts."""
from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database import get_db
from app.models import Athlete, DailyLog, Alert
from app.auth import get_current_athlete
from app.schemas import AlertResponse

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertResponse])
async def list_alerts(
    days: int = Query(14, ge=1, le=90),
    athlete: Athlete = Depends(get_current_athlete),
    db: AsyncSession = Depends(get_db),
):
    """List alerts for the athlete (per-athlete isolation)."""
    cutoff = date.today() - timedelta(days=days)
    q = await db.execute(
        select(Alert)
        .join(DailyLog, Alert.daily_log_id == DailyLog.id)
        .where(DailyLog.athlete_id == athlete.id, DailyLog.log_date >= cutoff)
        .order_by(desc(Alert.created_at))
        .limit(50)
    )
    alerts = list(q.scalars().all())
    return [AlertResponse(id=a.id, alert_type=a.alert_type, severity=a.severity, message=a.message, created_at=a.created_at) for a in alerts]
