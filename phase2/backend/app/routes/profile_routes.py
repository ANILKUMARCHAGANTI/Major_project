"""Profile routes: get/update athlete profile."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Athlete
from app.schemas import AthleteProfile, AthleteProfileBase
from app.auth import get_current_athlete

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/me", response_model=AthleteProfile)
async def get_profile(athlete: Athlete = Depends(get_current_athlete)):
    """Get current athlete profile (per-athlete isolation)."""
    return athlete


@router.patch("/me", response_model=AthleteProfile)
async def update_profile(
    patch: AthleteProfileBase,
    athlete: Athlete = Depends(get_current_athlete),
    db: AsyncSession = Depends(get_db),
):
    """Update athlete profile."""
    for k, v in patch.model_dump(exclude_unset=True).items():
        setattr(athlete, k, v)
    await db.flush()
    await db.refresh(athlete)
    return athlete
