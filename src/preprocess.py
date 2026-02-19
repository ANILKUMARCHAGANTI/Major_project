import argparse
import pandas as pd
import numpy as np

def add_temporal_features(df: pd.DataFrame, group_col: str = None):
    """
    Add rolling mean/std features over 7-day and 14-day windows.
    If group_col provided, compute rolling stats per group (e.g., per athlete).
    """
    df = df.copy()
    
    # Ensure data is sorted by time/date if available
    sort_cols = []
    if group_col and group_col in df.columns:
        sort_cols.append(group_col)
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        sort_cols.append('date')
    if sort_cols:
        df = df.sort_values(sort_cols).reset_index(drop=True)
    
    # Define columns to compute rolling stats on
    rolling_cols = [
        "session_mins", "intensity", "hr_avg", "distance_km", "activity_calories",
        "water_intake_L", "sweat_loss_L", "fatigue_score", "hydration_deficit_pct"
    ]
    rolling_cols = [c for c in rolling_cols if c in df.columns]
    
    # Function to compute rolling stats (per group or global)
    def compute_rolling(data):
        result = data.copy()
        for col in rolling_cols:
            if col in data.columns:
                # 7-day rolling window
                result[f"{col}_rolling7_mean"] = data[col].rolling(window=7, min_periods=1).mean()
                result[f"{col}_rolling7_std"] = data[col].rolling(window=7, min_periods=1).std().fillna(0)
                # 14-day rolling window
                result[f"{col}_rolling14_mean"] = data[col].rolling(window=14, min_periods=1).mean()
                result[f"{col}_rolling14_std"] = data[col].rolling(window=14, min_periods=1).std().fillna(0)
        return result
    
    # Apply groupby if group_col provided, else apply globally
    if group_col and group_col in df.columns:
        df = df.groupby(group_col, group_keys=False).apply(compute_rolling).reset_index(drop=True)
    else:
        df = compute_rolling(df)
    
    return df

def engineer(
    df: pd.DataFrame,
    group_col: str | None = "athlete_id",
    target_cols: list[str] | None = None,
):
    """Feature engineering shared by training and inference.

    Args:
        df: Raw dataframe.
        group_col: Optional column used to scope rolling features per entity.
        target_cols: Columns considered supervised targets (excluded from features).
    """

    df = df.copy()

    if target_cols is None:
        target_cols = []

    grp = group_col if group_col and group_col in df.columns else None
    df = add_temporal_features(df, group_col=grp)

    if {"sweat_loss_L", "water_intake_L"}.issubset(df.columns):
        df["sweat_loss_L"] = df["sweat_loss_L"].astype(float)
        df["water_intake_L"] = df["water_intake_L"].astype(float)
        df["hydration_gap_L"] = df["sweat_loss_L"] - df["water_intake_L"]
        if "hydration_deficit_pct" not in df.columns:
            with np.errstate(divide="ignore", invalid="ignore"):
                deficit = np.where(
                    df["sweat_loss_L"] > 0,
                    (df["sweat_loss_L"] - df["water_intake_L"]) /
                    np.maximum(df["sweat_loss_L"], 1e-6) * 100.0,
                    0.0,
                )
            df["hydration_deficit_pct"] = np.clip(deficit, -30, 80)
    if {"activity_calories", "session_mins"}.issubset(df.columns):
        df["work_rate"] = df["activity_calories"] / (df["session_mins"] + 1e-6)
    if {"hr_avg", "hr_rest"}.issubset(df.columns):
        df["hr_delta"] = df["hr_avg"] - df["hr_rest"]
    if "pace_min_per_km" in df.columns:
        df["pace_inv"] = 1.0 / (df["pace_min_per_km"] + 1e-6)
    if {"temp_c", "humidity"}.issubset(df.columns):
        df["env_index"] = (df["temp_c"] - 18) * (0.5 + df["humidity"])  # heat+humidity stress

    for c in ["hydration_deficit_pct", "caloric_balance", "fatigue_score"]:
        if c in df.columns:
            df[c] = df[c].clip(df[c].quantile(0.01), df[c].quantile(0.99))

    primary_target = target_cols[0] if target_cols else None
    if primary_target is None and "hydration_deficit_pct" in df.columns:
        primary_target = "hydration_deficit_pct"

    if primary_target and primary_target in df.columns:
        df["dehydration_risk"] = (df[primary_target] > 10).astype(int)

    return df

def select_features(
    df: pd.DataFrame,
    target_cols: list[str] | None = None,
):
    # Base features
    base_feats = [
        "sleep_hours","soreness","temp_c","humidity","session_mins","intensity",
        "hr_rest","hr_avg","distance_km","pace_min_per_km","work_rate","hr_delta",
        "pace_inv","env_index","bmr","vo2max","body_mass","calories_in","activity_calories",
        "water_intake_L","sweat_loss_L","caloric_balance","fatigue_score"
    ]
    
    # Temporal rolling features (7 & 14 day windows)
    rolling_cols = [
        "session_mins", "intensity", "hr_avg", "distance_km", "activity_calories",
        "water_intake_L", "sweat_loss_L", "fatigue_score", "hydration_deficit_pct"
    ]
    temporal_feats = []
    for col in rolling_cols:
        temporal_feats.extend([
            f"{col}_rolling7_mean", f"{col}_rolling7_std",
            f"{col}_rolling14_mean", f"{col}_rolling14_std"
        ])
    
    # Combine and filter to what exists in df
    all_feats = base_feats + temporal_feats

    if target_cols is None:
        target_cols = []

    exclude = set(target_cols)
    exclude.add("dehydration_risk")

    feats = [c for c in all_feats if c in df.columns and c not in exclude]
    return feats

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=str, required=True)
    ap.add_argument("--out", type=str, required=True)
    args = ap.parse_args()
    df = pd.read_csv(args.data)
    df = engineer(df)
    df.to_csv(args.out, index=False)
    print("Wrote preprocessed to", args.out)

if __name__ == "__main__":
    main()
