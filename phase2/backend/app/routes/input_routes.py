"""Input routes: submit daily logs and training sessions."""
from datetime import date, timedelta
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete

from app.database import get_db
from app.models import Athlete, DailyLog, TrainingSession, MetricSnapshot, Alert, Recommendation
from app.schemas import DailyLogInput, TrainingSessionInput, SubmitResponse, MetricsResponse, AlertResponse, RecommendationResponse
from app.auth import get_current_athlete
from app.services.metrics import compute_all_metrics
from app.services.alerts import evaluate_all_alerts
from app.services.recommendations import generate_contextual_recommendations

router = APIRouter(prefix="/inputs", tags=["inputs"])


async def _get_acute_chronic(db: AsyncSession, athlete_id: int, as_of: date) -> tuple[float, float]:
    """Compute acute (7d) and chronic (28d) load from sessions."""
    start_7 = as_of - timedelta(days=7)
    start_28 = as_of - timedelta(days=28)
    # Acute: sum of session_mins * (intensity/10) for last 7 days
    q7 = await db.execute(
        select(func.coalesce(func.sum(TrainingSession.session_mins * TrainingSession.intensity / 10), 0)).where(
            TrainingSession.athlete_id == athlete_id,
            TrainingSession.session_date >= start_7,
            TrainingSession.session_date < as_of,
        )
    )
    acute = float(q7.scalar() or 0)
    q28 = await db.execute(
        select(func.coalesce(func.sum(TrainingSession.session_mins * TrainingSession.intensity / 10), 0)).where(
            TrainingSession.athlete_id == athlete_id,
            TrainingSession.session_date >= start_28,
            TrainingSession.session_date < as_of,
        )
    )
    chronic = float(q28.scalar() or 0)
    if chronic == 0:
        chronic = 1.0  # avoid div by zero
    return acute, chronic


async def _get_session_counts(db: AsyncSession, athlete_id: int, as_of: date) -> tuple[int, int]:
    """Session count in last 7 and 14 days."""
    start_7 = as_of - timedelta(days=7)
    start_14 = as_of - timedelta(days=14)
    q7 = await db.execute(
        select(func.count(TrainingSession.id)).where(
            TrainingSession.athlete_id == athlete_id,
            TrainingSession.session_date >= start_7,
            TrainingSession.session_date < as_of,
        )
    )
    q14 = await db.execute(
        select(func.count(TrainingSession.id)).where(
            TrainingSession.athlete_id == athlete_id,
            TrainingSession.session_date >= start_14,
            TrainingSession.session_date < as_of,
        )
    )
    return int(q7.scalar() or 0), int(q14.scalar() or 0)


@router.post("/daily", response_model=SubmitResponse)
async def submit_daily_log(
    inp: DailyLogInput,
    athlete: Athlete = Depends(get_current_athlete),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit daily recovery/hydration/nutrition log.
    Triggers metric computation, alerts, and recommendations immediately.
    """
    # Check duplicate date
    q = await db.execute(
        select(DailyLog).where(
            DailyLog.athlete_id == athlete.id,
            DailyLog.log_date == inp.log_date,
        )
    )
    existing = q.scalar_one_or_none()
    if existing:
        # Update existing
        for k, v in inp.model_dump().items():
            setattr(existing, k, v)
        daily = existing
        # Remove old metrics/alerts/recs
        await db.execute(delete(MetricSnapshot).where(MetricSnapshot.daily_log_id == existing.id))
        await db.execute(delete(Alert).where(Alert.daily_log_id == existing.id))
        await db.execute(delete(Recommendation).where(Recommendation.daily_log_id == existing.id))
    else:
        data = inp.model_dump()
        data.pop('log_date', None)  # Remove log_date from dict to avoid duplicate
        daily = DailyLog(
            athlete_id=athlete.id,
            log_date=inp.log_date,
            **data,
        )
        db.add(daily)
        await db.flush()

    caloric_balance = inp.calories_in - (athlete.bmr_kcal + inp.activity_calories)
    daily.caloric_balance = caloric_balance

    acute, chronic = await _get_acute_chronic(db, athlete.id, inp.log_date)
    cnt7, cnt14 = await _get_session_counts(db, athlete.id, inp.log_date)
    # Use 0 for session_mins when no session on this day - we use historical
    session_mins = 0  # daily log doesn't have session; use 60 as placeholder for recs
    intensity = 6.0

    metrics_dict = compute_all_metrics(
        log_date=inp.log_date,
        sleep_hours=inp.sleep_hours,
        soreness=inp.soreness,
        mood=inp.mood,
        water_intake_L=inp.water_intake_L,
        sweat_loss_L=inp.sweat_loss_L,
        calories_in=inp.calories_in,
        activity_calories=inp.activity_calories,
        bmr=athlete.bmr_kcal,
        acute_load=acute,
        chronic_load=chronic,
        session_count_7d=cnt7,
        session_count_14d=cnt14,
        temp_c=inp.temp_c,
        humidity=inp.humidity,
    )

    snapshot = MetricSnapshot(
        daily_log_id=daily.id,
        readiness_score=metrics_dict["readiness_score"],
        fatigue_index=metrics_dict["fatigue_index"],
        recovery_score=metrics_dict["recovery_score"],
        hydration_score=metrics_dict["hydration_score"],
        nutrition_score=metrics_dict["nutrition_score"],
        consistency_score=metrics_dict["consistency_score"],
        acute_load=metrics_dict["acute_load"],
        chronic_load=metrics_dict["chronic_load"],
        acute_chronic_ratio=metrics_dict["acute_chronic_ratio"],
        training_load_balance=metrics_dict["training_load_balance"],
        formula_version=metrics_dict["formula_version"],
        breakdown_json=json.dumps(metrics_dict["breakdown"]),
    )
    db.add(snapshot)
    await db.flush()

    alerts = evaluate_all_alerts(
        metrics=metrics_dict,
        sleep_hours=inp.sleep_hours,
        soreness=inp.soreness,
        water_intake_L=inp.water_intake_L,
        sweat_loss_L=inp.sweat_loss_L,
        calories_in=inp.calories_in,
        activity_calories=inp.activity_calories,
        bmr=athlete.bmr_kcal,
        session_mins=session_mins,
        temp_c=inp.temp_c,
    )

    alert_rows = []
    for a in alerts:
        alert_row = Alert(
            daily_log_id=daily.id,
            alert_type=a.alert_type,
            severity=a.severity,
            message=a.message,
            triggered_by=json.dumps(a.triggered_by),
        )
        db.add(alert_row)
        alert_rows.append(alert_row)
    await db.flush()

    recs = generate_contextual_recommendations(
        metrics=metrics_dict,
        alerts=alerts,
        temp_c=inp.temp_c,
        humidity=inp.humidity,
        session_mins=session_mins,
        intensity=intensity,
    )
    rec_rows = []
    for r in recs:
        rec_row = Recommendation(
            daily_log_id=daily.id,
            category=r.category,
            priority=r.priority,
            message=r.message,
            context_used=json.dumps(r.context_used),
        )
        db.add(rec_row)
        rec_rows.append(rec_row)

    await db.flush()
    for ar in alert_rows:
        await db.refresh(ar)
    for rr in rec_rows:
        await db.refresh(rr)

    return SubmitResponse(
        log_date=inp.log_date,
        metrics=MetricsResponse(
            readiness_score=metrics_dict["readiness_score"],
            fatigue_index=metrics_dict["fatigue_index"],
            recovery_score=metrics_dict["recovery_score"],
            hydration_score=metrics_dict["hydration_score"],
            nutrition_score=metrics_dict["nutrition_score"],
            consistency_score=metrics_dict["consistency_score"],
            acute_load=metrics_dict["acute_load"],
            chronic_load=metrics_dict["chronic_load"],
            acute_chronic_ratio=metrics_dict["acute_chronic_ratio"],
            training_load_balance=metrics_dict["training_load_balance"],
            breakdown=metrics_dict["breakdown"],
        ),
        alerts=[AlertResponse(id=ar.id, alert_type=ar.alert_type, severity=ar.severity, message=ar.message, created_at=ar.created_at) for ar in alert_rows],
        recommendations=[RecommendationResponse(id=rr.id, category=rr.category, priority=rr.priority, message=rr.message, created_at=rr.created_at) for rr in rec_rows],
    )


@router.post("/session")
async def submit_session(
    inp: TrainingSessionInput,
    athlete: Athlete = Depends(get_current_athlete),
    db: AsyncSession = Depends(get_db),
):
    """Submit a training session. Per-athlete isolation enforced."""
    session = TrainingSession(
        athlete_id=athlete.id,
        session_date=inp.session_date,
        session_mins=inp.session_mins,
        intensity=inp.intensity,
        distance_km=inp.distance_km,
        activity_type=inp.activity_type,
        notes=inp.notes,
    )
    db.add(session)
    await db.flush()
    return {"id": session.id, "session_date": inp.session_date, "message": "Session logged"}
