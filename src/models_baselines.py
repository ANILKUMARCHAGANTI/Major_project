import argparse, os
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, KFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression, ElasticNet
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import r2_score, mean_squared_error
from joblib import dump

from preprocess import engineer, select_features

def metrics(y_true, y_pred):
    return {
        "R2": float(r2_score(y_true, y_pred)),
        "RMSE": float(np.sqrt(mean_squared_error(y_true, y_pred)))
    }

def train_models(df, target, outdir):
    os.makedirs(outdir, exist_ok=True)
    feats = select_features(df, target_cols=[target])
    X = df[feats].values
    y = df[target].values

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    models = {
        "Linear": Pipeline([("scaler", StandardScaler()), ("model", LinearRegression())]),
        "ElasticNet": Pipeline([("scaler", StandardScaler()), ("model", ElasticNet(alpha=0.1, l1_ratio=0.3, random_state=42))]),
        "RandomForest": RandomForestRegressor(n_estimators=300, random_state=42, n_jobs=-1),
        "GradientBoosting": GradientBoostingRegressor(random_state=42)
    }

    rows = []
    for name, mdl in models.items():
        mdl.fit(X_train, y_train)
        pred = mdl.predict(X_test)
        m = metrics(y_test, pred)
        rows.append({"model": name, **m})
        dump(mdl, os.path.join(outdir, f"{name}.joblib"))
        # save predictions
        pd.DataFrame({"y_true": y_test, "y_pred": pred}).to_csv(os.path.join(outdir, f"{name}_preds.csv"), index=False)

    pd.DataFrame(rows).to_csv(os.path.join(outdir, "baseline_metrics.csv"), index=False)
    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=str, required=True)
    ap.add_argument("--target", type=str, default="hydration_deficit_pct")
    ap.add_argument("--outdir", type=str, required=True)
    args = ap.parse_args()
    df = pd.read_csv(args.data)
    df = engineer(df, target_cols=[args.target])
    rows = train_models(df, args.target, args.outdir)
    print("Saved baseline models and metrics to", args.outdir)

if __name__ == "__main__":
    main()
