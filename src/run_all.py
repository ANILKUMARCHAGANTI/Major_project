import argparse, os, json, subprocess, sys, shutil
import pandas as pd
from preprocess import engineer
from models_baselines import train_models
from novel_haae import train_haae

def run_cmd(cmd):
    print(">>", " ".join(cmd))
    r = subprocess.run(cmd, check=True)
    return r.returncode

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=str, required=True)
    ap.add_argument("--outdir", type=str, required=True)
    ap.add_argument("--target", type=str, default="hydration_deficit_pct")
    ap.add_argument("--epochs", type=int, default=20)  # reserved for extension
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    figs = os.path.join(args.outdir, "figures"); os.makedirs(figs, exist_ok=True)
    tabs = os.path.join(args.outdir, "tables"); os.makedirs(tabs, exist_ok=True)
    mods = os.path.join(args.outdir, "models"); os.makedirs(mods, exist_ok=True)

    # 1) Preprocess file (in-place)
    df = pd.read_csv(args.data)
    df = engineer(df, target_cols=[args.target])
    preproc_path = os.path.join(args.outdir, "preprocessed.csv")
    df.to_csv(preproc_path, index=False)

    # 2) EDA
    run_cmd([sys.executable, "src/eda.py", "--data", preproc_path, "--outdir", figs])

    # 3) Baselines
    base_dir = os.path.join(args.outdir, "baselines")
    os.makedirs(base_dir, exist_ok=True)
    rows = train_models(df, args.target, base_dir)
    pd.DataFrame(rows).to_csv(os.path.join(tabs, "baseline_metrics.csv"), index=False)

    # create preds index JSON (model name -> preds path) for stats_validate
    preds_index = {}
    for fn in os.listdir(base_dir):
        if fn.endswith("_preds.csv"):
            model_name = fn.replace("_preds.csv", "")
            preds_index[model_name] = os.path.join(base_dir, fn)
    preds_index_path = os.path.join(base_dir, "preds_index.json")
    with open(preds_index_path, "w") as f:
        json.dump(preds_index, f)

    # Pick GradientBoosting as baseline for stats
    baseline_preds = os.path.join(base_dir, "GradientBoosting_preds.csv")

    # 4) Novel HAAE
    novel_dir = os.path.join(args.outdir, "haae")
    os.makedirs(novel_dir, exist_ok=True)
    m = train_haae(df, args.target, novel_dir)
    with open(os.path.join(tabs, "haae_metrics.json"), "w") as f:
        json.dump(m, f, indent=2)

    # 5) Stats validation
    run_cmd([sys.executable, "src/stats_validate.py",
        "--preds_index", preds_index_path,
        "--novel_preds", os.path.join(novel_dir, "HAAE_preds.csv"),
        "--outdir", tabs])

    print("All done. See outputs in", args.outdir)

if __name__ == "__main__":
    main()
