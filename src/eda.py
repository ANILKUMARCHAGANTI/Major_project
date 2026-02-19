import argparse, os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def fig_path(outdir, name): return os.path.join(outdir, f"{name}.png")

def run_eda(df, outdir):
    os.makedirs(outdir, exist_ok=True)

    # 1. Targets distribution
    fig = plt.figure(figsize=(6,4))
    plt.hist(df["hydration_deficit_pct"], bins=40)
    plt.xlabel("Hydration Deficit (%)"); plt.ylabel("Count"); plt.title("Distribution: Hydration Deficit")
    fig.savefig(fig_path(outdir,"dist_hydration_deficit"), dpi=160); plt.close(fig)

    fig = plt.figure(figsize=(6,4))
    plt.hist(df["caloric_balance"], bins=40)
    plt.xlabel("Caloric Balance (kcal)"); plt.ylabel("Count"); plt.title("Distribution: Caloric Balance")
    fig.savefig(fig_path(outdir,"dist_caloric_balance"), dpi=160); plt.close(fig)

    # 2. Scatter: intensity vs deficit
    fig = plt.figure(figsize=(5,4))
    plt.scatter(df["intensity"], df["hydration_deficit_pct"], s=6, alpha=0.5)
    plt.xlabel("Intensity"); plt.ylabel("Hydration Deficit (%)"); plt.title("Intensity vs Hydration Deficit")
    fig.savefig(fig_path(outdir,"intensity_vs_hdef"), dpi=160); plt.close(fig)

    # 3. Heatmap of correlations
    corr_cols = ["hydration_deficit_pct","caloric_balance","sleep_hours","soreness","temp_c","humidity",
                 "session_mins","intensity","hr_rest","hr_avg","distance_km","work_rate","hr_delta","env_index","calories_in"]
    corr_cols = [c for c in corr_cols if c in df.columns]
    C = df[corr_cols].corr()
    fig = plt.figure(figsize=(8,6))
    plt.imshow(C, interpolation="nearest")
    plt.xticks(range(len(corr_cols)), corr_cols, rotation=45, ha="right")
    plt.yticks(range(len(corr_cols)), corr_cols)
    for i in range(C.shape[0]):
        for j in range(C.shape[1]):
            plt.text(j, i, f"{C.iloc[i,j]:.2f}", ha="center", va="center", fontsize=7)
    plt.title("Correlation Heatmap")
    plt.tight_layout()
    fig.savefig(fig_path(outdir,"corr_heatmap"), dpi=180); plt.close(fig)

    # 4. Full correlation heatmap across all numeric features
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if len(numeric_cols) > 1:
        C_full = df[numeric_cols].corr()
        n_cols = len(numeric_cols)
        fig = plt.figure(figsize=(0.38*n_cols + 4, 0.38*n_cols + 4))
        im = plt.imshow(C_full, interpolation="nearest", cmap="coolwarm", vmin=-1, vmax=1)
        plt.xticks(range(n_cols), numeric_cols, rotation=90, fontsize=7)
        plt.yticks(range(n_cols), numeric_cols, fontsize=7)
        plt.title("Correlation Heatmap (All Numeric Features)")
        plt.colorbar(im, fraction=0.046, pad=0.04)

        annot_size = max(4, min(9, 220 / max(n_cols, 1)))
        for i in range(n_cols):
            for j in range(n_cols):
                val = C_full.iat[i, j]
                txt_color = "white" if abs(val) > 0.55 else "black"
                plt.text(j, i, f"{val:.2f}", ha="center", va="center", fontsize=annot_size, color=txt_color)

        plt.tight_layout()
        fig.savefig(fig_path(outdir, "corr_heatmap_full"), dpi=220); plt.close(fig)
        C_full.to_csv(os.path.join(outdir, "corr_matrix_full.csv"))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=str, required=True)
    ap.add_argument("--outdir", type=str, required=True)
    args = ap.parse_args()
    df = pd.read_csv(args.data)
    run_eda(df, args.outdir)
    print("EDA figures written to", args.outdir)

if __name__ == "__main__":
    main()
