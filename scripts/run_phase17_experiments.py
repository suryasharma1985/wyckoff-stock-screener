import os
import sys
import time
import json
import pandas as pd
import numpy as np
from pathlib import Path

# Paths
INPUT_DIR = Path("c:/Users/surya/Downloads/wyckoff-stock-screener/data/validation_results/20260826")
RETURNS_CSV = INPUT_DIR / "backtest_returns.csv"
PRICES_CSV = INPUT_DIR / "historical_prices.csv"
DIAG_OUT_DIR = Path("c:/Users/surya/Downloads/wyckoff-stock-screener/data/diagnostics/phase17")
PROGRESS_JSON = DIAG_OUT_DIR / "progress.json"
RESULTS_JSON = DIAG_OUT_DIR / "phase17_results.json"

def calculate_downside_deviation(series):
    neg_diffs = series[series < 0]
    if len(series) == 0:
        return 0.0
    return float(np.sqrt((neg_diffs ** 2).sum() / len(series)))

def update_progress(percent, exp_name, processed, total, elapsed, errors=0):
    DIAG_OUT_DIR.mkdir(parents=True, exist_ok=True)
    rem = 0
    if percent > 0:
        rem = int((elapsed / (percent / 100.0)) - elapsed)
        
    prog = {
        "phase": "17",
        "status": "running" if percent < 100 else "completed",
        "overall_percent": round(percent, 1),
        "current_experiment": exp_name,
        "stocks_processed": processed,
        "stocks_total": total,
        "observations_processed": processed,
        "observations_total": total,
        "elapsed_seconds": int(elapsed),
        "estimated_remaining_seconds": rem,
        "trades_processed": processed,
        "errors": errors
    }
    with open(PROGRESS_JSON, "w") as f:
        json.dump(prog, f, indent=2)
    print(f"[{exp_name}] {percent:.1%} Complete - Processed {processed}/{total} - Elapsed: {elapsed:.1f}s - ETA: {rem}s")

def simulate_lps_breakout(df_returns, df_prices, t0):
    update_progress(10.0, "LPS Breakout Simulation", 0, len(df_returns), time.time() - t0)
    
    lps_signals = df_returns[df_returns["most_recent_event_type"] == "LPS"].copy()
    n_signals = len(lps_signals)
    
    prices_by_stock = {}
    for sym, group in df_prices.groupby("Symbol"):
        group = group.sort_values(by="Date").reset_index(drop=True)
        group["Date_dt"] = pd.to_datetime(group["Date"])
        prices_by_stock[sym] = group
        
    horizons = [10, 20, 60]
    results = {h: {"model_a": [], "model_b": [], "model_c": []} for h in horizons}
    
    count_processed = 0
    errors = 0
    
    for idx, row in lps_signals.iterrows():
        count_processed += 1
        if count_processed % 3000 == 0:
            pct = 10.0 + (count_processed / n_signals) * 20.0
            update_progress(pct, "LPS Breakout Simulation", count_processed, n_signals, time.time() - t0, errors)
            
        sym = row["symbol"]
        if sym not in prices_by_stock:
            errors += 1
            continue
            
        pdf = prices_by_stock[sym]
        sig_date = pd.to_datetime(row["signal_date"])
        
        matches = pdf.index[pdf["Date_dt"] == sig_date].tolist()
        if not matches:
            errors += 1
            continue
        t_idx = matches[0]
        lps_high = float(pdf.loc[t_idx, "High"])
        total_bars = len(pdf)
        
        # 1. MODEL A: Baseline
        entry_idx_a = t_idx + 1
        if entry_idx_a < total_bars:
            entry_p_a = float(pdf.loc[entry_idx_a, "Open"])
            for h in horizons:
                exit_idx = entry_idx_a + h
                if exit_idx < total_bars:
                    exit_p = float(pdf.loc[exit_idx, "Close"])
                    gross_ret = (exit_p - entry_p_a) / entry_p_a * 100.0
                    results[h]["model_a"].append(gross_ret)
                    
        # 2. MODEL B: Breakout of High (Within 10-day window)
        triggered_idx_b = None
        entry_p_b = None
        for k in range(1, 11):
            scan_idx = t_idx + k
            if scan_idx >= total_bars:
                break
            high_val = float(pdf.loc[scan_idx, "High"])
            open_val = float(pdf.loc[scan_idx, "Open"])
            if high_val > lps_high:
                triggered_idx_b = scan_idx
                entry_p_b = max(open_val, lps_high)
                break
                
        if triggered_idx_b is not None:
            for h in horizons:
                exit_idx = triggered_idx_b + h
                if exit_idx < total_bars:
                    exit_p = float(pdf.loc[exit_idx, "Close"])
                    gross_ret = (exit_p - entry_p_b) / entry_p_b * 100.0
                    results[h]["model_b"].append(gross_ret)
                    
        # 3. MODEL C: Conservative Close Breakout
        triggered_idx_c = None
        for k in range(1, 11):
            scan_idx = t_idx + k
            if scan_idx >= total_bars:
                break
            close_val = float(pdf.loc[scan_idx, "Close"])
            if close_val > lps_high:
                triggered_idx_c = scan_idx + 1
                break
                
        if triggered_idx_c is not None and triggered_idx_c < total_bars:
            entry_p_c = float(pdf.loc[triggered_idx_c, "Open"])
            for h in horizons:
                exit_idx = triggered_idx_c + h
                if exit_idx < total_bars:
                    exit_p = float(pdf.loc[exit_idx, "Close"])
                    gross_ret = (exit_p - entry_p_c) / entry_p_c * 100.0
                    results[h]["model_c"].append(gross_ret)
                    
    model_stats = {}
    csv_rows = []
    
    for h in horizons:
        model_stats[f"{h}d"] = {}
        for m_name in ["model_a", "model_b", "model_c"]:
            arr = np.array(results[h][m_name])
            n_trades = len(arr)
            trig_rate = (n_trades / n_signals) * 100.0 if n_signals > 0 else 0.0
            expired_rate = 100.0 - trig_rate if m_name in ["model_b", "model_c"] else 0.0
            
            # Apply 0.40% friction
            net_arr = arr - 0.40
            
            wins = int((net_arr > 0).sum())
            losses = int((net_arr < 0).sum())
            win_rate = (wins / len(net_arr)) * 100.0 if len(net_arr) > 0 else 0.0
            avg_net = float(net_arr.mean()) if len(net_arr) > 0 else 0.0
            med_net = float(np.median(net_arr)) if len(net_arr) > 0 else 0.0
            
            sum_win = net_arr[net_arr > 0].sum()
            sum_loss = abs(net_arr[net_arr < 0].sum())
            pf = float(sum_win / sum_loss) if sum_loss > 0 else 999.0
            
            avg_win = float(net_arr[net_arr > 0].mean()) if wins > 0 else 0.0
            avg_loss = float(net_arr[net_arr < 0].mean()) if losses > 0 else 0.0
            expectancy = (win_rate / 100.0 * avg_win) + ((100.0 - win_rate) / 100.0 * avg_loss)
            
            max_gain = float(net_arr.max()) if len(net_arr) > 0 else 0.0
            max_loss = float(net_arr.min()) if len(net_arr) > 0 else 0.0
            
            # Outlier contributions
            wins_only = np.sort(net_arr[net_arr > 0])[::-1]
            total_wins_sum = wins_only.sum()
            top_1_cnt = max(1, int(np.ceil(0.01 * len(wins_only)))) if len(wins_only) > 0 else 0
            top_5_cnt = max(1, int(np.ceil(0.05 * len(wins_only)))) if len(wins_only) > 0 else 0
            top_1_contrib = float(wins_only[:top_1_cnt].sum() / total_wins_sum * 100.0) if total_wins_sum > 0 else 0.0
            top_5_contrib = float(wins_only[:top_5_cnt].sum() / total_wins_sum * 100.0) if total_wins_sum > 0 else 0.0
            
            model_stats[f"{h}d"][m_name] = {
                "trades": n_trades,
                "trigger_rate": round(trig_rate, 2),
                "expired_rate": round(expired_rate, 2),
                "net_win_rate": round(win_rate, 2),
                "avg_net_ret": round(avg_net, 2),
                "med_net_ret": round(med_net, 2),
                "profit_factor": round(pf, 2),
                "expectancy": round(expectancy, 2),
                "max_gain": round(max_gain, 2),
                "max_loss": round(max_loss, 2),
                "top_1pct_contribution": round(top_1_contrib, 2),
                "top_5pct_contribution": round(top_5_contrib, 2)
            }
            
            csv_rows.append({
                "Horizon": f"{h}D",
                "Model": m_name,
                "Trades": n_trades,
                "TriggerRate": round(trig_rate, 2),
                "ExpiredRate": round(expired_rate, 2),
                "WinRate": round(win_rate, 2),
                "AvgNetReturn": round(avg_net, 2),
                "MedNetReturn": round(med_net, 2),
                "ProfitFactor": round(pf, 2),
                "Expectancy": round(expectancy, 2),
                "MaxGain": round(max_gain, 2),
                "MaxLoss": round(max_loss, 2)
            })
            
    # Export CSV
    pd.DataFrame(csv_rows).to_csv(DIAG_OUT_DIR / "lps_execution_comparison.csv", index=False)
    return model_stats

def run_diagnostics():
    t0 = time.time()
    update_progress(0.0, "Initialization", 0, 100, 0.0)
    
    # 1. Load datasets
    df = pd.read_csv(RETURNS_CSV)
    df_prices = pd.read_csv(PRICES_CSV)
    update_progress(5.0, "Data Ingestion Complete", len(df), len(df), time.time() - t0)
    
    horizons = [10, 20, 60]
    results = {}
    
    # Setup breadth regimes
    df["above_50dma"] = (df["signal_close"] > df["dma_50"]).astype(int)
    breadth = df.groupby("signal_date")["above_50dma"].mean()
    regime_map = {dt: ("Bull" if val >= 0.60 else "Bear" if val < 0.30 else "Neutral") for dt, val in breadth.items()}
    df["market_regime"] = df["signal_date"].map(regime_map)
    
    # --- EXPERIMENT 1: LPS BREAKOUT ---
    results["lps_breakout_experiment"] = simulate_lps_breakout(df, df_prices, t0)
    update_progress(35.0, "LPS Breakout Simulation Complete", len(df), len(df), time.time() - t0)
    
    # --- EXPERIMENT 2: EVENT-LEVEL EDGE ---
    print("\nRunning Event-Level Edge analysis...")
    results["wyckoff_events"] = {}
    event_col = "most_recent_event_type"
    csv_rows_events = []
    
    for h in horizons:
        ret_col = f"fwd_ret_{h}d"
        net_ret_col = f"fwd_net_ret_{h}d"
        hdf = df[[event_col, ret_col, net_ret_col, "signal_date", "market_regime"]].dropna(subset=[ret_col, event_col]).copy()
        results["wyckoff_events"][f"{h}d"] = {}
        
        for ev_name in hdf[event_col].unique():
            edf = hdf[hdf[event_col] == ev_name]
            n_obs = len(edf)
            if n_obs < 10:
                continue
                
            wins = int((edf[net_ret_col] > 0).sum())
            losses = int((edf[net_ret_col] < 0).sum())
            win_rate = (wins / n_obs) * 100.0
            avg_net = float(edf[net_ret_col].mean())
            med_net = float(edf[net_ret_col].median())
            
            sum_win = edf[edf[net_ret_col] > 0][net_ret_col].sum()
            sum_loss = abs(edf[edf[net_ret_col] < 0][net_ret_col].sum())
            pf = float(sum_win / sum_loss) if sum_loss > 0 else 999.0
            
            avg_win = float(edf[edf[net_ret_col] > 0][net_ret_col].mean()) if wins > 0 else 0.0
            avg_loss = float(edf[edf[net_ret_col] < 0][net_ret_col].mean()) if losses > 0 else 0.0
            expectancy = (win_rate / 100.0 * avg_win) + ((100.0 - win_rate) / 100.0 * avg_loss)
            
            # Robustness exclusions
            wins_sorted = edf[net_ret_col].sort_values(ascending=False)
            total_wins = edf[edf[net_ret_col] > 0][net_ret_col].sum()
            cnt_1 = max(1, int(np.ceil(0.01 * len(wins_sorted))))
            cnt_5 = max(1, int(np.ceil(0.05 * len(wins_sorted))))
            
            pct_1_wins = float(wins_sorted.head(cnt_1).sum() / total_wins * 100.0) if total_wins > 0 else 0.0
            pct_5_wins = float(wins_sorted.head(cnt_5).sum() / total_wins * 100.0) if total_wins > 0 else 0.0
            
            # Yearly
            edf["year"] = pd.to_datetime(edf["signal_date"]).dt.year
            yearly_stats = {}
            for yr in sorted(edf["year"].unique()):
                ydf = edf[edf["year"] == yr]
                yearly_stats[str(yr)] = {
                    "trades": len(ydf),
                    "avg_net_ret": round(ydf[net_ret_col].mean(), 2),
                    "win_rate": round((ydf[net_ret_col] > 0).sum() / len(ydf) * 100.0, 2) if len(ydf) > 0 else 0.0
                }
                
            # Regime
            regime_stats = {}
            for reg in ["Bull", "Neutral", "Bear"]:
                rdf = edf[edf["market_regime"] == reg]
                regime_stats[reg] = {
                    "trades": len(rdf),
                    "avg_net_ret": round(rdf[net_ret_col].mean(), 2) if len(rdf) > 0 else 0.0,
                    "win_rate": round((rdf[net_ret_col] > 0).sum() / len(rdf) * 100.0, 2) if len(rdf) > 0 else 0.0
                }
                
            results["wyckoff_events"][f"{h}d"][str(ev_name)] = {
                "trades": n_obs,
                "win_rate": round(win_rate, 2),
                "avg_net_ret": round(avg_net, 2),
                "med_net_ret": round(med_net, 2),
                "profit_factor": round(pf, 2),
                "expectancy": round(expectancy, 2),
                "top_1pct_wins_share": round(pct_1_wins, 2),
                "top_5pct_wins_share": round(pct_5_wins, 2),
                "yearly": yearly_stats,
                "regime": regime_stats
            }
            
            csv_rows_events.append({
                "Horizon": f"{h}D",
                "Event": ev_name,
                "Trades": n_obs,
                "WinRate": round(win_rate, 2),
                "AvgNetReturn": round(avg_net, 2),
                "MedNetReturn": round(med_net, 2),
                "ProfitFactor": round(pf, 2),
                "Expectancy": round(expectancy, 2)
            })
            
    pd.DataFrame(csv_rows_events).to_csv(DIAG_OUT_DIR / "event_performance.csv", index=False)
    update_progress(50.0, "Event-Level Edge Complete", len(df), len(df), time.time() - t0)
    
    # --- EXPERIMENT 3: SCORE DISCRIMINATION ---
    print("\nRunning Score Discrimination statistics...")
    results["score_discrimination"] = {}
    score_buckets = [("0-49", 0, 49), ("50-59", 50, 59), ("60-69", 60, 69), ("70-79", 70, 79), ("80-89", 80, 89), ("90-100", 90, 100)]
    csv_rows_scores = []
    
    for h in horizons:
        ret_col = f"fwd_ret_{h}d"
        net_ret_col = f"fwd_net_ret_{h}d"
        hdf = df[[ret_col, net_ret_col, "composite_score", "signal_date"]].dropna(subset=[ret_col]).copy()
        
        results["score_discrimination"][f"{h}d"] = {"buckets": {}, "correlations": {}}
        
        for b_name, b_min, b_max in score_buckets:
            bdf = hdf[(hdf["composite_score"] >= b_min) & (hdf["composite_score"] <= b_max)]
            n_obs = len(bdf)
            if n_obs == 0:
                continue
            wins = int((bdf[net_ret_col] > 0).sum())
            win_rate = (wins / n_obs) * 100.0
            avg_net = float(bdf[net_ret_col].mean())
            med_net = float(bdf[net_ret_col].median())
            
            sum_win = bdf[bdf[net_ret_col] > 0][net_ret_col].sum()
            sum_loss = abs(bdf[bdf[net_ret_col] < 0][net_ret_col].sum())
            pf = float(sum_win / sum_loss) if sum_loss > 0 else 999.0
            
            results["score_discrimination"][f"{h}d"]["buckets"][b_name] = {
                "trades": n_obs,
                "win_rate": round(win_rate, 2),
                "avg_net_ret": round(avg_net, 2),
                "med_net_ret": round(med_net, 2),
                "profit_factor": round(pf, 2)
            }
            
            csv_rows_scores.append({
                "Horizon": f"{h}D",
                "ScoreBucket": b_name,
                "Trades": n_obs,
                "WinRate": round(win_rate, 2),
                "AvgNetReturn": round(avg_net, 2),
                "MedNetReturn": round(med_net, 2),
                "ProfitFactor": round(pf, 2)
            })
            
        pearson = hdf["composite_score"].corr(hdf[net_ret_col], method="pearson")
        spearman = hdf["composite_score"].rank().corr(hdf[net_ret_col].rank(), method="pearson")
        
        results["score_discrimination"][f"{h}d"]["correlations"] = {
            "pearson_r": round(pearson, 4) if pd.notna(pearson) else 0.0,
            "spearman_r": round(spearman, 4) if pd.notna(spearman) else 0.0
        }
        
    pd.DataFrame(csv_rows_scores).to_csv(DIAG_OUT_DIR / "score_buckets_performance.csv", index=False)
    update_progress(65.0, "Score Discrimination Complete", len(df), len(df), time.time() - t0)
    
    # --- EXPERIMENT 4: SCORE COMPONENT ATTRIBUTION ---
    print("\nRunning Score Component Attribution...")
    results["component_attribution"] = {}
    indicators = ["pf_upside_pct", "atr_contraction_ratio", "bb_width_20", "rsi_14", "is_mechanically_qualified"]
    
    for ind in indicators:
        if ind not in df.columns:
            continue
        results["component_attribution"][ind] = {}
        for h in horizons:
            net_ret_col = f"fwd_net_ret_{h}d"
            hdf = df[[ind, net_ret_col]].dropna().copy()
            if len(hdf) == 0:
                continue
            if hdf[ind].dtype == bool:
                hdf[ind] = hdf[ind].astype(int)
            pearson = hdf[ind].corr(hdf[net_ret_col], method="pearson")
            spearman = hdf[ind].rank().corr(hdf[net_ret_col].rank(), method="pearson")
            results["component_attribution"][ind][f"{h}d"] = {
                "pearson_r": round(pearson, 4) if pd.notna(pearson) else 0.0,
                "spearman_r": round(spearman, 4) if pd.notna(spearman) else 0.0
            }
    update_progress(75.0, "Score Component Attribution Complete", len(df), len(df), time.time() - t0)
    
    # --- EXPERIMENT 5: GROUP A VS GROUP B ---
    print("\nRunning Group A (Spring/SC/SOS) vs Group B (LPS/AR/ST/UTAD)...")
    results["group_comparison"] = {}
    csv_rows_groups = []
    
    for h in horizons:
        ret_col = f"fwd_ret_{h}d"
        net_ret_col = f"fwd_net_ret_{h}d"
        hdf = df[[event_col, ret_col, net_ret_col, "signal_date", "market_regime"]].dropna(subset=[ret_col, event_col]).copy()
        
        results["group_comparison"][f"{h}d"] = {}
        
        groups = [
            ("Group_A", hdf[hdf[event_col].isin(["Spring", "SC", "SOS"])]),
            ("Group_B", hdf[hdf[event_col].isin(["LPS", "AR", "ST", "UTAD"])])
        ]
        
        for g_name, gdf in groups:
            n_obs = len(gdf)
            if n_obs == 0:
                continue
            wins = int((gdf[net_ret_col] > 0).sum())
            win_rate = (wins / n_obs) * 100.0
            avg_net = float(gdf[net_ret_col].mean())
            med_net = float(gdf[net_ret_col].median())
            
            sum_win = gdf[gdf[net_ret_col] > 0][net_ret_col].sum()
            sum_loss = abs(gdf[gdf[net_ret_col] < 0][net_ret_col].sum())
            pf = float(sum_win / sum_loss) if sum_loss > 0 else 999.0
            
            wins_sorted = gdf[net_ret_col].sort_values(ascending=False)
            total_wins = gdf[gdf[net_ret_col] > 0][net_ret_col].sum()
            cnt_1 = max(1, int(np.ceil(0.01 * len(wins_sorted))))
            pct_1 = float(wins_sorted.head(cnt_1).sum() / total_wins * 100.0) if total_wins > 0 else 0.0
            
            # Yearly
            gdf["year"] = pd.to_datetime(gdf["signal_date"]).dt.year
            yearly_stats = {}
            for yr in sorted(gdf["year"].unique()):
                ydf = gdf[gdf["year"] == yr]
                yearly_stats[str(yr)] = round(ydf[net_ret_col].mean(), 2)
                
            results["group_comparison"][f"{h}d"][g_name] = {
                "trades": n_obs,
                "win_rate": round(win_rate, 2),
                "avg_net_ret": round(avg_net, 2),
                "med_net_ret": round(med_net, 2),
                "profit_factor": round(pf, 2),
                "top_1pct_wins_share": round(pct_1, 2),
                "yearly_avg_returns": yearly_stats
            }
            
            csv_rows_groups.append({
                "Horizon": f"{h}D",
                "Group": g_name,
                "Trades": n_obs,
                "WinRate": round(win_rate, 2),
                "AvgNetReturn": round(avg_net, 2),
                "MedNetReturn": round(med_net, 2),
                "ProfitFactor": round(pf, 2)
            })
            
    pd.DataFrame(csv_rows_groups).to_csv(DIAG_OUT_DIR / "group_comparison.csv", index=False)
    update_progress(85.0, "Group Comparison Complete", len(df), len(df), time.time() - t0)
    
    # --- EXPERIMENT 6: REGIME BREADTH PERFORMANCE ---
    print("\nRunning Breadth Regime performance breakdown...")
    results["regime_breadth"] = {}
    csv_rows_regimes = []
    
    for h in horizons:
        ret_col = f"fwd_ret_{h}d"
        net_ret_col = f"fwd_net_ret_{h}d"
        hdf = df[[net_ret_col, "market_regime"]].dropna(subset=[net_ret_col]).copy()
        
        results["regime_breadth"][f"{h}d"] = {}
        
        for reg in ["Bull", "Neutral", "Bear"]:
            rdf = hdf[hdf["market_regime"] == reg]
            n_obs = len(rdf)
            if n_obs == 0:
                continue
            wins = int((rdf[net_ret_col] > 0).sum())
            win_rate = (wins / n_obs) * 100.0
            avg_net = float(rdf[net_ret_col].mean())
            med_net = float(rdf[net_ret_col].median())
            
            sum_win = rdf[rdf[net_ret_col] > 0][net_ret_col].sum()
            sum_loss = abs(rdf[rdf[net_ret_col] < 0][net_ret_col].sum())
            pf = float(sum_win / sum_loss) if sum_loss > 0 else 999.0
            
            results["regime_breadth"][f"{h}d"][reg] = {
                "trades": n_obs,
                "win_rate": round(win_rate, 2),
                "avg_net_ret": round(avg_net, 2),
                "med_net_ret": round(med_net, 2),
                "profit_factor": round(pf, 2)
            }
            
            csv_rows_regimes.append({
                "Horizon": f"{h}D",
                "Regime": reg,
                "Trades": n_obs,
                "WinRate": round(win_rate, 2),
                "AvgNetReturn": round(avg_net, 2),
                "MedNetReturn": round(med_net, 2),
                "ProfitFactor": round(pf, 2)
            })
            
    pd.DataFrame(csv_rows_regimes).to_csv(DIAG_OUT_DIR / "regime_performance.csv", index=False)
    update_progress(90.0, "Regime Breadth Analysis Complete", len(df), len(df), time.time() - t0)
    
    # --- EXPERIMENT 7: FAT-TAIL SENSITIVITY ---
    print("\nRunning Outlier Exclusions...")
    results["fat_tail_exclusions"] = {}
    csv_rows_excl = []
    
    for h in horizons:
        net_ret_col = f"fwd_net_ret_{h}d"
        hdf = df[net_ret_col].dropna().copy()
        if len(hdf) == 0:
            continue
            
        sorted_ret = hdf.sort_values(ascending=False)
        n_trades = len(sorted_ret)
        
        results["fat_tail_exclusions"][f"{h}d"] = {}
        
        for pct in [0.5, 1.0, 2.0, 5.0, 10.0]:
            cnt_cut = max(1, int(np.ceil(pct / 100.0 * n_trades)))
            clean_arr = sorted_ret.iloc[cnt_cut:]
            
            avg_net = float(clean_arr.mean())
            med_net = float(np.median(clean_arr))
            wins = int((clean_arr > 0).sum())
            win_rate = (wins / len(clean_arr)) * 100.0
            
            sum_win = clean_arr[clean_arr > 0].sum()
            sum_loss = abs(clean_arr[clean_arr < 0].sum())
            pf = float(sum_win / sum_loss) if sum_loss > 0 else 999.0
            
            avg_win = float(clean_arr[clean_arr > 0].mean()) if wins > 0 else 0.0
            avg_loss = float(clean_arr[clean_arr < 0].mean()) if (len(clean_arr) - wins) > 0 else 0.0
            expectancy = (win_rate / 100.0 * avg_win) + ((100.0 - win_rate) / 100.0 * avg_loss)
            
            results["fat_tail_exclusions"][f"{h}d"][f"excl_{pct}pct"] = {
                "trades_remaining": len(clean_arr),
                "win_rate": round(win_rate, 2),
                "avg_net_ret": round(avg_net, 2),
                "med_net_ret": round(med_net, 2),
                "profit_factor": round(pf, 2),
                "expectancy": round(expectancy, 2)
            }
            
            csv_rows_excl.append({
                "Horizon": f"{h}D",
                "ExcludedPercentile": f"{pct}%",
                "TradesRemaining": len(clean_arr),
                "WinRate": round(win_rate, 2),
                "AvgNetReturn": round(avg_net, 2),
                "MedNetReturn": round(med_net, 2),
                "ProfitFactor": round(pf, 2),
                "Expectancy": round(expectancy, 2)
            })
            
    pd.DataFrame(csv_rows_excl).to_csv(DIAG_OUT_DIR / "fat_tail_exclusions.csv", index=False)
    update_progress(100.0, "All Experiments Complete", len(df), len(df), time.time() - t0)
    
    # Save final JSON results
    with open(RESULTS_JSON, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nWritten Phase 17 JSON results to {RESULTS_JSON}")

if __name__ == "__main__":
    run_diagnostics()
