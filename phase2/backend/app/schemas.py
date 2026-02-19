"""Pydantic schemas for API."""
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# Auth
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    athlete_id: Optional[int] = None


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str = ""


class UserLogin(BaseModel):
    email: EmailStr
    password: str


# Profile
class AthleteProfileBase(BaseModel):
    full_name: str = ""
    sport: str = "general"
    body_mass_kg: float = 70.0
    bmr_kcal: float = 1700.0
    vo2max: float = 50.0


class AthleteProfile(AthleteProfileBase):
    id: int
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


# Daily Log Input
class DailyLogInput(BaseModel):
    log_date: date
    sleep_hours: float = Field(ge=0, le=24, default=7.0)
    soreness: float = Field(ge=0, le=10, default=3.0)
    mood: float = Field(ge=0, le=10, default=5.0)
    water_intake_L: float = Field(ge=0, le=20, default=2.5)
    sweat_loss_L: float = Field(ge=0, le=15, default=1.5)
    calories_in: float = Field(ge=0, le=10000, default=2200.0)
    activity_calories: float = Field(ge=0, le=5000, default=500.0)
    temp_c: float = Field(ge=-10, le=50, default=22.0)
    humidity: float = Field(ge=0, le=1, default=0.5)


class TrainingSessionInput(BaseModel):
    session_date: date
    session_mins: float = Field(ge=0, le=600, default=60.0)
    intensity: float = Field(ge=0, le=10, default=6.0)
    distance_km: float = Field(ge=0, le=200, default=0.0)
    activity_type: str = "general"
    notes: str = ""


# Metrics & Explainability
class MetricBreakdown(BaseModel):
    formula: str
    inputs: dict
    intermediate: dict
    weight_contributions: dict
    final_value: float


class MetricsResponse(BaseModel):
    readiness_score: float
    fatigue_index: float
    recovery_score: float
    hydration_score: float
    nutrition_score: float
    consistency_score: float
    acute_load: float
    chronic_load: float
    acute_chronic_ratio: float
    training_load_balance: float
    breakdown: dict


# Alerts & Recommendations
class AlertResponse(BaseModel):
    id: int
    alert_type: str
    severity: str
    message: str
    created_at: datetime

    class Config:
        from_attributes = True


class RecommendationResponse(BaseModel):
    id: int
    category: str
    priority: int
    message: str
    created_at: datetime

    class Config:
        from_attributes = True


# Combined submission response
class SubmitResponse(BaseModel):
    log_date: date
    metrics: MetricsResponse
    alerts: list[AlertResponse]
    recommendations: list[RecommendationResponse]
