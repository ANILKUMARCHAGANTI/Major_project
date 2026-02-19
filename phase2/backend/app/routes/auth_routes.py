"""Auth routes: register, login."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import Athlete
from app.schemas import UserCreate, UserLogin, Token
from app.auth import get_password_hash, create_access_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new athlete."""
    result = await db.execute(select(Athlete).where(Athlete.email == user.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    athlete = Athlete(
        email=user.email,
        hashed_password=get_password_hash(user.password),
        full_name=user.full_name or "",
    )
    db.add(athlete)
    await db.flush()
    await db.refresh(athlete)
    token = create_access_token(data={"sub": str(athlete.id)})
    return Token(access_token=token)


@router.post("/login", response_model=Token)
async def login(cred: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login and get JWT."""
    result = await db.execute(select(Athlete).where(Athlete.email == cred.email))
    athlete = result.scalar_one_or_none()
    if not athlete or not verify_password(cred.password, athlete.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not athlete.is_active:
        raise HTTPException(status_code=401, detail="Account disabled")
    token = create_access_token(data={"sub": str(athlete.id)})
    return Token(access_token=token)
