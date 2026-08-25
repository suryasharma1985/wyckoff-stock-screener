import time
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import pandas as pd
from wyckoff_screener.data_loader import validate_ohlcv_dataframe
from wyckoff_screener.wyckoff.schematic_events import detect_all_schematic_events
from wyckoff_screener.pointfigure.pf_chart import build_point_and_figure_chart
from wyckoff_screener.scanning.broad_filter import evaluate_broad_setup
from wyckoff_screener.scoring.setup_scorer import score_setup

df = pd.read_csv("data/cache/ANANTRAJ.NS.csv")
v_df = validate_ohlcv_dataframe(df)
as_of = "2024-03-28"
pit_df = v_df[v_df["Date"] <= as_of].copy()

t0 = time.perf_counter()
for _ in range(20):
    broad = evaluate_broad_setup(pit_df, symbol="ANANTRAJ")
t_broad = (time.perf_counter() - t0) / 20

t0 = time.perf_counter()
for _ in range(20):
    ev = detect_all_schematic_events(pit_df)
t_events = (time.perf_counter() - t0) / 20

t0 = time.perf_counter()
for _ in range(20):
    cols, bs = build_point_and_figure_chart(pit_df)
t_pf = (time.perf_counter() - t0) / 20

t0 = time.perf_counter()
for _ in range(20):
    sc = score_setup(pit_df, symbol="ANANTRAJ")
t_score = (time.perf_counter() - t0) / 20

print(f"Timing Breakdown per Stock-Date Evaluation:")
print(f"  1. evaluate_broad_setup:            {t_broad*1000:.2f} ms")
print(f"  2. detect_all_schematic_events:     {t_events*1000:.2f} ms")
print(f"  3. build_point_and_figure_chart:    {t_pf*1000:.2f} ms")
print(f"  4. full score_setup:                {t_score*1000:.2f} ms")
print(f"  Total per evaluation:               {(t_broad + t_score)*1000:.2f} ms")
