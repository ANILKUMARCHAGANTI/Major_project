"""SQLAlchemy models for Athlete Readiness."""
from datetime import datetime, date
from sqlalchemy import String, Float, Integer, Date, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Athlete(Base):
    """Athlete profile - per-athlete data isolation."""
    __tablename__ = "athletes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), default="")
    sport: Mapped[str] = mapped_column(String(100), default="general")
    body_mass_kg: Mapped[float] = mapped_column(Float, default=70.0)
    bmr_kcal: Mapped[float] = mapped_column(Float, default=1700.0)
    vo2max: Mapped[float] = mapped_column(Float, default=50.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    daily_logs: Mapped[list["DailyLog"]] = relationship(back_populates="athlete", order_by="DailyLog.log_date")
    sessions: Mapped[list["TrainingSession"]] = relationship(back_populates="athlete", order_by="TrainingSession.session_date")


class DailyLog(Base):
    """Self-reported daily recovery, hydration, and nutrition."""
    __tablename__ = "daily_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    athlete_id: Mapped[int] = mapped_column(Integer, ForeignKey("athletes.id"), nullable=False)
    log_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Recovery
    sleep_hours: Mapped[float] = mapped_column(Float, default=7.0)
    soreness: Mapped[float] = mapped_column(Float, default=3.0)  # 0-10 scale
    mood: Mapped[float] = mapped_column(Float, default=5.0)  # 0-10

    # Hydration (L)
    water_intake_L: Mapped[float] = mapped_column(Float, default=2.5)
    sweat_loss_L: Mapped[float] = mapped_column(Float, default=1.5)

    # Nutrition (kcal)
    calories_in: Mapped[float] = mapped_column(Float, default=2200.0)
    activity_calories: Mapped[float] = mapped_column(Float, default=500.0)
    caloric_balance: Mapped[float] = mapped_column(Float, default=0.0)

    # Environment (for context)
    temp_c: Mapped[float] = mapped_column(Float, default=22.0)
    humidity: Mapped[float] = mapped_column(Float, default=0.5)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    athlete: Mapped["Athlete"] = relationship(back_populates="daily_logs")
    metrics: Mapped[list["MetricSnapshot"]] = relationship(back_populates="daily_log", cascade="all, delete-orphan")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="daily_log", cascade="all, delete-orphan")
    recommendations: Mapped[list["Recommendation"]] = relationship(back_populates="daily_log", cascade="all, delete-orphan")


class TrainingSession(Base):
    """Training session log."""
    __tablename__ = "training_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    athlete_id: Mapped[int] = mapped_column(Integer, ForeignKey("athletes.id"), nullable=False)
    session_date: Mapped[date] = mapped_column(Date, nullable=False)

    session_mins: Mapped[float] = mapped_column(Float, default=60.0)
    intensity: Mapped[float] = mapped_column(Float, default=6.0)  # 0-10 RPE scale
    distance_km: Mapped[float] = mapped_column(Float, default=0.0)
    activity_type: Mapped[str] = mapped_column(String(100), default="general")
    notes: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    athlete: Mapped["Athlete"] = relationship(back_populates="sessions")


class MetricSnapshot(Base):
    """Computed metrics for a given day - explainable, stored for audit."""
    __tablename__ = "metric_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    daily_log_id: Mapped[int] = mapped_column(Integer, ForeignKey("daily_logs.id"), nullable=False)

    readiness_score: Mapped[float] = mapped_column(Float, default=0.0)
    fatigue_index: Mapped[float] = mapped_column(Float, default=0.0)
    recovery_score: Mapped[float] = mapped_column(Float, default=0.0)
    hydration_score: Mapped[float] = mapped_column(Float, default=0.0)
    nutrition_score: Mapped[float] = mapped_column(Float, default=0.0)
    consistency_score: Mapped[float] = mapped_column(Float, default=0.0)
    acute_load: Mapped[float] = mapped_column(Float, default=0.0)
    chronic_load: Mapped[float] = mapped_column(Float, default=0.0)
    acute_chronic_ratio: Mapped[float] = mapped_column(Float, default=1.0)
    training_load_balance: Mapped[float] = mapped_column(Float, default=100.0)  # 0-100 interpretable

    formula_version: Mapped[str] = mapped_column(String(20), default="1.0")
    breakdown_json: Mapped[str] = mapped_column(Text, default="{}")  # Explainability

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    daily_log: Mapped["DailyLog"] = relationship(back_populates="metrics")


class Alert(Base):
    """Rule-triggered alert for a day."""
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    daily_log_id: Mapped[int] = mapped_column(Integer, ForeignKey("daily_logs.id"), nullable=False)

    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)  # overtraining, hydration, recovery, nutrition_mismatch
    severity: Mapped[str] = mapped_column(String(20), default="medium")  # low, medium, high
    message: Mapped[str] = mapped_column(Text, nullable=False)
    triggered_by: Mapped[str] = mapped_column(Text, default="{}")  # JSON of rule conditions
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    daily_log: Mapped["DailyLog"] = relationship(back_populates="alerts")


class Recommendation(Base):
    """Context-aware recommendation for a day."""
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    daily_log_id: Mapped[int] = mapped_column(Integer, ForeignKey("daily_logs.id"), nullable=False)

    category: Mapped[str] = mapped_column(String(50), nullable=False)  # hydration, nutrition, recovery, training
    priority: Mapped[int] = mapped_column(Integer, default=0)  # higher = show first
    message: Mapped[str] = mapped_column(Text, nullable=False)
    context_used: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    daily_log: Mapped["DailyLog"] = relationship(back_populates="recommendations")
