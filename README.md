# Nutrition & Hydration Pattern Prediction + AthleteReadiness Platform

## Project Overview (Two Modules, One Journey)

This is a **two-phase academic project** exploring sports performance analytics and athlete support systems.

- **Phase-1 (N&H Pipeline)**: Nutrition & Hydration Pattern Prediction for Sports Performance Logs
  - Dataset: synthetic sports performance logs
  - Goal: explore patterns in nutrition, hydration, and training
  - Technology: Python ML pipeline (scikit-learn, SHAP, baseline models)

- **Phase-2 (AthleteReadiness)**: A complete redesign into an explainable athlete readiness web application
  - Goal: real-time, actionable athlete support using only self-logged inputs
  - Technology: FastAPI + React + TypeScript (production-grade)
  - Team: 3 CS students

**Why the change?** Phase-1 taught us what NOT to do (vague problem, weak data). Phase-2 is a deliberate redesign with clear objectives, explainability, and deployability.

---

## Project Structure

```
nutri_hydration_pipeline_plus/
│
├── PHASE-1 (N&H Pattern Prediction Pipeline)
│   ├── src/                          # Python scripts for data exploration & ML
│   │   ├── generate_dataset.py       # Synthetic data generation
│   │   ├── preprocess.py             # Data cleaning & engineering
│   │   ├── eda.py                    # Exploratory data analysis
│   │   ├── models_baselines.py       # Baseline models (Linear, ElasticNet, RF, GB)
│   │   ├── novel_haae.py             # Novel HAAE model (Hybrid Auto-Encoder)
│   │   ├── shap_explainer.py         # SHAP-based explainability
│   │   ├── stats_validate.py         # Statistical validation (Friedman test)
│   │   └── run_all.py                # End-to-end pipeline runner
│   ├── outputs/                      # Results, models, metrics, figures
│   │   ├── baselines/                # Baseline model artifacts
│   │   ├── haae/                     # HAAE model weights & predictions
│   │   └── tables/                   # Statistical test results
│   ├── data/
│   │   └── synthetic_logs.csv        # Generated synthetic dataset
│   ├── requirements.txt              # Python dependencies
│   └── README.md                     # Phase-1 documentation
│
├── PHASE-2 (AthleteReadiness Web App)
│   ├── backend/                      # FastAPI application
│   │   ├── app/
│   │   │   ├── main.py               # FastAPI endpoints
│   │   │   ├── database.py           # SQLAlchemy ORM + persistence
│   │   │   ├── models.py             # DB tables (Athlete, Session, Metric, Alert)
│   │   │   ├── schemas.py            # Pydantic validators
│   │   │   ├── compute.py            # Feature engine (formulas & metrics)
│   │   │   ├── alerts.py             # Rule-based alert engine
│   │   │   ├── explainability.py     # Per-metric explanations
│   │   │   └── routes/               # Route handlers
│   │   ├── tests/                    # Unit tests (planned)
│   │   ├── requirements.txt          # Backend dependencies
│   │   └── run.py                    # Startup script
│   │
│   ├── frontend/                     # React + TypeScript UI
│   │   ├── src/
│   │   │   ├── pages/                # 6 main pages (Profile, Inputs, Dashboard, etc.)
│   │   │   ├── components/           # Reusable UI components
│   │   │   ├── context/              # Auth & state management
│   │   │   ├── App.tsx               # Main app
│   │   │   └── main.tsx              # Entry point
│   │   ├── vite.config.ts
│   │   ├── tsconfig.json
│   │   ├── package.json
│   │   └── index.html
│   │
│   ├── docs/
│   │   ├── EXPLAINABILITY.md         # Formula documentation
│   │   └── ARCHITECTURE.md           # Technical deep-dive
│   │
│   └── README.md                     # Phase-2 setup & quick start
│
├── phase2_baseline_comparison.md     # Phase-1 vs Phase-2 analysis
├── requirements.txt                  # Main project dependencies
└── README.md                         # This file
```

---

## Phase-1: Nutrition & Hydration Pattern Prediction

**Goal:** Explore machine learning on synthetic sports performance data.

### What it does
- Generates synthetic athlete logs (training, nutrition, hydration)
- Trains baseline models (Linear Regression, ElasticNet, Random Forest, Gradient Boosting)
- Trains a novel HAAE model (Hybrid Auto-Encoder + Attention)
- Compares models using statistical tests (Friedman test)
- Explains predictions using SHAP

### Quick Start (Phase-1)
```bash
cd nutri_hydration_pipeline_plus
python -m venv venv
venv\Scripts\Activate.ps1          # Windows
source venv/bin/activate           # Mac/Linux

pip install -r requirements.txt
python src/run_all.py              # Generates data, trains models, outputs results
```

### Outputs
- Model artifacts in `outputs/baselines/` and `outputs/haae/`
- Metrics in `outputs/tables/`
- Predictions & evaluation plots in `outputs/figures/`

### Files Overview
| File | Purpose |
|------|---------|
| `generate_dataset.py` | Creates synthetic athlete logs |
| `preprocess.py` | Cleans and engineers features |
| `models_baselines.py` | Trains & evaluates baseline models |
| `novel_haae.py` | Implements HAAE (novel model) |
| `shap_explainer.py` | Post-hoc explainability via SHAP |
| `stats_validate.py` | Statistical significance testing |

---

## Phase-2: AthleteReadiness (The Redesign)

**Goal:** Build a production-grade, explainable athlete support application.

### What it does
- Accepts self-logged training, recovery, hydration, nutrition inputs
- Computes 7 transparent metrics (readiness score, fatigue, hydration, nutrition, recovery, consistency, acute:chronic load)
- Triggers rule-based alerts (overtraining, poor hydration, nutrition mismatch)
- Provides context-aware, non-medical recommendations
- Displays results in a multi-page React UI with charts and trends

### Why it's different from Phase-1
| Aspect | Phase-1 | Phase-2 |
|--------|---------|---------|
| **Problem** | Pattern discovery (vague) | Athlete readiness support (clear) |
| **Data** | Synthetic, unstructured | Self-logged, user-provided |
| **Logic** | Black-box ML models | Transparent rules & formulas |
| **Output** | Predictions + SHAP explanations | Scores + alerts + recommendations |
| **UI** | None (Python scripts only) | Full web application |
| **Deployment** | Research artifact | Production-ready |

### Quick Start (Phase-2)

**Backend:**
```bash
cd phase2/backend
python -m venv .venv
.venv\Scripts\Activate.ps1          # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```
API runs at `http://localhost:8000` | Swagger: `http://localhost:8000/docs`

**Frontend:**
```bash
cd phase2/frontend
npm install
npm run dev
```
UI runs at `http://localhost:5173`

**Demo:**
1. Create an athlete: `POST /api/athletes`
2. Submit a session: `POST /api/sessions`
3. View readiness: `GET /api/features/latest`
4. See explainability: `GET /api/explainability?metric=readiness`

### Core Metrics (Phase-2)

All formulas are transparent and auditable:

| Metric | Formula | Purpose |
|--------|---------|---------|
| **Training Load** | `duration × intensity × (1 + RPE_factor)` | Quantifies workout effort |
| **Fatigue Index** | EWM(training_load, span=7d) | 7-day cumulative fatigue |
| **Acute:Chronic** | `mean(7d) / mean(28d)` | Overtraining detector |
| **Hydration** | `(water / target) × env_factor × feeling` | Hydration adequacy |
| **Nutrition** | `0.5×quality + 0.25×protein + 0.25×carbs` | Meal completeness |
| **Recovery** | `0.5×hours + 0.3×sleep + 0.2×soreness` | Rest quality |
| **Readiness** | `0.35×recovery + 0.25×(1-fatigue) + 0.15×hydration + 0.15×nutrition + 0.10×consistency` | **Overall score 0–100** |

### Alert Rules (Phase-2)
- **Overtraining:** Fatigue high + readiness low + AC:CH >1.4 → "Reduce load, rest 48–72h"
- **Poor Hydration:** Score <0.5 → "Drink 0.5L + electrolytes"
- **Insufficient Recovery:** Score <0.4 → "Prioritize sleep"
- **Nutrition Mismatch:** Score <0.5 + advanced athlete → "Eat protein post-workout"

### Tech Stack (Phase-2)
**Backend:** FastAPI + SQLAlchemy + Pydantic (Python)  
**Frontend:** React 18 + TypeScript + Vite + Plotly  
**Database:** SQLite (dev) / PostgreSQL (prod)  
**No Docker** ✓

---

## Team Work Distribution (Phase-2)

Since this is a 3-person group project:

| Member | Role | Phase-2 Deliverable |
|--------|------|---------------------|
| **Member A** | Compute & Explainability | `compute.py`, `explainability.py`, unit tests |
| **Member B** | Backend API & Integration | `main.py`, `models.py`, `alerts.py`, database setup |
| **Member C** | Frontend UI & Demo | React pages, charts, Swagger demo, README |

---

## How to Present (Code Review Tips)

**Narrative to your teacher:**

> *"Phase-1 was a pattern discovery exercise—we learned what NOT to do (vague problem, weak dataset). Phase-2 is the redesign: we pivoted to a clear, athlete-centric problem and built a production-grade web app. Phase-2 uses only self-logged inputs, transparent formulas, and rule-based logic. Every metric is explainable and auditable. It's not just research—it's deployable."*

**Quick demo flow (5 minutes):**
1. Show backend API via Swagger (`/docs`)
2. Create athlete + submit session (show returned metrics & alerts)
3. Call explainability endpoint (show breakdown)
4. Open React UI dashboard (show score, zone, recommendations, trends)

---

## Dependencies

**Phase-1 (Python ML Pipeline):**
```
numpy, pandas, matplotlib, scikit-learn, scipy, joblib, shap, tensorflow, keras
```

**Phase-2 Backend:**
```
fastapi, uvicorn, sqlalchemy, pydantic, numpy, python-dotenv, pytest, httpx
```

**Phase-2 Frontend:**
```
react, typescript, vite, axios, plotly, @mui/material (or chakra-ui)
```

---

## Running Everything Locally

**Option A: Just Phase-2 (recommended for demo)**
```bash
cd phase2/backend
pip install -r requirements.txt
uvicorn app.main:app --reload
# In another terminal:
cd phase2/frontend
npm install
npm run dev
```

**Option B: Both Phase-1 and Phase-2**
```bash
# Phase-1
pip install -r requirements.txt
python src/run_all.py

# Phase-2 (see Option A)
```

---

## Deployment (Phase-2)

**Backend:** Render, Railway, or Azure App Service  
**Frontend:** Vercel  
**Database:** PostgreSQL on Supabase (free tier available)  
**No Docker needed** ✓

---

## FAQ

**Q: Are these two separate projects?**  
A: They're two phases of one course. Phase-1 was exploration phase. Phase-2 is a deliberate redesign and production deliverable.

**Q: Should I run both?**  
A: For viva, show Phase-2 (the web app). Phase-1 is context (shows your learning journey).

**Q: Can I extend Phase-2?**  
A: Absolutely. Add wearable integration, personalized thresholds, or ML layers—modular design supports it.

**Q: Is Phase-2 production-ready?**  
A: Mostly. Auth is minimal (JWT scaffold ready). Add hardened auth before production.

---

## Project Timeline (Typical)

| Week | Phase-1 | Phase-2 |
|------|---------|---------|
| 1 | ✅ Complete | Backend scaffold + compute engine |
| 2 | — | Frontend UI + API wiring |
| 3 | — | Tests, sample data, explainability docs |
| 4 | — | Polish, viva materials, demo prep |

---

## Next Steps

- [ ] Phase-2: Add unit tests
- [ ] Phase-2: Enforce JWT auth
- [ ] Phase-2: Deploy to Vercel + Render
- [ ] Phase-2: Wearable integration (Garmin, Oura)
- [ ] Future: Personalized ML thresholds

---

## Resources & Docs

- `phase2/README.md` — Phase-2 setup & features
- `phase2/docs/EXPLAINABILITY.md` — Formula documentation
- `phase2/docs/ARCHITECTURE.md` — Technical design
- `outputs/tables/baseline_metrics.csv` — Phase-1 benchmark results
- `http://localhost:8000/docs` — Live API docs (when backend is running)

---

## License & Attribution

**MIT License** — Built by 3 CS students as an academic learning project.

*"From vague pattern discovery to clear athlete support: a journey in problem framing, explainability, and production engineering."*

---

**Questions?** Check the phase-specific README files or contact the team.  
**Ready to demo?** Start with `cd phase2` and follow the quick start above. 🚀
