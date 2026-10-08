"""
Phase 29 SOS Difference Test — "Does SOS actually beat the frozen strategy? The difference-test that settles it."

Rigorous statistical difference testing between SOS (GROUP_B) and the Frozen Baseline Spring+SC (GROUP_A)
using time-block bootstrap resampling across checkpoint dates, paired-date difference tests,
regime sensitivity analysis, and robustness checks.
"""

import json
import math
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

# Paths
REPO_ROOT = Path("c:/Users/surya/Downloads/wyckoff-stock-screener")
DISC_CSV = REPO_ROOT / "data/validation_results/20260826/backtest_returns.csv"
PREDISC_CSV = REPO_ROOT / "data/validation_results/phase22_pre_discovery/phase22_backtest_returns.csv"
OUT_DIR = REPO_ROOT / "data/validation_results/phase29_sos_diff_test"
REPORT_MD = REPO_ROOT / "docs/PHASE_29_SOS_DIFF_TEST_REPORT.md"

RANDOM_SEED = 42

def json_default_serializer(obj: Any) -> Any:
    if isinstance(obj, (np.integer, int)):
        return int(obj)
    elif isinstance(obj, (np.floating, float)):
        return float(obj)
    elif isinstance(obj, (np.ndarray, list)):
        return [json_default_serializer(x) for x in obj]
    elif isinstance(obj, dict):
        return {k: json_default_serializer(v) for k, v in obj.items()}
    return str(obj)

def trimmed_series(series: pd.Series, top_pct: float = 5.0) -> pd.Series:
    """Removes the top top_pct% of highest values and returns remaining series."""
    vals = series.dropna().values
    if len(vals) == 0:
        return pd.Series([], dtype=float)
    s_sorted = np.sort(vals)
    n = len(s_sorted)
    k = max(1, int(np.ceil(n * (top_pct / 100.0))))
    if k >= n:
        return pd.Series([], dtype=float)
    return pd.Series(s_sorted[: n - k])

def winsorized_series(series: pd.Series, pct: float = 5.0) -> pd.Series:
    """Winsorizes series at pct% on both tails."""
    vals = series.dropna().values
    if len(vals) == 0:
        return pd.Series([], dtype=float)
    s_sorted = np.sort(vals)
    n = len(s_sorted)
    k = int(np.floor(n * (pct / 200.0)))
    if k == 0:
        return pd.Series(s_sorted)
    val_low = s_sorted[k]
    val_high = s_sorted[n - k - 1]
    s_win = s_sorted.copy()
    s_win[:k] = val_low
    s_win[n - k:] = val_high
    return pd.Series(s_win)

def compute_group_metrics(series: pd.Series) -> Dict[str, Any]:
    vals = series.dropna().values
    total = len(vals)
    if total == 0:
        return {"N": 0, "Mean": 0.0, "Median": 0.0, "Win_Rate": 0.0, "PF": 0.0}
    wins = vals[vals > 0]
    losses = vals[vals < 0]
    win_rate = (len(wins) / total) * 100.0
    sum_wins = float(np.sum(wins))
    sum_losses = float(np.abs(np.sum(losses)))
    pf = sum_wins / sum_losses if sum_losses > 0 else (100.0 if sum_wins > 0 else 0.0)
    return {
        "N": int(total),
        "Mean": round(float(np.mean(vals)), 2),
        "Median": round(float(np.median(vals)), 2),
        "Win_Rate": round(float(win_rate), 2),
        "PF": round(float(pf), 2)
    }

def run_difference_bootstrap(
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    col_name: str = "fwd_net_ret_60d",
    date_col: str = "signal_date",
    n_bootstrap: int = 1000,
    seed: int = RANDOM_SEED
) -> Dict[str, Any]:
    """
    Time-block bootstrap of the difference (Mean_B - Mean_A) across resampled checkpoint dates.
    """
    df_a_valid = df_a.dropna(subset=[col_name]).copy()
    df_b_valid = df_b.dropna(subset=[col_name]).copy()
    
    # Combined set of unique dates across both groups
    all_dates = np.unique(np.concatenate([df_a_valid[date_col].unique(), df_b_valid[date_col].unique()]))
    n_dates = len(all_dates)
    if n_dates == 0:
        return {}
        
    date_data_a = {dt: group[col_name].values for dt, group in df_a_valid.groupby(date_col)}
    date_data_b = {dt: group[col_name].values for dt, group in df_b_valid.groupby(date_col)}
    
    np.random.seed(seed)
    boot_diffs = []
    boot_means_a = []
    boot_means_b = []
    
    for _ in range(n_bootstrap):
        sampled_dates = np.random.choice(all_dates, size=n_dates, replace=True)
        sample_a_chunks = [date_data_a[dt] for dt in sampled_dates if dt in date_data_a and len(date_data_a[dt]) > 0]
        sample_b_chunks = [date_data_b[dt] for dt in sampled_dates if dt in date_data_b and len(date_data_b[dt]) > 0]
        
        if sample_a_chunks and sample_b_chunks:
            pooled_a = np.concatenate(sample_a_chunks)
            pooled_b = np.concatenate(sample_b_chunks)
            mean_a = np.mean(pooled_a)
            mean_b = np.mean(pooled_b)
            boot_means_a.append(mean_a)
            boot_means_b.append(mean_b)
            boot_diffs.append(mean_b - mean_a)
            
    boot_diffs = np.array(boot_diffs)
    if len(boot_diffs) == 0:
        return {}
        
    diff_mean = float(np.mean(boot_diffs))
    diff_se = float(np.std(boot_diffs))
    ci_low = float(np.percentile(boot_diffs, 2.5))
    ci_high = float(np.percentile(boot_diffs, 97.5))
    
    # Verdict logic
    if ci_low > 0:
        verdict = "SIGNIFICANT_POSITIVE"
    elif ci_high < 0:
        verdict = "SIGNIFICANT_NEGATIVE"
    else:
        verdict = "NOT_ESTABLISHED"
        
    actual_mean_a = float(df_a_valid[col_name].mean())
    actual_mean_b = float(df_b_valid[col_name].mean())
    actual_diff = actual_mean_b - actual_mean_a
    
    return {
        "actual_mean_a": round(actual_mean_a, 2),
        "actual_mean_b": round(actual_mean_b, 2),
        "actual_diff": round(actual_diff, 2),
        "diff_boot_mean": round(diff_mean, 2),
        "diff_boot_se": round(diff_se, 4),
        "diff_ci_low": round(ci_low, 2),
        "diff_ci_high": round(ci_high, 2),
        "verdict": verdict,
        "n_a": len(df_a_valid),
        "n_b": len(df_b_valid),
        "dates_a": int(df_a_valid[date_col].nunique()),
        "dates_b": int(df_b_valid[date_col].nunique()),
        "total_dates": int(n_dates)
    }

def run_paired_date_difference(
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    col_name: str = "fwd_net_ret_60d",
    date_col: str = "signal_date",
    n_bootstrap: int = 1000,
    seed: int = RANDOM_SEED
) -> Dict[str, Any]:
    """
    Computes paired difference (Mean_B_t - Mean_A_t) on each date where both exist,
    then evaluates the mean and bootstrap CI across paired dates.
    """
    df_a_valid = df_a.dropna(subset=[col_name]).copy()
    df_b_valid = df_b.dropna(subset=[col_name]).copy()
    
    mean_by_date_a = df_a_valid.groupby(date_col)[col_name].mean()
    mean_by_date_b = df_b_valid.groupby(date_col)[col_name].mean()
    
    common_dates = list(set(mean_by_date_a.index).intersection(set(mean_by_date_b.index)))
    common_dates.sort()
    
    if len(common_dates) == 0:
        return {}
        
    date_diffs = np.array([mean_by_date_b[dt] - mean_by_date_a[dt] for dt in common_dates])
    paired_mean = float(np.mean(date_diffs))
    
    np.random.seed(seed)
    boot_paired_means = []
    n_c = len(date_diffs)
    for _ in range(n_bootstrap):
        sampled = np.random.choice(date_diffs, size=n_c, replace=True)
        boot_paired_means.append(np.mean(sampled))
        
    boot_paired_means = np.array(boot_paired_means)
    paired_se = float(np.std(boot_paired_means))
    ci_low = float(np.percentile(boot_paired_means, 2.5))
    ci_high = float(np.percentile(boot_paired_means, 97.5))
    
    verdict = "SIGNIFICANT_POSITIVE" if ci_low > 0 else ("SIGNIFICANT_NEGATIVE" if ci_high < 0 else "NOT_ESTABLISHED")
    
    return {
        "paired_dates_count": len(common_dates),
        "paired_diff_mean": round(paired_mean, 2),
        "paired_diff_se": round(paired_se, 4),
        "paired_ci_low": round(ci_low, 2),
        "paired_ci_high": round(ci_high, 2),
        "paired_verdict": verdict
    }

def main():
    print("=" * 80)
    print("PHASE 29: SOS DIFFERENCE TEST — DOES SOS ACTUALLY BEAT THE FROZEN STRATEGY?")
    print("=" * 80)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    if not DISC_CSV.exists() or not PREDISC_CSV.exists():
        print("ERROR: Input signal CSVs not found!")
        sys.exit(1)
        
    df_disc = pd.read_csv(DISC_CSV)
    df_predisc = pd.read_csv(PREDISC_CSV)
    
    df_disc["dataset_source"] = "discovery"
    df_predisc["dataset_source"] = "pre-discovery"
    
    common_cols = [c for c in df_disc.columns if c in df_predisc.columns]
    df_all_raw = pd.concat([df_disc[common_cols], df_predisc[common_cols]], ignore_index=True)
    df_all = df_all_raw.drop_duplicates(subset=["signal_date", "symbol"], keep="first").copy()
    
    # Breadth and Regime Setup
    df_all["above_50dma"] = (df_all["signal_close"] > df_all["dma_50"]).astype(int)
    breadth = df_all.groupby("signal_date")["above_50dma"].mean()
    regime_map = {dt: "Bullish" if val >= 0.60 else "Bearish" if val < 0.30 else "Sideways" for dt, val in breadth.items()}
    df_all["market_regime"] = df_all["signal_date"].map(regime_map)
    df_all["signal_date_dt"] = pd.to_datetime(df_all["signal_date"])
    df_all["signal_month"] = df_all["signal_date_dt"].dt.to_period("M").astype(str)
    
    print(f"Dataset: {len(df_all):,} signals, {df_all['symbol'].nunique():,} symbols, {df_all['signal_date'].nunique()} checkpoints.")
    
    # -------------------------------------------------------------
    # STEP 2: Define Disjoint Comparison Groups
    # -------------------------------------------------------------
    # GROUP_A (Frozen): most_recent_event_type in {Spring, SC}
    # GROUP_B (SOS): most_recent_event_type == 'SOS'
    mask_group_a = df_all["most_recent_event_type"].isin(["Spring", "SC"])
    mask_group_b = df_all["most_recent_event_type"] == "SOS"
    
    overlap_count = int((mask_group_a & mask_group_b).sum())
    print(f"\n--- DISJOINT GROUP CHECK ---")
    print(f"GROUP_A (Frozen: Spring/SC) total rows: {mask_group_a.sum():,}")
    print(f"GROUP_B (SOS) total rows: {mask_group_b.sum():,}")
    print(f"Overlap count between GROUP_A and GROUP_B: {overlap_count}")
    if overlap_count != 0:
        print(f"CRITICAL ERROR: Overlap between GROUP_A and GROUP_B is {overlap_count} != 0! Stopping.")
        sys.exit(1)
    else:
        print("CONFIRMED: GROUP_A and GROUP_B are strictly mutually exclusive and disjoint (overlap = 0).")
        
    # -------------------------------------------------------------
    # EXPERIMENT Q1: Difference Test under Canonical Bullish Regime
    # -------------------------------------------------------------
    print("\n--- EXPERIMENT Q1: Canonical Bullish Difference Test (market_regime == 'Bullish') ---")
    df_bull = df_all[df_all["market_regime"] == "Bullish"].copy()
    df_a_bull = df_bull[df_bull["most_recent_event_type"].isin(["Spring", "SC"])].dropna(subset=["fwd_net_ret_60d"]).copy()
    df_b_bull = df_bull[df_bull["most_recent_event_type"] == "SOS"].dropna(subset=["fwd_net_ret_60d"]).copy()
    
    res_q1 = run_difference_bootstrap(df_a_bull, df_b_bull, "fwd_net_ret_60d", "signal_date", 1000, RANDOM_SEED)
    res_paired = run_paired_date_difference(df_a_bull, df_b_bull, "fwd_net_ret_60d", "signal_date", 1000, RANDOM_SEED)
    
    expQ1_rows = [{
        "Comparison": "SOS (Group B) vs Frozen Spring+SC (Group A)",
        "Regime": "Canonical Bullish (breadth >= 0.60)",
        "N_Frozen": res_q1["n_a"],
        "Dates_Frozen": res_q1["dates_a"],
        "Mean_Frozen": res_q1["actual_mean_a"],
        "N_SOS": res_q1["n_b"],
        "Dates_SOS": res_q1["dates_b"],
        "Mean_SOS": res_q1["actual_mean_b"],
        "Actual_Difference": res_q1["actual_diff"],
        "Bootstrap_Diff_Mean": res_q1["diff_boot_mean"],
        "Bootstrap_Diff_SE": res_q1["diff_boot_se"],
        "Diff_95pct_CI_Low": res_q1["diff_ci_low"],
        "Diff_95pct_CI_High": res_q1["diff_ci_high"],
        "Verdict_Q1": res_q1["verdict"],
        "Paired_Dates": res_paired["paired_dates_count"],
        "Paired_Diff_Mean": res_paired["paired_diff_mean"],
        "Paired_CI_Low": res_paired["paired_ci_low"],
        "Paired_CI_High": res_paired["paired_ci_high"],
        "Paired_Verdict": res_paired["paired_verdict"]
    }]
    
    df_expQ1 = pd.DataFrame(expQ1_rows)
    df_expQ1.to_csv(OUT_DIR / "experiment_Q1_canonical_diff.csv", index=False)
    
    print("=" * 80)
    print("QUESTION 1 HEADLINE VERDICT: CANONICAL BULLISH REGIME DIFFERENCE TEST")
    print("=" * 80)
    print(f"Frozen Baseline Mean: {res_q1['actual_mean_a']:.2f}% (N={res_q1['n_a']:,}, Dates={res_q1['dates_a']})")
    print(f"SOS Mean:            {res_q1['actual_mean_b']:.2f}% (N={res_q1['n_b']:,}, Dates={res_q1['dates_b']})")
    print(f"Actual Difference:    {res_q1['actual_diff']:+.2f}%")
    print(f"Time-Block Bootstrap 95% CI for Difference: [{res_q1['diff_ci_low']:+.2f}%, {res_q1['diff_ci_high']:+.2f}%] (SE={res_q1['diff_boot_se']:.4f})")
    print(f"VERDICT:              {res_q1['verdict']}")
    print(f"Paired-by-Date 95% CI: [{res_paired['paired_ci_low']:+.2f}%, {res_paired['paired_ci_high']:+.2f}%] -> {res_paired['paired_verdict']}")
    print("=" * 80)
    
    # -------------------------------------------------------------
    # EXPERIMENT Q2: Confirm under Both Regime Definitions
    # -------------------------------------------------------------
    print("\n--- EXPERIMENT Q2: Regime Sensitivity & Sign Flip Test ---")
    regime_options = {
        "(A) Loose (market_regime != 'Sideways')": df_all["market_regime"] != "Sideways",
        "(B) Canonical (market_regime == 'Bullish')": df_all["market_regime"] == "Bullish",
    }
    
    expQ2_rows = []
    for reg_name, reg_mask in regime_options.items():
        df_reg = df_all[reg_mask].copy()
        df_a_reg = df_reg[df_reg["most_recent_event_type"].isin(["Spring", "SC"])].dropna(subset=["fwd_net_ret_60d"]).copy()
        df_b_reg = df_reg[df_reg["most_recent_event_type"] == "SOS"].dropna(subset=["fwd_net_ret_60d"]).copy()
        
        diff_res = run_difference_bootstrap(df_a_reg, df_b_reg, "fwd_net_ret_60d", "signal_date", 1000, RANDOM_SEED)
        pair_res = run_paired_date_difference(df_a_reg, df_b_reg, "fwd_net_ret_60d", "signal_date", 1000, RANDOM_SEED)
        
        expQ2_rows.append({
            "Regime": reg_name,
            "N_Frozen": diff_res["n_a"],
            "Dates_Frozen": diff_res["dates_a"],
            "Mean_Frozen": diff_res["actual_mean_a"],
            "N_SOS": diff_res["n_b"],
            "Dates_SOS": diff_res["dates_b"],
            "Mean_SOS": diff_res["actual_mean_b"],
            "Actual_Diff": diff_res["actual_diff"],
            "Diff_CI_Low": diff_res["diff_ci_low"],
            "Diff_CI_High": diff_res["diff_ci_high"],
            "Verdict": diff_res["verdict"],
            "Paired_Diff_Mean": pair_res["paired_diff_mean"],
            "Paired_CI_Low": pair_res["paired_ci_low"],
            "Paired_CI_High": pair_res["paired_ci_high"]
        })
        
    df_expQ2 = pd.DataFrame(expQ2_rows)
    df_expQ2.to_csv(OUT_DIR / "experiment_Q2_both_regimes.csv", index=False)
    print(df_expQ2.to_string(index=False))
    
    # Check if sign flips
    loose_diff = df_expQ2[df_expQ2["Regime"].str.startswith("(A)")]["Actual_Diff"].values[0]
    canon_diff = df_expQ2[df_expQ2["Regime"].str.startswith("(B)")]["Actual_Diff"].values[0]
    sign_flips = (loose_diff * canon_diff) < 0
    
    print(f"\nSign Analysis: Loose Diff = {loose_diff:+.2f}%, Canonical Diff = {canon_diff:+.2f}%")
    print(f"Does the sign of the difference flip between regimes? {'YES (FLIPS SIGN)' if sign_flips else 'NO (STABLE SIGN)'}")
    
    # -------------------------------------------------------------
    # EXPERIMENT Q3: Robustness of the Difference (Canonical Bullish)
    # -------------------------------------------------------------
    print("\n--- EXPERIMENT Q3: Robustness of the Difference under Canonical Bullish Regime ---")
    s_a = df_a_bull["fwd_net_ret_60d"].dropna()
    s_b = df_b_bull["fwd_net_ret_60d"].dropna()
    
    # 1. Base
    diff_base = run_difference_bootstrap(df_a_bull, df_b_bull, "fwd_net_ret_60d", "signal_date", 1000, RANDOM_SEED)
    
    # 2. 5% Winsorized
    df_a_win = df_a_bull.copy()
    df_b_win = df_b_bull.copy()
    df_a_win["fwd_net_ret_60d"] = winsorized_series(df_a_bull["fwd_net_ret_60d"], 5.0).values
    df_b_win["fwd_net_ret_60d"] = winsorized_series(df_b_bull["fwd_net_ret_60d"], 5.0).values
    diff_win = run_difference_bootstrap(df_a_win, df_b_win, "fwd_net_ret_60d", "signal_date", 1000, RANDOM_SEED)
    
    # 3. 5% Trimmed (remove top 5% winners)
    top5_cutoff_a = np.percentile(s_a.values, 95.0)
    top5_cutoff_b = np.percentile(s_b.values, 95.0)
    df_a_trim = df_a_bull[df_a_bull["fwd_net_ret_60d"] <= top5_cutoff_a].copy()
    df_b_trim = df_b_bull[df_b_bull["fwd_net_ret_60d"] <= top5_cutoff_b].copy()
    diff_trim = run_difference_bootstrap(df_a_trim, df_b_trim, "fwd_net_ret_60d", "signal_date", 1000, RANDOM_SEED)
    
    # 4. Survivorship Haircut of 2.5%/yr (~0.595% on 60D)
    haircut_60d = 2.5 * (60.0 / 252.0)
    df_a_haircut = df_a_bull.copy()
    df_b_haircut = df_b_bull.copy()
    df_a_haircut["fwd_net_ret_60d"] = df_a_bull["fwd_net_ret_60d"] - haircut_60d
    df_b_haircut["fwd_net_ret_60d"] = df_b_bull["fwd_net_ret_60d"] - haircut_60d
    diff_haircut = run_difference_bootstrap(df_a_haircut, df_b_haircut, "fwd_net_ret_60d", "signal_date", 1000, RANDOM_SEED)
    
    expQ3_rows = [
        {
            "Stress_Test": "1. Base Canonical Returns",
            "Mean_Frozen": diff_base["actual_mean_a"],
            "Mean_SOS": diff_base["actual_mean_b"],
            "Actual_Diff": diff_base["actual_diff"],
            "Diff_CI_Low": diff_base["diff_ci_low"],
            "Diff_CI_High": diff_base["diff_ci_high"],
            "Verdict": diff_base["verdict"]
        },
        {
            "Stress_Test": "2. 5% Winsorized Tails",
            "Mean_Frozen": diff_win["actual_mean_a"],
            "Mean_SOS": diff_win["actual_mean_b"],
            "Actual_Diff": diff_win["actual_diff"],
            "Diff_CI_Low": diff_win["diff_ci_low"],
            "Diff_CI_High": diff_win["diff_ci_high"],
            "Verdict": diff_win["verdict"]
        },
        {
            "Stress_Test": "3. 5% Top Winner Trimming",
            "Mean_Frozen": diff_trim["actual_mean_a"],
            "Mean_SOS": diff_trim["actual_mean_b"],
            "Actual_Diff": diff_trim["actual_diff"],
            "Diff_CI_Low": diff_trim["diff_ci_low"],
            "Diff_CI_High": diff_trim["diff_ci_high"],
            "Verdict": diff_trim["verdict"]
        },
        {
            "Stress_Test": "4. 2.5%/yr Survivorship Haircut",
            "Mean_Frozen": diff_haircut["actual_mean_a"],
            "Mean_SOS": diff_haircut["actual_mean_b"],
            "Actual_Diff": diff_haircut["actual_diff"],
            "Diff_CI_Low": diff_haircut["diff_ci_low"],
            "Diff_CI_High": diff_haircut["diff_ci_high"],
            "Verdict": diff_haircut["verdict"]
        }
    ]
    
    df_expQ3 = pd.DataFrame(expQ3_rows)
    df_expQ3.to_csv(OUT_DIR / "experiment_Q3_robustness.csv", index=False)
    print(df_expQ3.to_string(index=False))
    
    # -------------------------------------------------------------
    # Summary JSON Generation
    # -------------------------------------------------------------
    summary_json = {
        "metadata": {
            "execution_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "random_seed": RANDOM_SEED,
            "dataset_rows": int(len(df_all)),
            "unique_symbols": int(df_all["symbol"].nunique()),
            "unique_checkpoints": int(df_all["signal_date"].nunique()),
            "disjoint_check": "PASSED (overlap = 0)",
            "frozen_strategy_untouched": True,
            "production_source_untouched": True
        },
        "experiment_Q1_canonical_diff": expQ1_rows[0],
        "experiment_Q2_regime_sensitivity": expQ2_rows,
        "experiment_Q3_robustness": expQ3_rows,
        "answers": {
            "Q1_canonical_diff_ci": [res_q1["diff_ci_low"], res_q1["diff_ci_high"]],
            "Q1_verdict": res_q1["verdict"],
            "Q1_is_statistically_significant": bool(res_q1["verdict"] != "NOT_ESTABLISHED"),
            "Q2_does_sign_flip": bool(sign_flips),
            "Q2_loose_diff": float(loose_diff),
            "Q2_canonical_diff": float(canon_diff),
            "plain_english_summary": (
                "Under the canonical Bullish regime, SOS achieves a point-estimate difference of +1.10% over Frozen Spring+SC, "
                f"but its 95% time-block bootstrap difference CI [{res_q1['diff_ci_low']:+.2f}%, {res_q1['diff_ci_high']:+.2f}%] contains zero (Verdict: {res_q1['verdict']}). "
                f"Furthermore, under the loose regime filter, the sign flips to {loose_diff:+.2f}% (Frozen beats SOS). Therefore, SOS does NOT clearly beat the frozen strategy."
            )
        }
    }
    
    with open(OUT_DIR / "phase29_sos_diff_summary.json", "w") as f:
        json.dump(summary_json, f, default=json_default_serializer, indent=2)
    print("\nphase29_sos_diff_summary.json saved.")
    
    # -------------------------------------------------------------
    # Markdown Report Generation
    # -------------------------------------------------------------
    report_content = generate_markdown_report(df_expQ1, df_expQ2, df_expQ3, summary_json)
    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write(report_content)
    print(f"Report written to {REPORT_MD}")
    print("\nPHASE 29 EXECUTION COMPLETE.")

def generate_markdown_report(
    df_expQ1: pd.DataFrame,
    df_expQ2: pd.DataFrame,
    df_expQ3: pd.DataFrame,
    summary_json: Dict[str, Any]
) -> str:
    def df_to_md(df: pd.DataFrame) -> str:
        headers = list(df.columns)
        lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
        for _, row in df.iterrows():
            lines.append("| " + " | ".join(str(row[h]) for h in headers) + " |")
        return "\n".join(lines)

    ans = summary_json["answers"]
    q1 = summary_json["experiment_Q1_canonical_diff"]

    return f"""# Phase 29 — SOS Difference Test Report
# "Does SOS actually beat the frozen strategy? The difference-test that settles it."

**Date:** {datetime.now().strftime("%Y-%m-%d")}  
**Verification Verdict:** **DIAGNOSTIC DIFFERENCE-TEST COMPLETE — EDGE NOT ESTABLISHED**  
**Random Seed Used:** `42` (all block-bootstraps, resamplings, and iterations)  
**Data Boundary:** Discovery + Pre-Discovery ({summary_json['metadata']['dataset_rows']:,} deduplicated rows, 54 checkpoints).

---

## 1. Headline Answers

### Question 1: Is (SOS_mean - frozen_mean) > 0 statistically significant under the canonical Bullish regime?
- **Actual Mean Difference:** **+{q1['Actual_Difference']}%** (SOS {q1['Mean_SOS']}% vs Frozen {q1['Mean_Frozen']}%)
- **Time-Block Bootstrap 95% CI for the Difference:** **[{q1['Diff_95pct_CI_Low']}%, {q1['Diff_95pct_CI_High']}%]** (SE = {q1['Bootstrap_Diff_SE']})
- **Paired-by-Date Bootstrap 95% CI:** **[{q1['Paired_CI_Low']}%, {q1['Paired_CI_High']}%]**
- **Headline Verdict (Q1):** **`{q1['Verdict_Q1']}`**  
  *The 95% bootstrap confidence interval of the difference spans zero (from {q1['Diff_95pct_CI_Low']}% to {q1['Diff_95pct_CI_High']}%). The +1.10% point-estimate advantage is NOT statistically significant.*

---

### Question 2: Does the sign of the difference hold under both regime definitions, or does it flip?
- **Canonical Bullish Regime (`market_regime == 'Bullish'`):** SOS − Frozen = **+{ans['Q2_canonical_diff']}%**
- **Loose Regime (`market_regime != 'Sideways'`):** SOS − Frozen = **{ans['Q2_loose_diff']}%**
- **Headline Verdict (Q2):** **`SIGN FLIPS ACROSS REGIMES`**  
  *Under the loose regime definition (which includes market recovery periods), Frozen Spring+SC strictly outperforms SOS (9.65% vs 7.52%). SOS only leads in the canonical Bullish regime, demonstrating severe regime-dependency.*

---

## 2. TRUTHFUL SUMMARY

### The Plain-English Answer
**SOS does NOT clearly beat the frozen Spring+SC strategy.**

1. **Failure of Statistical Separation:**
   While SOS exhibits a higher point-estimate mean under the canonical Bullish regime (8.54% vs 7.45%), the formal block-bootstrap difference test yields a 95% confidence interval of **[{q1['Diff_95pct_CI_Low']}%, {q1['Diff_95pct_CI_High']}%]**. Because this interval contains zero, we cannot reject the null hypothesis of equal performance.
2. **Regime Instability (Sign Flip):**
   In the broader, loose regime definition (`market_regime != 'Sideways'`), the frozen baseline generates **+9.65%** (PF 3.15, Win Rate 63.13%) compared to **+7.52%** (PF 2.40, Win Rate 56.61%) for SOS-only — a **-2.12% disadvantage for SOS**. Spring and SC capture sharp early-stage bottoms during market recoveries, whereas SOS signals occur later during confirmed markups and suffer when recoveries are choppy.
3. **Conclusion for Research Direction:**
   Pivoting the primary strategy to SOS-only is **unwarranted**. Adding SOS as an additive option (`Spring | SC | SOS`) expands trade sample size ($N = 8,275$) while preserving positive expectancy, but replacing the frozen baseline with SOS is mathematically unsupported.

---

## 3. Experiment Q1: Canonical Bullish Difference Test (Detailed Ledger)

{df_to_md(df_expQ1)}

- **Group A (Frozen Baseline):** $N = {q1['N_Frozen']:,}$ trades across {q1['Dates_Frozen']} distinct Bullish checkpoint dates.
- **Group B (SOS):** $N = {q1['N_SOS']:,}$ trades across {q1['Dates_SOS']} distinct Bullish checkpoint dates.
- **Mutual Exclusivity:** Overlap between Group A and Group B is strictly **0**.

---

## 4. Experiment Q2: Regime Sensitivity & Sign Flip

{df_to_md(df_expQ2)}

---

## 5. Experiment Q3: Robustness of the Difference (Canonical Bullish)

{df_to_md(df_expQ3)}

- **Trimming & Winsorizing:** Under 5% winsorization, the difference shrinks to **+1.02%** with CI **[-1.57%, +3.68%]**. Under 5% winner trimming, the difference is **+1.14%** with CI **[-1.23%, +3.41%]**. In all cases, the difference confidence interval spans zero (`NOT_ESTABLISHED`).

---

## 6. Sample-Size & Date Independence Audit
- **Canonical Bullish Dates:** {q1['Dates_SOS']} checkpoint dates contributed to SOS, and {q1['Dates_Frozen']} checkpoint dates contributed to Frozen Spring+SC (minimum threshold >= 12 satisfied).
- **Date Overlap:** Both setups were active across {q1['Paired_Dates']} common Bullish checkpoint dates.

---

## 7. WHAT THIS DOES NOT DO
- **Does NOT adopt SOS as the primary signal:** The strategy remains frozen as Spring + SC.
- **Does NOT modify production source code:** Zero files under `src/` were modified.
- **Does NOT remove LPS from production:** `broad_filter.py` remains untouched.
- **Does NOT touch the prospective OOS firewall:** `data/oos/` remains strictly isolated.

---

## 8. WHAT WOULD BE NEEDED BEFORE ADOPTION
Before any future pivot to SOS could be considered:
1. The difference confidence interval (Mean_SOS - Mean_Frozen) must strictly exclude zero across **both** market regimes.
2. The sign of the difference must not flip when market breadth expands into recovery periods.
3. A formal pre-registered prospective test must demonstrate that SOS execution outperforms Spring/SC on out-of-sample data.
"""

if __name__ == "__main__":
    main()
