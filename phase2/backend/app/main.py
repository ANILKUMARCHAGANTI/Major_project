"""
Athlete Readiness API - Phase 2
FastAPI backend: explainable metrics, alerts, recommendations, per-athlete isolation.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routes import auth_routes, profile_routes, input_routes, dashboard_routes, alerts_routes, recommendations_routes, explain_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    # shutdown if needed


app = FastAPI(
    title="Athlete Readiness API",
    description="Explainable, self-logged athlete readiness system. 8 core metrics, rule-based alerts, context-aware recommendations.",
    version="2.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(profile_routes.router)
app.include_router(input_routes.router)
app.include_router(dashboard_routes.router)
app.include_router(alerts_routes.router)
app.include_router(recommendations_routes.router)
app.include_router(explain_routes.router)


@app.get("/health")
async def health():
    from app.config import get_settings
    db_url = get_settings().database_url
    db_type = "supabase" if "supabase" in db_url or "pooler.supabase" in db_url else ("postgresql" if "postgresql" in db_url else "sqlite")
    return {"status": "healthy", "version": "2.0.0", "database": db_type}
