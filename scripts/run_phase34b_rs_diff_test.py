"""
Phase 34b RS Diff-Test -- direct difference test for C6c (SOS + RS_short(63d)>=70) vs its
own complement (SOS + RS_short(63d)<70), both within SOS+Bullish. This exists because C6c is
a SUBSET of C1, and Phase 34's point estimates (10.27% vs 8.35%) had overlapping bootstrap CIs
vs the full random-pool baseline -- exactly the Phase 28 trap ("SOS beats frozen" was overstated
because no direct difference test was run). This script runs that missing test honestly.
"""
import numpy as np
import pandas as pd
from pathlib import Path

REPO_ROOT = Path("c:/Users/surya/Downloads/wyckoff-stock-screener")
DISC_CSV = REPO_ROOT / "data/validation_results/20260826/backtest_returns.csv"
PREDISC_CSV = REPO_ROOT / "data/validation_results/phase22_pre_discovery/phase22_backtest_returns.csv"
NSE_SOURCE_CSV = REPO_ROOT / "data/universe_snapshots/20260823/source.csv"
RS_CSV_DIR = REPO_ROOT / "data/validation_results/phase34_rs_rank_benchmark"
OUT_DIR = RS_CSV_DIR
RANDOM_SEED = 42

df_disc = pd.read_csv(DISC_CSV)
df_predisc = pd.read_csv(PREDISC_CSV)
df_disc["dataset_source"] = "discovery"
df_predisc["dataset_source"] = "pre-discovery"
common_cols = [c for c in df_disc.columns if c in df_predisc.columns]
df_all = pd.concat([df_disc[common_cols], df_predisc[common_cols]], ignore_index=True).drop_duplicates(subset=["signal_date", "symbol"], keep="first").copy()

df_all["above_50dma"] = (df_all["signal_close"] > df_all["dma_50"]).astype(int)
breadth = df_all.groupby("signal_date")["above_50dma"].mean()
regime_map = {dt: "Bullish" if val >= 0.60 else "Bearish" if val < 0.30 else "Sideways" for dt, val in breadth.items()}
df_all["market_regime"] = df_all["signal_date"].map(regime_map)
df_all["signal_date_dt"] = pd.to_datetime(df_all["signal_date"])

df_nse = pd.read_csv(NSE_SOURCE_CSV)
df_nse.columns = df_nse.columns.str.strip()
df_nse["SYMBOL_CLEAN"] = df_nse["SYMBOL"].astype(str).str.strip()
df_nse["LISTING_DATE_PARSED"] = pd.to_datetime(df_nse["DATE OF LISTING"].astype(str).str.strip(), format="%d-%b-%Y", errors="coerce")
listing_map = dict(zip(df_nse["SYMBOL_CLEAN"], df_nse["LISTING_DATE_PARSED"]))
df_all["date_of_listing"] = df_all["symbol"].map(listing_map)
df_all["is_listed_on_or_before_T"] = False
vmask = df_all["date_of_listing"].notna()
df_all.loc[vmask, "is_listed_on_or_before_T"] = df_all.loc[vmask, "signal_date_dt"] >= df_all.loc[vmask, "date_of_listing"]

# Re-derive RS rank exactly as phase34 did (recompute cheaply is expensive; instead reuse phase34's
# raw per-signal RS values by recomputing rank merge from the saved metrics is not possible since
# metrics.csv doesn't carry row-level RS. Recompute via the same routine, importing the module.)
import importlib.util
spec = importlib.util.spec_from_file_location("phase34", REPO_ROOT / "scripts/run_phase34_rs_rank_benchmark.py")
phase34 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(phase34)

unique_dates = pd.DatetimeIndex(sorted(df_all["signal_date_dt"].unique()))
universe_symbols = df_all["symbol"].unique()
df_rs, rs_stats = phase34.compute_rs_rank_features(unique_dates, universe_symbols)
df_rs_merge = df_rs.rename(columns={"checkpoint_date": "signal_date_dt"})[["signal_date_dt", "symbol", "rs_short_rank", "rs_composite_rank"]]
df_all = df_all.merge(df_rs_merge, on=["signal_date_dt", "symbol"], how="left")

df_filtered = df_all[df_all["is_listed_on_or_before_T"] == True].copy()
is_bull = df_filtered["market_regime"] == "Bullish"
is_sos = df_filtered["possible_SOS"] == True
has_rs = df_filtered["rs_short_rank"].notna()

group_a = df_filtered[is_bull & is_sos & has_rs & (df_filtered["rs_short_rank"] >= 70)]  # C6c
group_b = df_filtered[is_bull & is_sos & has_rs & (df_filtered["rs_short_rank"] < 70)]   # complement

col = "fwd_net_ret_60d"
a_vals = group_a[col].dropna()
b_vals = group_b[col].dropna()
print(f"Group A (SOS+RS>=70): N={len(a_vals)}, mean={a_vals.mean():.2f}%, median={a_vals.median():.2f}%")
print(f"Group B (SOS+RS<70):  N={len(b_vals)}, mean={b_vals.mean():.2f}%, median={b_vals.median():.2f}%")
raw_diff = a_vals.mean() - b_vals.mean()
print(f"Raw mean difference (A - B): {raw_diff:.2f}%")

# --- Unpaired bootstrap CI on the difference ---
np.random.seed(RANDOM_SEED)
a_arr, b_arr = a_vals.values, b_vals.values
boot_diffs_unpaired = []
for _ in range(5000):
    a_s = np.random.choice(a_arr, size=len(a_arr), replace=True)
    b_s = np.random.choice(b_arr, size=len(b_arr), replace=True)
    boot_diffs_unpaired.append(a_s.mean() - b_s.mean())
ci_lo_unpaired = np.percentile(boot_diffs_unpaired, 2.5)
ci_hi_unpaired = np.percentile(boot_diffs_unpaired, 97.5)
print(f"\nUnpaired bootstrap CI on diff: [{ci_lo_unpaired:.2f}%, {ci_hi_unpaired:.2f}%] {'CONTAINS 0 -> NOT_ESTABLISHED' if ci_lo_unpaired <= 0 <= ci_hi_unpaired else 'EXCLUDES 0 -> SIGNIFICANT'}")

# --- Paired-by-date block bootstrap CI on the difference ---
a_by_date = {dt: g[col].dropna().values for dt, g in group_a.groupby("signal_date")}
b_by_date = {dt: g[col].dropna().values for dt, g in group_b.groupby("signal_date")}
common_dates = sorted(set(a_by_date.keys()) & set(b_by_date.keys()))
print(f"\nDates with BOTH groups present: {len(common_dates)} (out of A:{len(a_by_date)}, B:{len(b_by_date)})")

np.random.seed(RANDOM_SEED)
boot_diffs_paired = []
for _ in range(5000):
    sampled_dates = np.random.choice(common_dates, size=len(common_dates), replace=True)
    a_chunks = [a_by_date[d] for d in sampled_dates]
    b_chunks = [b_by_date[d] for d in sampled_dates]
    a_mean = np.mean(np.concatenate(a_chunks))
    b_mean = np.mean(np.concatenate(b_chunks))
    boot_diffs_paired.append(a_mean - b_mean)
ci_lo_paired = np.percentile(boot_diffs_paired, 2.5)
ci_hi_paired = np.percentile(boot_diffs_paired, 97.5)
print(f"Paired-by-date bootstrap CI on diff: [{ci_lo_paired:.2f}%, {ci_hi_paired:.2f}%] {'CONTAINS 0 -> NOT_ESTABLISHED' if ci_lo_paired <= 0 <= ci_hi_paired else 'EXCLUDES 0 -> SIGNIFICANT'}")

# --- Permutation test: shuffle A/B labels within each common date, build null of mean diff ---
np.random.seed(RANDOM_SEED)
perm_diffs = []
pooled_by_date = {}
for d in common_dates:
    pooled_by_date[d] = np.concatenate([a_by_date[d], b_by_date[d]])

n_a_by_date = {d: len(a_by_date[d]) for d in common_dates}
for _ in range(2000):
    perm_a_all, perm_b_all = [], []
    for d in common_dates:
        pooled = pooled_by_date[d].copy()
        np.random.shuffle(pooled)
        n_a = n_a_by_date[d]
        perm_a_all.append(pooled[:n_a])
        perm_b_all.append(pooled[n_a:])
    perm_a_mean = np.mean(np.concatenate(perm_a_all))
    perm_b_mean = np.mean(np.concatenate(perm_b_all))
    perm_diffs.append(perm_a_mean - perm_b_mean)
perm_diffs = np.array(perm_diffs)
p_val = min(np.sum(perm_diffs >= raw_diff), np.sum(perm_diffs <= raw_diff)) / len(perm_diffs) * 2.0
p_val = min(1.0, p_val)
print(f"\nWithin-date label-permutation test p-value on (A-B) diff: {p_val:.4f} {'SIGNIFICANT' if p_val < 0.05 else 'NOT_SIGNIFICANT'}")

# Save results
result = {
    "group_a_n": int(len(a_vals)), "group_a_mean": float(a_vals.mean()), "group_a_median": float(a_vals.median()),
    "group_b_n": int(len(b_vals)), "group_b_mean": float(b_vals.mean()), "group_b_median": float(b_vals.median()),
    "raw_diff": float(raw_diff),
    "unpaired_ci_low": float(ci_lo_unpaired), "unpaired_ci_high": float(ci_hi_unpaired),
    "paired_ci_low": float(ci_lo_paired), "paired_ci_high": float(ci_hi_paired),
    "common_dates": len(common_dates),
    "permutation_p_value": float(p_val),
    "verdict_unpaired": "NOT_ESTABLISHED" if ci_lo_unpaired <= 0 <= ci_hi_unpaired else "SIGNIFICANT",
    "verdict_paired": "NOT_ESTABLISHED" if ci_lo_paired <= 0 <= ci_hi_paired else "SIGNIFICANT",
    "verdict_permutation": "NOT_SIGNIFICANT" if p_val >= 0.05 else "SIGNIFICANT",
}
import json
with open(OUT_DIR / "phase34b_diff_test_result.json", "w") as f:
    json.dump(result, f, indent=2)
print("\nSaved phase34b_diff_test_result.json")
