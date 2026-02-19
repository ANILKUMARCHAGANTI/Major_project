# AthleteReadiness: Explainable Athlete Intelligence Platform

## What is this?

**AthleteReadiness** is a web application that helps athletes (and coaches) understand their training readiness in real-time. It's not a generic fitness tracker—it's built around self-logged inputs (training, recovery, hydration, nutrition) and converts them into **explainable, actionable insights**.

Instead of a black-box prediction, you get:
- A transparent **Readiness Score** (0–100) with a breakdown of what's affecting it
- **Real-time alerts** (e.g., "Overtraining risk detected. Reduce load by 20%.")
- **Context-aware recommendations** (e.g., "Post-workout: eat 25g protein + 40g carbs within 30 min")
- **Full visibility** into your hydration, nutrition, and recovery metrics

## Why Phase-2? (The honest story)

### Phase-1 Problem
Phase-1 had a vague problem statement and poorly-structured data. We were trying to predict "patterns" without a clear use case. It felt academic but not useful.

### Phase-2 Solution
We completely redesigned around a **clear, athlete-centric problem**: *How do we help athletes understand their readiness right now, with only their own logged data?*

This Phase-2 is:
- ✅ **Explainable** — every metric has a formula you can audit
- ✅ **Self-contained** — no external APIs or proprietary datasets
- ✅ **Actionable** — generates specific, non-medical recommendations
- ✅ **Reproducible** — all logic is deterministic and testable
- ✅ **Deployable** — production-grade tech stack, ready to run locally or in the cloud

---

## Quick Start (3 minutes)

### Prerequisites
- Python 3.10+ with venv
- Node.js 18+ with npm

### Setup & Run

**1. Enter project:**
```bash
cd phase2
```

**2. Backend (FastAPI)**
```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\Activate.ps1
# Mac/Linux:
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload
```
API at `http://localhost:8000` | Swagger: `http://localhost:8000/docs`

**3. Frontend (React + Vite)**
```bash
cd ../frontend
npm install
npm run dev
```
UI at `http://localhost:5173` (or next available port)

**4. Open browser**
Go to `http://localhost:5173`

---

## Architecture (30-second overview)

```
React UI (Profile, Dashboard, Alerts) 
       ↕ REST API
FastAPI Backend (compute + rules + explainability)
       ↕ SQL
Database (SQLite dev / PostgreSQL prod)
```

---

## How It Works (The Pipeline)

### 1. Log Your Session
- Workout: type, duration, intensity, RPE
- Recovery: hours since last, sleep, soreness
- Hydration: water intake, environment, feeling
- Nutrition: meal timing, quality, protein & carbs

### 2. Backend Computes Metrics
| Metric | What It Means |
|--------|--------------|
| **Training Load** | How hard you worked (duration × intensity × RPE) |
| **Fatigue** | Cumulative tiredness (7-day trend) |
| **Acute:Chronic** | Are you overtraining (>1.4) or undertraining (<0.6)? |
| **Hydration** | Water adequacy vs body weight & conditions |
| **Nutrition** | Meal completeness (quality + protein + carbs) |
| **Recovery** | Rest quality (hours + sleep + soreness) |
| **Readiness** | Overall score 0–100 (Green/Yellow/Red) |

### 3. Alerts Trigger
- "Overtraining risk — reduce load & rest 48–72h"
- "Poor hydration — drink 0.5L water + electrolytes"
- "Insufficient recovery — prioritize sleep"
- "Nutrition mismatch — eat protein post-workout"

### 4. Dashboard Shows Everything
Score, zone color, alert list, recommendations, trends over time.

---

## Key Features

✅ **Explainability** – Call `/api/explainability?metric=readiness` to see exactly how your score was calculated  
✅ **Rule-Based Logic** – No black-box ML; everything is auditable  
✅ **Per-Athlete Data** – Your data is yours; fully isolated  
✅ **Mobile-Friendly** – Works on tablet & phone  
✅ **Open Architecture** – Easy to add new metrics or integrate wearables  

---

## API (Quick Reference)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/athletes` | Create athlete profile |
| POST | `/api/sessions` | Submit training session |
| GET | `/api/features/latest?athlete_id=1` | Latest readiness & metrics |
| GET | `/api/features/history?athlete_id=1` | Trend data (last 30 days) |
| GET | `/api/alerts?athlete_id=1` | Active alerts |
| GET | `/api/recommendations?athlete_id=1` | Suggestions |
| GET | `/api/explainability?metric=readiness&athlete_id=1` | Full metric breakdown |

Full docs: `http://localhost:8000/docs`

---

## Tech Stack

**Backend:** FastAPI + SQLAlchemy (Python)  
**Frontend:** React 18 + TypeScript + Vite  
**Database:** SQLite (dev) / PostgreSQL (prod)  
**Charts:** Plotly  
**No Docker** (as per spec)  

---

## Project Structure

```
phase2/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app
│   │   ├── compute.py           # Feature engine
│   │   ├── alerts.py            # Alert rules
│   │   ├── explainability.py    # Metric explanations
│   │   ├── models.py            # DB tables
│   │   └── ...
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/               # Profile, Dashboard, Alerts, etc.
│   │   └── ...
│   └── package.json
└── README.md
```

---

## Demo Scenario

**Create athlete:**
```bash
curl -X POST http://localhost:8000/api/athletes \
  -H "Content-Type: application/json" \
  -d '{
    "age": 25,
    "gender": "male",
    "sport_type": "endurance",
    "training_level": "intermediate",
    "weight_kg": 75
  }'
```

**Log a session:**
```bash
curl -X POST http://localhost:8000/api/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "athlete_id": 1,
    "session_date": "2026-02-19",
    "duration_min": 60,
    "intensity": "moderate",
    "rpe": 6,
    "water_l": 1.5,
    "sleep_quality": "good",
    "meal_quality": "balanced",
    ...
  }'
```

Response will include computed readiness score, alerts, and recommendations.

---

## FAQ

**Q: Is my data private?**  
A: Yes. SQLite is local; PostgreSQL Supabase is encrypted. Zero external APIs.

**Q: Are these recommendations medical advice?**  
A: No. General, supportive guidance only. Consult a coach/nutritionist for personalized plans.

**Q: Can I export my data?**  
A: Yes, from the UI (planned) or by querying SQLite directly.

**Q: Can I add my own metrics?**  
A: Yes. `compute.py` is modular — add functions without breaking existing logic.

---

## Team Roles (3-person split)

| Role | Focus |
|------|-------|
| **Member A** | Compute engine, explainability, tests (`compute.py`, `explainability.py`) |
| **Member B** | API, models, alerts (`main.py`, `models.py`, `alerts.py`) |
| **Member C** | Frontend UI, demo (`pages/`, charts, README) |

---

## Next Steps

- [ ] Unit tests for compute functions
- [ ] JWT authentication enforcement
- [ ] Email alert notifications
- [ ] Wearable data integration (Garmin, Oura)
- [ ] Personalized thresholds (ML phase)
- [ ] Admin coach dashboard

---

## Troubleshooting

**Backend won't start?**  
→ Check Python version (3.10+). Ensure venv is activated. Try `pip install --upgrade pip`.

**Frontend can't connect to backend?**  
→ Is backend running on `:8000`? Check firewall. Try `http://localhost:8000/docs`.

**Port already in use?**  
→ Kill process: `lsof -i :8000` (Mac/Linux) or use Task Manager (Windows).

---

**Built by 3 CS students | Phase-2 Academic Project | MIT License**  
Have fun, log honestly, train smart. 🏃‍♂️💪
