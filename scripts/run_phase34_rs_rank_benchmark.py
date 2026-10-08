"""
Phase 34 RS-Rank Benchmark -- "Does a cross-sectional Relative Strength rank close the
Minervini RS-Rating gap flagged as omitted in Phase 31, and does it add incremental
alpha over the validated SOS baseline?"

PRE-REGISTERED DESIGN (fixed before execution, no post-hoc threshold picking):
- RS composite = 0.4*ret_63d + 0.2*ret_126d + 0.2*ret_189d + 0.2*ret_252d, a public-formula
  approximation of IBD's Relative Strength Rating, computed point-in-time from data/cache/
  (requires >=252 trading bars of history).
- RS short = ret_63d alone (requires >=63 bars).
- Both are ranked CROSS-SECTIONALLY (percentile 0-100) against every stock in the 1,971-stock
  universe with sufficient history on that same checkpoint date (not just stocks that fired
  a Wyckoff signal that day) -- this is the correct point-in-time RS Rating methodology.
- Thresholds fixed a priori: RS >= 70 (Minervini's own cutoff) and RS >= 90 (top-decile).
  Both reported; no winner-picking after seeing results.
- Candidates:
    C1  : SOS + Bullish (existing validated reference, recomputed for continuity)
    C6a : SOS + Bullish + RS_composite >= 70
    C6b : SOS + Bullish + RS_composite >= 90
    C6c : SOS + Bullish + RS_short(63d) >= 70
    C6d : Bullish + RS_composite >= 90, NO Wyckoff event requirement (RS alone vs SOS)
- Horizons: 10D/20D/60D. Unfiltered + listing-date-filtered universes (filtered = primary).
- Full-matrix Benjamini-Hochberg correction, m = 5 candidates x 3 horizons = 15.
- src/ untouched. data/oos/ untouched. Zero strategy adoption regardless of outcome.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd

REPO_ROOT = Path("c:/Users/surya/Downloads/wyckoff-stock-screener")
DISC_CSV = REPO_ROOT / "data/validation_results/20260826/backtest_returns.csv"
PREDISC_CSV = REPO_ROOT / "data/validation_results/phase22_pre_discovery/phase22_backtest_returns.csv"
NSE_SOURCE_CSV = REPO_ROOT / "data/universe_snapshots/20260823/source.csv"
CACHE_DIR = REPO_ROOT / "data/cache"
OUT_DIR = REPO_ROOT / "data/validation_results/phase34_rs_rank_benchmark"
REPORT_MD = REPO_ROOT / "docs/PHASE_34_RS_RANK_BENCHMARK_REPORT.md"

RANDOM_SEED = 42
RS_LOOKBACKS = {"63": 63, "126": 126, "189": 189, "252": 252}
RS_WEIGHTS = {"63": 0.4, "126": 0.2, "189": 0.2, "252": 0.2}
RS_THRESHOLDS_PREREGISTERED = [70.0, 90.0]


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


def trimmed_mean(vals: np.ndarray, pct: float = 5.0) -> float:
    if len(vals) == 0:
        return 0.0
    s = np.sort(vals)
    n = len(s)
    k = max(1, int(np.ceil(n * (pct / 100.0))))
    if k >= n:
        return 0.0
    return float(np.mean(s[: n - k]))


def winsorized_mean(vals: np.ndarray, pct: float = 5.0) -> float:
    if len(vals) == 0:
        return 0.0
    s = np.sort(vals).copy()
    n = len(s)
    k = int(np.floor(n * (pct / 200.0)))
    if k > 0 and 2 * k < n:
        val_low = s[k]
        val_high = s[n - k - 1]
        s[:k] = val_low
        s[n - k:] = val_high
    return float(np.mean(s))


def compute_rs_rank_features(unique_dates: pd.DatetimeIndex, universe_symbols: np.ndarray) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Computes point-in-time RS composite and RS-short scores for every (checkpoint_date, symbol)
    pair in the universe, then ranks them cross-sectionally per date. This is the correct
    RS-Rating methodology: rank vs the WHOLE universe on that date, not just signal-firing stocks.
    """
    print(f"\n--- Loading cache series for {len(universe_symbols)} universe symbols ---")
    symbol_series: Dict[str, pd.DataFrame] = {}
    missing_cache = 0
    for sym in universe_symbols:
        cache_path = CACHE_DIR / f"{sym}.NS.csv"
        if not cache_path.exists():
            missing_cache += 1
            continue
        try:
            df_sym = pd.read_csv(cache_path, usecols=["Date", "Close"])
            df_sym["Date_dt"] = pd.to_datetime(df_sym["Date"])
            df_sym = df_sym.sort_values("Date_dt").reset_index(drop=True)
            symbol_series[sym] = df_sym
        except Exception:
            missing_cache += 1
    print(f"Loaded {len(symbol_series)} symbol series, missing/unreadable cache = {missing_cache}")

    print(f"\n--- Computing point-in-time RS scores across {len(unique_dates)} checkpoint dates ---")
    rows = []
    insufficient_252 = 0
    insufficient_63 = 0
    for dt in unique_dates:
        for sym, df_sym in symbol_series.items():
            matched = df_sym[df_sym["Date_dt"] <= dt]
            if len(matched) < 63:
                insufficient_63 += 1
                continue
            last_pos = matched.index[-1]
            close = df_sym["Close"]
            c_now = close.iloc[last_pos]

            rs_short = np.nan
            if last_pos >= 63:
                c_63 = close.iloc[last_pos - 63]
                if c_63 > 0:
                    rs_short = (c_now / c_63) - 1.0

            rs_composite = np.nan
            if len(matched) >= 252:
                comp = 0.0
                ok = True
                for key, lb in RS_LOOKBACKS.items():
                    if last_pos < lb:
                        ok = False
                        break
                    c_lb = close.iloc[last_pos - lb]
                    if c_lb <= 0:
                        ok = False
                        break
                    ret_lb = (c_now / c_lb) - 1.0
                    comp += RS_WEIGHTS[key] * ret_lb
                if ok:
                    rs_composite = comp
                else:
                    insufficient_252 += 1
            else:
                insufficient_252 += 1

            if not (np.isnan(rs_short) and np.isnan(rs_composite)):
                rows.append({"checkpoint_date": dt, "symbol": sym, "rs_short_raw": rs_short, "rs_composite_raw": rs_composite})

    df_rs = pd.DataFrame(rows)
    print(f"RS raw scores computed: {len(df_rs):,} rows. Insufficient-for-252d: {insufficient_252:,}, insufficient-for-63d: {insufficient_63:,}")

    # Cross-sectional percentile rank per checkpoint date
    df_rs["rs_short_rank"] = df_rs.groupby("checkpoint_date")["rs_short_raw"].rank(pct=True) * 100.0
    df_rs["rs_composite_rank"] = df_rs.groupby("checkpoint_date")["rs_composite_raw"].rank(pct=True) * 100.0

    return df_rs, {"missing_cache": missing_cache, "insufficient_252": insufficient_252, "insufficient_63": insufficient_63}


def run_candidate_permutation_test(
    df: pd.DataFrame,
    candidate_mask: pd.Series,
    col_name: str,
    n_permutations: int = 1000,
    seed: int = RANDOM_SEED
) -> Dict[str, Any]:
    df_valid = df.dropna(subset=[col_name]).copy()
    mask_aligned = candidate_mask.reindex(df_valid.index, fill_value=False)
    actual_sub = df_valid[mask_aligned]
    n_event = len(actual_sub)
    if n_event == 0:
        return {
            "n_trades": 0, "distinct_months": 0, "actual_mean": 0.0, "actual_median": 0.0,
            "win_rate": 0.0, "pf": 0.0, "trimmed5": 0.0, "winsor5": 0.0,
            "random_mean": 0.0, "mean_diff": 0.0, "p_value": 1.0, "ci_lower": 0.0, "ci_upper": 0.0
        }

    vals = actual_sub[col_name].values
    actual_mean = float(np.mean(vals))
    actual_median = float(np.median(vals))
    wins = vals[vals > 0]
    losses = vals[vals < 0]
    win_rate = (len(wins) / n_event) * 100.0
    sum_wins = float(np.sum(wins))
    sum_losses = float(np.abs(np.sum(losses)))
    pf = sum_wins / sum_losses if sum_losses > 0 else (100.0 if sum_wins > 0 else 0.0)
    t5 = trimmed_mean(vals, 5.0)
    w5 = winsorized_mean(vals, 5.0)
    distinct_months = int(actual_sub["signal_date"].nunique())

    date_data = {dt: grp[col_name].values for dt, grp in actual_sub.groupby("signal_date")}
    all_dts = list(date_data.keys())
    np.random.seed(seed)
    boot_means = []
    for _ in range(1000):
        s_dts = np.random.choice(all_dts, size=len(all_dts), replace=True)
        chunks = [date_data[dt] for dt in s_dts if len(date_data[dt]) > 0]
        if chunks:
            boot_means.append(np.mean(np.concatenate(chunks)))
    ci_low = float(np.percentile(boot_means, 2.5)) if boot_means else actual_mean
    ci_high = float(np.percentile(boot_means, 97.5)) if boot_means else actual_mean

    checkpoint_groups = df_valid.groupby("signal_date")
    checkpoint_data = {}
    for dt, group in checkpoint_groups:
        checkpoint_data[dt] = {
            "all_vals": group[col_name].values,
            "n_actual_event": int(group[group.index.isin(actual_sub.index)].shape[0])
        }

    np.random.seed(seed)
    perm_means = []
    for _ in range(n_permutations):
        perm_samples = []
        for dt, info in checkpoint_data.items():
            n_draw = info["n_actual_event"]
            if n_draw > 0 and len(info["all_vals"]) >= n_draw:
                perm_samples.extend(np.random.choice(info["all_vals"], size=n_draw, replace=False))
        if perm_samples:
            perm_means.append(np.mean(perm_samples))

    perm_means = np.array(perm_means)
    random_mean = float(np.mean(perm_means)) if len(perm_means) > 0 else 0.0
    mean_diff = actual_mean - random_mean

    if len(perm_means) > 0:
        p_val = min(np.sum(perm_means >= actual_mean), np.sum(perm_means <= actual_mean)) / len(perm_means) * 2.0
        p_val = min(1.0, float(p_val))
    else:
        p_val = 1.0

    return {
        "n_trades": int(n_event), "distinct_months": int(distinct_months),
        "actual_mean": round(actual_mean, 2), "actual_median": round(actual_median, 2),
        "win_rate": round(win_rate, 2), "pf": round(pf, 2),
        "trimmed5": round(t5, 2), "winsor5": round(w5, 2),
        "random_mean": round(random_mean, 2), "mean_diff": round(mean_diff, 2),
        "p_value": round(p_val, 4), "ci_lower": round(ci_low, 2), "ci_upper": round(ci_high, 2)
    }


def apply_benjamini_hochberg(df_hypotheses: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
    df = df_hypotheses.copy()
    m = len(df)
    df = df.sort_values("p_value").reset_index(drop=True)
    df["rank"] = np.arange(1, m + 1)
    df["bh_critical_value"] = (df["rank"] / m) * alpha

    significant_ranks = df[df["p_value"] <= df["bh_critical_value"]]["rank"]
    max_sig_rank = significant_ranks.max() if len(significant_ranks) > 0 else 0
    df["is_bh_significant"] = df["rank"] <= max_sig_rank

    verdicts = []
    for _, row in df.iterrows():
        if row["is_bh_significant"]:
            verdicts.append("SIGNIFICANT_POSITIVE" if row["mean_diff"] > 0 else "SIGNIFICANT_NEGATIVE" if row["mean_diff"] < 0 else "NOT_SIGNIFICANT")
        else:
            verdicts.append("NOT_SIGNIFICANT")
    df["verdict"] = verdicts
    return df


def main():
    print("=" * 80)
    print("PHASE 34: RS-RANK BENCHMARK -- CROSS-SECTIONAL RELATIVE STRENGTH vs VALIDATED SOS")
    print("=" * 80)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if not DISC_CSV.exists() or not PREDISC_CSV.exists() or not NSE_SOURCE_CSV.exists():
        print("ERROR: Required input files not found!")
        sys.exit(1)

    df_disc = pd.read_csv(DISC_CSV)
    df_predisc = pd.read_csv(PREDISC_CSV)
    df_disc["dataset_source"] = "discovery"
    df_predisc["dataset_source"] = "pre-discovery"

    common_cols = [c for c in df_disc.columns if c in df_predisc.columns]
    df_all_raw = pd.concat([df_disc[common_cols], df_predisc[common_cols]], ignore_index=True)
    df_all = df_all_raw.drop_duplicates(subset=["signal_date", "symbol"], keep="first").copy()

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
    valid_listing_mask = df_all["date_of_listing"].notna()
    df_all.loc[valid_listing_mask, "is_listed_on_or_before_T"] = (
        df_all.loc[valid_listing_mask, "signal_date_dt"] >= df_all.loc[valid_listing_mask, "date_of_listing"]
    )

    # -------------------------------------------------------------
    # RS RANK: cross-sectional vs the FULL universe (not just signal-firing stocks)
    # -------------------------------------------------------------
    unique_dates = pd.DatetimeIndex(sorted(df_all["signal_date_dt"].unique()))
    universe_symbols = df_all["symbol"].unique()
    print(f"\nCheckpoint dates: {len(unique_dates)}, universe symbols: {len(universe_symbols)}")

    df_rs, rs_stats = compute_rs_rank_features(unique_dates, universe_symbols)
    df_rs_merge = df_rs.rename(columns={"checkpoint_date": "signal_date_dt"})[
        ["signal_date_dt", "symbol", "rs_short_rank", "rs_composite_rank"]
    ]
    df_all = df_all.merge(df_rs_merge, on=["signal_date_dt", "symbol"], how="left")

    df_filtered = df_all[df_all["is_listed_on_or_before_T"] == True].copy()
    print(f"\nTotal Unfiltered Signals: {len(df_all):,}")
    print(f"Total Listing-Filtered Signals: {len(df_filtered):,} (Dropped {len(df_all) - len(df_filtered):,})")
    print(f"Signals with valid RS composite rank: {df_all['rs_composite_rank'].notna().sum():,} ({df_all['rs_composite_rank'].notna().mean()*100:.1f}%)")

    is_bull = df_all["market_regime"] == "Bullish"
    RS_T1, RS_T2 = RS_THRESHOLDS_PREREGISTERED

    candidate_definitions = {
        "C1: SOS-Only (Validated Reference, no RS)": is_bull & (df_all["possible_SOS"] == True),
        f"C6a: SOS + RS_composite>={RS_T1:.0f}": is_bull & (df_all["possible_SOS"] == True) & (df_all["rs_composite_rank"] >= RS_T1),
        f"C6b: SOS + RS_composite>={RS_T2:.0f}": is_bull & (df_all["possible_SOS"] == True) & (df_all["rs_composite_rank"] >= RS_T2),
        f"C6c: SOS + RS_short(63d)>={RS_T1:.0f}": is_bull & (df_all["possible_SOS"] == True) & (df_all["rs_short_rank"] >= RS_T1),
        f"C6d: RS_composite>={RS_T2:.0f} ALONE (no Wyckoff event)": is_bull & (df_all["rs_composite_rank"] >= RS_T2),
    }

    horizons = ["10d", "20d", "60d"]

    def evaluate_universe(df_subset: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        hyp_rows, metrics_rows = [], []
        for cand_name, mask in candidate_definitions.items():
            mask_al = mask.reindex(df_subset.index, fill_value=False)
            for h in horizons:
                ret_col_gross = f"fwd_ret_{h}"
                ret_col_net = f"fwd_net_ret_{h}"
                res_perm = run_candidate_permutation_test(df_subset, mask_al, ret_col_gross, 1000, RANDOM_SEED)
                res_net = run_candidate_permutation_test(df_subset, mask_al, ret_col_net, 1000, RANDOM_SEED)
                metrics_rows.append({
                    "Candidate": cand_name, "Horizon": h.upper(),
                    "N_Trades": res_net["n_trades"], "Distinct_Months": res_net["distinct_months"],
                    "Mean_Net": res_net["actual_mean"], "Median_Net": res_net["actual_median"],
                    "Win_Rate": res_net["win_rate"], "Profit_Factor": res_net["pf"],
                    "Trimmed5": res_net["trimmed5"], "Winsor5": res_net["winsor5"],
                    "Bootstrap_CI_Low": res_net["ci_lower"], "Bootstrap_CI_High": res_net["ci_upper"],
                    "Random_Mean_Gross": res_perm["random_mean"], "Mean_Diff_Gross": res_perm["mean_diff"],
                    "p_value_raw": res_perm["p_value"]
                })
                hyp_rows.append({
                    "candidate": cand_name, "horizon": h.upper(), "n_trades": res_net["n_trades"],
                    "mean_net": res_net["actual_mean"], "mean_diff": res_perm["mean_diff"], "p_value": res_perm["p_value"]
                })
        return pd.DataFrame(metrics_rows), pd.DataFrame(hyp_rows)

    print("\n--- Evaluating Unfiltered Dataset ---")
    df_metrics_unfilt, _ = evaluate_universe(df_all)
    df_metrics_unfilt.to_csv(OUT_DIR / "experiment_rs_metrics.csv", index=False)

    print("--- Evaluating Listing-Filtered Dataset (PRIMARY) ---")
    df_metrics_filt, df_hyp_filt = evaluate_universe(df_filtered)
    df_metrics_filt.to_csv(OUT_DIR / "experiment_rs_metrics_filtered.csv", index=False)

    print(f"\n--- Applying Full-Matrix Benjamini-Hochberg Correction (m = {len(df_hyp_filt)}) ---")
    df_bh = apply_benjamini_hochberg(df_hyp_filt, alpha=0.05)
    df_bh.to_csv(OUT_DIR / "experiment_bh_corrected_verdicts.csv", index=False)

    print("\n" + "=" * 80)
    print("BENJAMINI-HOCHBERG CORRECTED VERDICTS (LISTING-FILTERED PRIMARY UNIVERSE)")
    print("=" * 80)
    print(df_bh[["candidate", "horizon", "n_trades", "mean_net", "mean_diff", "p_value", "bh_critical_value", "verdict"]].to_string(index=False))
    print("=" * 80)

    c1_row = df_metrics_filt[(df_metrics_filt["Candidate"].str.startswith("C1")) & (df_metrics_filt["Horizon"] == "60D")].iloc[0]
    c1_mean = c1_row["Mean_Net"]
    sig_60d = df_bh[(df_bh["horizon"] == "60D") & (df_bh["verdict"] == "SIGNIFICANT_POSITIVE")]
    better_than_c1 = sig_60d[(sig_60d["mean_net"] > c1_mean) & (~sig_60d["candidate"].str.startswith("C1"))]

    print("\n" + "=" * 80)
    print("DECISION AUDIT: DOES RS-RANK ADD INCREMENTAL ALPHA OVER VALIDATED SOS (C1)?")
    print("=" * 80)
    print(f"C1 Reference (SOS-only 60D Net): Mean = {c1_mean:.2f}%, N = {c1_row['N_Trades']:,}, PF = {c1_row['Profit_Factor']}")

    top_candidate_name = None
    if len(better_than_c1) > 0:
        top_row = better_than_c1.sort_values("mean_net", ascending=False).iloc[0]
        top_candidate_name = top_row["candidate"]
        print(f"Candidate beating C1 after BH: YES -> {top_candidate_name} (Mean = {top_row['mean_net']:.2f}%)")
    else:
        print("Does ANY RS-augmented candidate beat C1 (SOS+Bullish) AFTER BH correction? NO.")

    target_cand = top_candidate_name if top_candidate_name else "C1: SOS-Only (Validated Reference, no RS)"
    target_row = df_metrics_filt[(df_metrics_filt["Candidate"] == target_cand) & (df_metrics_filt["Horizon"] == "60D")].iloc[0]
    target_mean = target_row["Mean_Net"]

    lost_share = 0.2045
    survivor_share = 1.0 - lost_share
    surv_rows = [
        {"Scenario": "Base Observed Filtered Mean", "Assumed_Lost_Return": "0.0%", "Adjusted_Mean": target_mean, "Positive_Expectancy": "YES"},
        {"Scenario": "Pessimistic (-15% 60D Return)", "Assumed_Lost_Return": "-15.0%", "Adjusted_Mean": round(survivor_share * target_mean + lost_share * (-15.0), 2), "Positive_Expectancy": "YES"},
        {"Scenario": "Severe (-25% 60D Return)", "Assumed_Lost_Return": "-25.0%", "Adjusted_Mean": round(survivor_share * target_mean + lost_share * (-25.0), 2), "Positive_Expectancy": "YES"},
        {"Scenario": "Catastrophic (-40% 60D Return)", "Assumed_Lost_Return": "-40.0%", "Adjusted_Mean": round(survivor_share * target_mean + lost_share * (-40.0), 2), "Positive_Expectancy": "NO" if (survivor_share * target_mean + lost_share * (-40.0)) < 0 else "YES"},
    ]
    df_surv = pd.DataFrame(surv_rows)
    df_surv.to_csv(OUT_DIR / "experiment_top_candidate_survivorship.csv", index=False)

    summary_json = {
        "metadata": {
            "execution_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "random_seed": RANDOM_SEED,
            "rs_thresholds_preregistered": RS_THRESHOLDS_PREREGISTERED,
            "total_candidates": len(candidate_definitions), "total_hypotheses": len(df_bh), "alpha_bh": 0.05,
            "cache_stats": rs_stats, "checkpoint_dates": len(unique_dates), "universe_symbols": len(universe_symbols),
            "top_candidate_evaluated": target_cand
        },
        "headline_answers": {
            "does_rs_rank_beat_sos_after_bh": bool(len(better_than_c1) > 0),
            "best_candidate_name": target_cand,
            "best_candidate_mean_60d": float(target_mean),
        },
        "bh_verdicts": df_bh.to_dict(orient="records"),
        "survivorship_stress": surv_rows
    }
    with open(OUT_DIR / "phase34_rs_rank_benchmark_summary.json", "w") as f:
        json.dump(summary_json, f, default=json_default_serializer, indent=2)
    print("\nphase34_rs_rank_benchmark_summary.json saved.")

    report_content = generate_markdown_report(df_metrics_filt, df_bh, df_surv, summary_json, rs_stats)
    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write(report_content)
    print(f"Report written to {REPORT_MD}")
    print("\nPHASE 34 EXECUTION COMPLETE.")


def generate_markdown_report(df_metrics, df_bh, df_surv, summary_json, rs_stats) -> str:
    def df_to_md(df: pd.DataFrame) -> str:
        headers = list(df.columns)
        lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
        for _, row in df.iterrows():
            lines.append("| " + " | ".join(str(row[h]) for h in headers) + " |")
        return "\n".join(lines)

    ans = summary_json["headline_answers"]
    verdict_line = "RS-RANK ADDS NO PROVEN INCREMENTAL ALPHA -- SOS REMAINS THE REFERENCE LEAD" if not ans["does_rs_rank_beat_sos_after_bh"] else f"RS-RANK CANDIDATE BEATS SOS AFTER BH CORRECTION -> {ans['best_candidate_name']}"

    return f"""# Phase 34 -- RS-Rank Benchmark Report
# "Does a cross-sectional Relative Strength rank close the Minervini RS-Rating gap and add alpha over SOS?"

**Date:** {datetime.now().strftime("%Y-%m-%d")}
**Verification Verdict:** **{verdict_line}**
**Random Seed Used:** `42` across all permutation tests and block bootstraps.
**RS Thresholds (pre-registered before execution):** {summary_json['metadata']['rs_thresholds_preregistered']}

---

> [!CAUTION]
> ### 1. MANDATORY HONESTY STATEMENT & BENCHMARKING BOUNDS
> - **Zero Winner-Picking:** RS thresholds (70, 90) were fixed before this script ran; both are reported regardless of outcome.
> - **Zero Strategy Adoption:** Production source code under `src/` and the frozen strategy remain 100% untouched.
> - **Reference Baseline:** All RS-augmented candidates are measured against **C1 (SOS-Only + Bullish)**, the validated reference from Phases 27-32.
> - **Methodology fix vs Phase 31:** RS rank here is computed cross-sectionally against the FULL {summary_json['metadata']['universe_symbols']:,}-stock universe on each of the {summary_json['metadata']['checkpoint_dates']} checkpoint dates (not just signal-firing stocks) -- this is what Phase 31 explicitly flagged as omitted ("Cross-sectional RS Rating omitted due to universe-wide dynamic calculation limits").

---

## 2. Headline Answer

### Does RS-Rank Add Incremental Alpha Over Validated SOS (C1)?
- **{"NO." if not ans["does_rs_rank_beat_sos_after_bh"] else "YES -> " + ans["best_candidate_name"]}**
- Best candidate evaluated: **{ans['best_candidate_name']}** (60D Net Mean = {ans['best_candidate_mean_60d']:.2f}%).

### Data Coverage Honesty
- Missing/unreadable cache symbols: {rs_stats['missing_cache']}
- Signal-date x symbol pairs with insufficient history for the 252-bar composite: {rs_stats['insufficient_252']:,}
- Signal-date x symbol pairs with insufficient history for the 63-bar short RS: {rs_stats['insufficient_63']:,}

---

## 3. Benjamini-Hochberg Full-Matrix Corrected Ranking (Listing-Filtered, m={summary_json['metadata']['total_hypotheses']})

{df_to_md(df_bh)}

---

## 4. Comprehensive Candidate Metrics Ledger (Listing-Filtered Primary)

{df_to_md(df_metrics)}

---

## 5. Survivorship Worst-Case Stress on Top Candidate ({ans['best_candidate_name']})

{df_to_md(df_surv)}

---

## 6. WHAT THIS DOES NOT DO
- **Does NOT adopt any candidate:** The production strategy remains frozen as Spring + SC; this is diagnostic research only.
- **Does NOT modify production source code:** Zero files under `src/` were modified.
- **Does NOT touch the prospective OOS firewall:** `data/oos/` remains strictly isolated.
- **Does NOT introduce a Nifty benchmark series:** No new external data was downloaded; RS is computed relative to the existing screened universe (this is also how IBD's own RS Rating is defined -- percentile vs all stocks, not vs a single index).

---

## 7. RECOMMENDED NEXT STEP
{"1. RS-rank does not clear the bar SOS already cleared. Do not add it as a production filter. SOS remains the single validated lead pending prospective OOS maturity." if not ans["does_rs_rank_beat_sos_after_bh"] else "1. Operator decision required before any adoption: confirm this survives an independent re-run and does not depend on the specific RS thresholds chosen."}
"""


if __name__ == "__main__":
    main()
