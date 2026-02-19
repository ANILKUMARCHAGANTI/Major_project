# Nutrition & Hydration Pattern Prediction — Full Toolkit

This repository provides an **offline, end-to-end** pipeline for the project:
**"Nutrition and Hydration Pattern Prediction from Sports Performance Logs"**.

It includes:
- **Synthetic dataset generator** (realistic physiology + environment)
- **Preprocessing & Feature Engineering**
- **EDA** (figures saved to disk)
- **Conventional ML models** (Linear/ElasticNet/RF/GB; optional MLP)
- **Novel Algorithm — HAAE (Hydration-Aware Adaptive Ensemble)**
- **Statistical Validation** (k-fold CV, paired t-test, bootstrap CI, Bland–Altman, ANOVA across athletes)
- **Reproducible outputs** (figures + tables)

## Quick Start

1) Create a virtual environment and install requirements
```bash
pip install -r requirements.txt
```

2) (Optional) Regenerate a dataset
```bash
python src/generate_dataset.py   --out data/synthetic_logs.csv   --n_athletes 150   --days 120   --seed 42
```

3) Run the full pipeline (preprocess → EDA → models → novel → stats)
```bash
python src/run_all.py   --data data/synthetic_logs.csv   --outdir outputs   --target hydration_deficit_pct   --epochs 20
```

Outputs are written to `outputs/`:
```
outputs/
  figures/        # PNG charts
  tables/         # CSV metrics & stats
  models/         # saved models (joblib)
  logs/           # training history (JSON)
```

## Novel Method: HAAE
**Hydration-Aware Adaptive Ensemble** combines RF, GB, and a small MLP/BiLSTM (optional)
with **physiology-informed weighting** based on derived hydration and caloric balance.
It adapts per-batch weights via a simple meta-optimizer to improve predictive accuracy and reduce bias.

## Note
- All code is CPU-friendly and offline.
- You can scale dataset size via CLI flags.
