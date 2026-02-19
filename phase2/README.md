# Athlete Readiness System — Phase 2

Explainable, self-logged athlete readiness with 8 core metrics, rule-based alerts, and context-aware recommendations.

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy (async)
- **Database**: SQLite (local) or **Supabase** (PostgreSQL, recommended)
- **Frontend**: React, TypeScript, Vite
- **Auth**: JWT
- **No Docker** (as per scope)

## Quick Start

### 1. Backend

```bash
cd phase2/backend
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend

```bash
cd phase2/frontend
npm install
npm run dev
```

### 3. Use the app

- Open http://localhost:5173
- Register a new account
- Go to **Profile** and set BMR, body mass, etc.
- Go to **Inputs** and submit a daily log (sleep, hydration, nutrition, etc.)
- View **Dashboard**, **Alerts**, **Recommendations**, **Trends**

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /auth/register | Register |
| POST | /auth/login | Login |
| GET | /profile/me | Get profile |
| PATCH | /profile/me | Update profile |
| POST | /inputs/daily | Submit daily log |
| POST | /inputs/session | Submit training session |
| GET | /dashboard/latest | Latest metrics |
| GET | /dashboard/history | Metric history |
| GET | /alerts | List alerts |
| GET | /recommendations | List recommendations |
| GET | /explain/breakdown/{date} | Explainability for date |
| GET | /explain/formulas | Formula documentation |

## 8 Core Metrics

1. **Readiness Score** (0–100) — Weighted composite
2. **Fatigue Index** (0–10)
3. **Recovery Score** (0–100)
4. **Hydration Score** (0–100)
5. **Nutrition Score** (0–100)
6. **Consistency Score** (0–100)
7. **Acute:Chronic Load** (ratio)
8. **Training Load Balance** (0–100)

## Alerts

- Overtraining risk
- Poor hydration
- Insufficient recovery
- Nutrition–training mismatch

## Data Storage

- **SQLite** (default): `phase2/backend/readiness.db`
- **Supabase**: PostgreSQL in the cloud — scalable, free tier, backups

## Data Privacy

- Per-athlete isolation: each user sees only their own data
- JWT authentication
