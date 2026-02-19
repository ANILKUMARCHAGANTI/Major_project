
import argparse, os, json
import numpy as np
import pandas as pd
from scipy import stats

def diebold_mariano(e1, e2, h=1, power=2):
    """
    Simple Diebold-Mariano test for equal predictive accuracy.
    e1, e2 are forecast errors (aligned); h is horizon (1 here), power is 1 or 2 for loss.
    Returns DM statistic and p-value (two-sided, normal approximation).
    """
    d = np.abs(e1)**power - np.abs(e2)**power
    d_mean = np.mean(d)
    gamma0 = np.var(d, ddof=1)
    var_d = gamma0
    dm_stat = d_mean / (np.sqrt(var_d / len(d) + 1e-12))
    pval = 2 * (1 - stats.norm.cdf(np.abs(dm_stat)))
    return float(dm_stat), float(pval)

def lins_concordance(y_true, y_pred):
    mu_x = np.mean(y_true); mu_y = np.mean(y_pred)
    s_x2 = np.var(y_true, ddof=1); s_y2 = np.var(y_pred, ddof=1)
    s_xy = np.cov(y_true, y_pred, ddof=1)[0,1]
    ccc = (2*s_xy) / (s_x2 + s_y2 + (mu_x - mu_y)**2 + 1e-12)
    return float(ccc)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preds_index", type=str, required=True)
    ap.add_argument("--novel_preds", type=str, required=True)
    ap.add_argument("--outdir", type=str, required=True)
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    with open(args.preds_index, "r") as f:
        idx = json.load(f)
    novel = pd.read_csv(args.novel_preds)
    y_true = novel["y_true"].values
    y_n = novel["y_pred"].values

    rows = []
    for model, path in idx.items():
        b = pd.read_csv(path)
        m = min(len(b), len(novel))
        yt = b["y_true"].values[:m]
        yb = b["y_pred"].values[:m]
        yn = y_n[:m]
        yref = yt

        e_b = np.abs(yref - yb)
        e_n = np.abs(yref - yn)

        tstat, tp = stats.ttest_rel(e_b, e_n)
        try:
            wstat, wp = stats.wilcoxon(e_b, e_n, zero_method="wilcox", correction=True, alternative="two-sided")
        except Exception:
            wstat, wp = np.nan, np.nan

        dm, dmp = diebold_mariano(yref - yb, yref - yn, h=1, power=2)

        diff = e_b - e_n
        try:
            sh_s, sh_p = stats.shapiro(diff if len(diff) <= 5000 else np.random.choice(diff, 5000, replace=False))
        except Exception:
            sh_s, sh_p = np.nan, np.nan

        ccc_n = lins_concordance(yref, yn)

        rows.append({
            "baseline_model": model,
            "t_paired_t": float(tstat), "p_paired_t": float(tp),
            "w_wilcoxon": float(wstat), "p_wilcoxon": float(wp),
            "dm_stat": dm, "p_dm": dmp,
            "shapiro_stat": float(sh_s), "shapiro_p": float(sh_p),
            "ccc_novel": ccc_n,
            "mae_baseline": float(np.mean(e_b)),
            "mae_novel": float(np.mean(e_n))
        })

    out_df = pd.DataFrame(rows).sort_values(by="mae_novel")
    out_df.to_csv(os.path.join(args.outdir, "stats_pairwise_vs_novel.csv"), index=False)

    mats = []
    names = []
    min_len = None
    for model, path in idx.items():
        b = pd.read_csv(path)
        m = min(len(b), len(novel))
        if min_len is None or m < min_len:
            min_len = m
        yt = b["y_true"].values
        yb = b["y_pred"].values
        mats.append((model, yt, yb))

    if min_len is None or min_len == 0:
        print("Not enough overlapping predictions for Friedman test.")
    else:
        aligned_mats = []
        aligned_names = []
        novel_true = novel["y_true"].values[:min_len]
        novel_abs_err = np.abs(novel_true - y_n[:min_len])
        for model, yt, yb in mats:
            if len(yt) < min_len or len(yb) < min_len:
                continue
            if np.allclose(yt[:min_len], novel_true):
                aligned_mats.append(np.abs(yt[:min_len] - yb[:min_len]))
                aligned_names.append(model)
        aligned_mats.append(novel_abs_err)
        aligned_names.append("HAAE_novel")

        if len(aligned_mats) >= 3:
            from scipy.stats import friedmanchisquare
            stat, p = friedmanchisquare(*aligned_mats)
            with open(os.path.join(args.outdir, "friedman_test.json"), "w") as f:
                json.dump({"k_models": len(aligned_mats), "statistic": float(stat), "pvalue": float(p), "models": aligned_names}, f, indent=2)

    print("Saved extended statistics to", args.outdir)

if __name__ == "__main__":
    main()
