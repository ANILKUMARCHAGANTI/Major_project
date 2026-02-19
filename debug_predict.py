"""
Debug script to load HAAE models and run sample predictions using the same
preprocessing pipeline as the Streamlit app. Prints per-model outputs and
saves results to `outputs/debug_predict_script.csv`.
"""
import os
import sys
import pandas as pd
import numpy as np
from joblib import load

# Ensure src is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from preprocess import engineer, select_features
except Exception as e:
    print("Could not import preprocessing pipeline from src/:", e)
    raise

TRAINING_DATA = os.path.join("outputs", "preprocessed.csv")
MODEL_DIR = os.path.join("outputs", "haae")
rf = load(os.path.join(MODEL_DIR, "HAAE_rf.joblib"))
gb = load(os.path.join(MODEL_DIR, "HAAE_gb.joblib"))
mlp = load(os.path.join(MODEL_DIR, "HAAE_mlp.joblib"))

# If LSTM exists, attempt to load (joblib or keras)
lstm = None
lstm_path = os.path.join(MODEL_DIR, "HAAE_lstm.joblib")
if os.path.exists(lstm_path):
    try:
        lstm = load(lstm_path)
    except Exception:
        lstm = None

# Determine canonical training feature order
if os.path.exists(TRAINING_DATA):
    train_df = pd.read_csv(TRAINING_DATA)
    train_features = select_features(train_df, target_cols=["hydration_deficit_pct"])
else:
    print(f"Training data not found at {TRAINING_DATA}. Falling back to feature selection from sample rows.")
    train_features = None

# Define a base input using defaults - match keys from app.py DEFAULT_VALUES
base = {
    "sleep_hours": 8.0,
    "soreness": 3.0,
    "temp_c": 25.0,
    "humidity": 0.65,
    "session_mins": 60,
    "intensity": 7,
    "hr_rest": 60,
    "hr_avg": 140,
    "distance_km": 10.0,
    "pace_min_per_km": 6.0,
    "calories_in": 2500,
    "activity_calories": 800,
    "caloric_balance": -300,
    "water_intake_L": 2.5,
    "sweat_loss_L": 2.0,
    "bmr": 1700,
    "vo2max": 50,
    "body_mass": 75,
    "fatigue_score": 5.0
}

# Create a few scaled variants to ensure models respond
scales = [0.8, 1.0, 1.2]
rows = []
for s in scales:
    row = {k: (v * s if isinstance(v, (int, float)) else v) for k, v in base.items()}
    rows.append(row)

results = []
for i, r in enumerate(rows):
    df = pd.DataFrame([r])
    try:
        df_proc = engineer(df, target_cols=["hydration_deficit_pct"])
    except Exception as e:
        print("Preprocessing failed:", e)
        raise

    if train_features is None:
        feats = select_features(df_proc, target_cols=["hydration_deficit_pct"])
    else:
        feats = train_features

    missing = [c for c in feats if c not in df_proc.columns]
    for col in missing:
        df_proc[col] = 0.0

    X = df_proc.reindex(columns=feats, fill_value=0.0).values

    rf_pred = float(rf.predict(X)[0])
    gb_pred = float(gb.predict(X)[0])
    mlp_pred = float(mlp.predict(X)[0])
    ensemble = float(np.mean([rf_pred, gb_pred, mlp_pred]))

    print(f"--- Sample {i} (scale={scales[i]}) ---")
    print("RF:", rf_pred)
    print("GB:", gb_pred)
    print("MLP:", mlp_pred)
    print("Ensemble:", ensemble)
    print()

    res = {"scale": scales[i], **{f: r[f] for f in r}, "RF": rf_pred, "GB": gb_pred, "MLP": mlp_pred, "Ensemble": ensemble}
    results.append(res)

# Save results
out_path = os.path.join("outputs", "debug_predict_script.csv")
pd.DataFrame(results).to_csv(out_path, index=False)
print(f"Saved debug predictions to {out_path}")
