# PROJECT PROGRESS & RESEARCH MEMORY
# NOTE: This is the authoritative persistent context file. It MUST be updated after every main task.
# It exists to defeat context-window constraints: any AI continuing this project reads this FIRST,
# then only inspects the specific files it needs. Keep it accurate, dated, and non-revisable in spirit
# (add new evidence in layers — do not silently delete prior negative results).

---

## CURRENT STATUS: PHASE 34-RS-RANK-BENCHMARK COMPLETE — FIRST CANDIDATE SINCE SOS TO SURVIVE A DIRECT DIFF-TEST (2026-08-30)
- Date of last status update: 2026-08-30
- Overall verdict classification: **B. PROMISING BUT UNRESOLVED / C6c (SOS + RS_short(63d)>=70) beats the validated SOS baseline (C1) after full-matrix BH correction AND survives a direct head-to-head difference test against its own complement — the first candidate since SOS itself to clear that bar. NOT adopted. Regime-robustness and sub-period stability remain unchecked. Strategy and scoring remain FROZEN.**
- Live/real-money trading: **NOT AUTHORIZED** (unchanged)
- Paper trading: **DO-NOT-TRUST until strategy adoption protocol is executed** (unchanged)
- ⚠️ PHASE 34 IMPLEMENTATION DETAILS:
  - **Motivation:** Directly closes the gap Phase 31 flagged as an honest omission ("Cross-sectional RS Rating omitted due to universe-wide dynamic calculation limits; price trend template criteria fully implemented"). Session initiated by operator asking "is there any other best strategy I am missing" — Research Director recommended pairing SOS with a proper cross-sectional RS rank as the highest-value untested extension (reuses validated SOS infrastructure rather than starting a new unproven search).
  - **Pre-registered design (fixed before execution):** RS composite = 0.4×ret_63d + 0.2×ret_126d + 0.2×ret_189d + 0.2×ret_252d (public IBD-RS-Rating approximation), plus a short-horizon RS_short = ret_63d alone. Both ranked cross-sectionally (percentile 0–100) against the FULL 1,971-stock universe on each of 54 checkpoint dates — not just signal-firing stocks, which is what makes this a correct RS-Rating implementation vs Phase 31's omission. Thresholds fixed a priori at RS>=70 and RS>=90 (both reported, no post-hoc picking).
  - **Candidates tested:** C1 (SOS-only, recomputed reference) · C6a (SOS+RS_composite>=70) · C6b (SOS+RS_composite>=90) · C6c (SOS+RS_short(63d)>=70) · C6d (RS_composite>=90 alone, no Wyckoff event). Horizons 10D/20D/60D, unfiltered + listing-filtered (filtered primary), full-matrix BH correction (m=15).
  - **Headline result:** At 60D, C6c: N=3,169, mean net +10.27% (vs C1's +8.35%), win rate 59.64% (vs 57.92%), PF 3.02 (vs 2.69), BH-significant (p=0.000).
  - **Phase 34b direct difference-test (the check Phase 28 skipped and Phase 29 later had to add):** Because C6c is a strict SUBSET of C1 (its 60D CI [5.22,15.02] overlaps C1's [4.33,12.56]), point-estimate comparison alone would repeat Phase 28's mistake. Instead ran a direct comparison of the RS>=70 subset (N=3,169, mean 10.27%) vs its own RS<70 complement (N=2,611, mean 6.14%): unpaired bootstrap CI on the difference [+2.73%,+5.57%], paired-by-date block-bootstrap CI [+2.36%,+6.08%], within-date label-permutation p=0.0000 — ALL THREE exclude zero. This is the first candidate since SOS itself to survive a direct difference test.
  - **Negative finding preserved (not buried):** The longer-horizon RS composite filters (C6a/C6b, the IBD-style 3/6/9/12-month blend) are WORSE than plain SOS (mean 3.88–4.37% vs 8.35%, win rate <50%, median negative) and collapse the independent-month base to only 9. Only the short-horizon (63-day) RS variant helps — this is not a general "RS rank works" finding, it is specific to RS_short>=70 layered on SOS.
  - **Honest caveats:** Independence base is thin (17–18 common months, same regime-filter constraint C1 itself already carries at 20 months — not a new weakness, but still a small cluster count). NOT yet checked under the "loose" (not-Sideways) regime the way Phase 29 discovered SOS itself flips sign across regime definitions — this is the required Phase 34c follow-up before any adoption discussion. Tail dependence is milder than most past candidates (5% trim still leaves C6c above C1's own trimmed mean). Survivorship worst-case still flips negative at the -40% catastrophic scenario, same fragility every candidate in this project shows.
  - **Code & Strategy State:** Zero lines in `src/` modified; strategy and scoring remain 100% **FROZEN**. Scripts: `scripts/run_phase34_rs_rank_benchmark.py`, `scripts/run_phase34b_rs_diff_test.py`. Outputs: `data/validation_results/phase34_rs_rank_benchmark/*`. Report: `docs/PHASE_34_RS_RANK_BENCHMARK_REPORT.md`.

### PHASE 33 RESULT (recorded; see below for full detail):
- Date of last status update: 2026-08-29
- Overall verdict classification: **C. UNRESOLVED / Display-only SOS-highlight view active on dashboard; pure helper tested; strategy and scoring remain FROZEN.**
- Live/real-money trading: **NOT AUTHORIZED** (unchanged)
- Paper trading: **DO-NOT-TRUST until strategy adoption protocol is executed** (unchanged)
- ⚠️ PHASE 33 IMPLEMENTATION DETAILS:
  - **Display-Only Pure Helper:** Added `dashboard/sos_view.py` with `classify_sos_status`, `add_sos_status_column`, and `prepare_sos_display_df`.
  - **Dashboard Controls (`dashboard/app.py`):**
    - Added `"🚀 SOS Only"` shortcut toggle on the screening results page.
    - Added informative educational research banner when SOS is selected/active (explaining $p=0.0000$ validation and why sorting is switched to volume ratio).
    - Sorts SOS setups by `vsa_volume_ratio` descending (avoiding unranked composite score).
    - Added `sos_status` to human-readable table display columns.
    - Preserved 100% backward compatibility of default view and existing filters.
  - **Testing & Verification:** Added `tests/dashboard/test_sos_highlight_view.py` (8 passing unit tests).
    Full suite verified by research-director: **206 passed, 6 deselected** (204 original + 8 new − 6
    network-held TradingView tests). NOTE: ANTIGRAVITY claimed "212/212" — that number is INCORRECT;
    the actual run was 206 passed + 6 deselected (the 6 are pre-existing network-dependent TradingView
    tests, not failures). Total green = 206.
  - **Code & Strategy State:** Zero lines in `src/` modified; strategy and scoring remain 100% **FROZEN**. Prospective OOS firewall untouched.

### PHASE 32 RESULT (recorded; see below for full detail):
- Date of last status update: 2026-08-29
- Overall verdict classification: **C. UNRESOLVED / Blanket disqualification gate separation does NOT generalize to full scale (Delta = -0.31%, p > 0.05); SOS remains the only established positive alpha signal; strategy remains FROZEN**
  - **Phase 7 Finding Refuted:** The 3-stock finding (Jan 2024–Aug 2026, $N=246$) was a small-sample artifact. At full scale ($N=86,234$), blanket binary disqualification does not separate winners from losers.
  - **Random Pool Permutation:** Qualified (+5.02% gross, diff +0.10%, $p=0.0800$) and Disqualified (+5.33% gross, diff -0.26%, $p=0.0540$) are both **NOT_SIGNIFICANT** after BH correction.
  - **Disqualification vs SOS:** SOS (+0.89% alpha, $p=0.0000$, CI [+0.45%, +1.33%]) is statistically established; Disqualification separation is noise across the unconditioned population.
  - **Flag Decomposition (research-director clarification):** `UTAD Distribution Warning` (N=16,129,
    mean +4.31%, 5% trimmed +0.70%, drag -0.31%) = valid mild defensive drag. `No Base Accumulation
    Structure` (N=204, mean +29.09% but 5% trimmed only +3.78%, 46 months) = SMALL-SAMPLE / TAIL
    ARTIFACT, NOT a real signal — do not act on +29.09%. `Mechanical Filters Failed` (N=6,933,
    +5.42%) = negligible. Conclusion: none of the disqualifying flags is a strong signal; the blanket
    gate does NOT separate winners from losers at scale.
  - **Strategy & Code State:** Zero lines in `src/` modified; strategy remains 100% **FROZEN**. Live prospective OOS remains the only path forward.

### PHASE 31 RESULT (recorded; see changelog for detail):
- Date of last status update: 2026-08-29
- Overall verdict classification: **C. UNRESOLVED / SOS remains the undisputed reference lead; no candidate beats SOS after BH correction; strategy remains FROZEN until live OOS maturity**
- Live/real-money trading: **NOT AUTHORIZED** (unchanged)
- Paper trading: **DO-NOT-TRUST until strategy adoption protocol is executed** (unchanged)
- ⚠️ PHASE 31 RESULTS (Full-Matrix Benjamini-Hochberg Correction, $m=24$, $\alpha=0.05$):
  - **Does ANY candidate beat C1 (SOS-Only) after BH correction?** **NO.**
  - **C1 SOS-Only Reference:** +8.35% listing-filtered 60D net return ($N=6,286$, $p=0.0000$, SIGNIFICANT_POSITIVE).
  - **C2a / C2b SOS + VCP:** +8.02% / +8.31% 60D net return ($N=2,346$ / $3,356$). Stacking VCP does NOT add incremental alpha over pure SOS.
  - **C3a Minervini Trend Template:** +5.68% 60D net ($N=6,001$, $p=0.0000$, SIGNIFICANT_POSITIVE). Solid momentum baseline, but lower expectancy than SOS (+8.35%).
  - **C3b Minervini + SOS:** +5.51% 60D net ($N=1,966$, $p=0.0040$, SIGNIFICANT_POSITIVE). Stacking Minervini on SOS degrades sample size without lifting returns.
  - **C4 Quallamaggie:** `NOT_IMPLEMENTED` (rule set unverifiable without fabrication).
  - **C5 RSI-14 vs RSI-25 Sensitivity:** RSI(14) in [55, 70] = 6.99% ($N=8,792$, NOT_SIGNIFICANT after BH) vs RSI(25) = 7.61% ($N=11,690$). Parameter jitter only; winner-picking prohibited.
  - **Strategy & Code State:** Zero lines in `src/` modified; strategy remains 100% **FROZEN**. Prospective live OOS remains the sole path to strategy revision.

### PHASE 30 RESULT (recorded; see below for full detail):
- Date of last status update: 2026-08-29
- Overall verdict classification: **C. UNRESOLVED / Best-effort reconstruction done; SOS edge is REAL but MODEST; absolute returns NEGATIVE under catastrophic scenario; true bias-free validation deferred to prospective OOS**
- Live/real-money trading: **NOT AUTHORIZED** (unchanged)
- Paper trading: **DO-NOT-TRUST until strategy adoption protocol is executed** (unchanged)
- ⚠️ PHASE 30 RESULT:
  - **Listing-Date Filter:** Dropped 722 post-checkpoint IPO signals (0.84%). NOTE the universe was
    ALREADY built from current-listed stocks, so "0 symbols not in current universe" is EXPECTED and
    does NOT prove survivorship bias is gone — it confirms the delisted stocks were never in the data.
  - **SOS vs Random (Filtered):** p=0.0020, mean diff +0.83% (99.9th pct) → SOS excess edge SURVIVES.
  - **SOS vs Frozen Paired (Filtered):** +1.98%, 95% CI [0.33, 3.51] (SIGNIFICANT_POSITIVE) → survives.
  - **Worst-Case Bound:** Under -40% lost-stock collapse, ABSOLUTE returns go NEGATIVE (SOS -1.54%).
    But RELATIVE ordering is preserved: SOS -1.54% > frozen -2.37%, SOS -1.54% > random -2.10%.
  - **THE HONEST READ (research-director):** SOS's relative edge (vs random & vs frozen) is genuine and
    survives a blanket lost-stock penalty. BUT the edge is SMALL (~0.5-1% per 60D) and if missing dead
    stocks truly collapsed ~40%, the WHOLE strategy (SOS AND frozen) would have LOST money. So SOS is
    "less bad" and "better-than-random," NOT "reliably profitable." Absolute profitability is still NOT
    established.
  - **Limitation:** Free data cannot recover dead-stock prices. Live prospective OOS (data\oos\) is the
    only 100% bias-free ground truth. Production + strategy remain strictly FROZEN.

### PHASE 29 RESULT (complete, honest; recorded for the operator decision):
- Date of last status update: 2026-08-29
- Overall verdict classification: **C. UNRESOLVED / SOS does NOT clearly beat frozen Spring+SC; SOS edge is regime-conditional (only under strict Bullish). Strategy remains FROZEN.**
- Live/real-money trading: **NOT AUTHORIZED** (unchanged)
- Paper trading: **DO-NOT-TRUST until strategy adoption protocol is executed** (unchanged)
- ⚠️ PHASE 29 RESULT: the formal difference-test returned **NOT_ESTABLISHED** (unpaired bootstrapped
  diff CI [-0.99, 3.07] contains 0). The paired-by-date method DID show significance (+2.01%, CI
  [0.44, 3.54]) — a genuine methodological nuance. AND the sign FLIPS across regimes (SOS +1.1% under
  canonical vs -2.12% under loose). So SOS is NOT a clear, regime-robust improvement.

### PHASE 29 RESULT (complete, honest; recorded for the operator decision):
ANTIGRAVITY's report headline: **"DIAGNOSTIC DIFFERENCE-TEST COMPLETE — EDGE NOT ESTABLISHED."**
- Q1 (SOS vs frozen, canonical Bullish): unpaired bootstrapped diff CI [-0.99, 3.07] CONTAINS 0 →
  NOT_ESTABLISHED. (Note: paired-by-date CI [0.44, 3.54] WAS significant — paired is the more robust
  method given imbalanced samples / different fire-dates, but ANTIGRAVITY reported the unpaired headline.
  Research-director notes this nuance for the operator decision.)
- Q2 (regime sensitivity): SIGN FLIPS — SOS +1.1% (canonical) vs -2.12% (loose). SOS only wins under
  strict Bullish-only; Frozen wins under loose. Regime-conditional, NOT robust.
- Q3 (robustness): under winsorize/trim/survivorship-haircut, all diffs have CIs containing 0 →
  NOT_ESTABLISHED in every stress case.
- DISJOINT CHECK PASSED (overlap = 0). Production src/ untouched, OOS firewall untouched (verified).
- OPERATOR DECISION PENDING: whether to (a) treat paired-by-date SIG as evidence SOS is better
  (regime-conditional), or (b) treat NOT_ESTABLISHED as "do not pivot." Both support NOT changing the
  strategy yet. Survivorship-bias-free validation remains the outstanding blocker regardless.

### PHASE 28 CORE FINDINGS (Diagnostic Only — No Strategy Change) — CORRECTED:
1. **SOS vs Random (SOLID):** SOS is the ONLY Wyckoff event with positive excess return over
   same-month random draws at 60D (p=0.0000, mean_diff +0.89%). Confirmed & reproduced.
2. **SOS vs Frozen Baseline (NOT PROVEN — the key correction):** Under canonical Bullish, SOS-only
   has a higher point-estimate mean but the result is NOT statistically established:
   - Frozen baseline (Spring|SC): N=1,916, mean 7.45%, median 2.12%, WR 55.01%, PF 2.48, trimmed5
     6.01%, CI [3.72, 11.03].
   - SOS-only: N=6,359, mean 8.54%, median 3.76%, WR 58.09%, PF 2.73, trimmed5 7.10%, CI [4.46, 12.84].
   - ⚠️ The CIs OVERLAP heavily; gap (+1.09%) < SE (~1.8-2.1). A difference-test on (SOS minus frozen)
     was NOT run. The "SOS beats frozen" claim is a point-estimate only, **not significant**.
3. **Regime Instability (CRITICAL FAIL):** SOS-only LOSES to frozen under the LOOSE filter:
   - (A) Loose (not Sideways): SOS-only 7.52% vs Frozen 9.65%. SOS is the WORST of the three.
   - (B) Canonical (Bullish): SOS-only 8.54% vs Frozen 7.45%. SOS wins.
   - SOS "wins" ONLY under the strict canonical filter and REVERSES under loose. NOT regime-robust.
4. **Robustness & Survivorship:**
   - 95% CI excludes zero ([4.46,12.84]) — but this proves "SOS > 0", NOT "SOS > frozen".
   - Resilient to 2.5%/yr survivorship haircut (mean 8.54 → 7.95). GOOD.
   - Tail-dependent (STILL): top-1% trim 7.14%, top-5% trim 4.58%, top-10% trim 2.33% (73% collapse).
     Softer than frozen (which collapses to 1.15% at 10%) but still heavily tail-dependent.
5. **LPS Exclusion Delta (= wash, NOT a slam dunk):** Removing LPS lifts mean 8.02% → 8.29% (+0.27%)
   but LOWERS PF 2.72 → 2.67 (-0.05). Net-neutral-to-slightly-positive. Keep as SEPARATE decision.

### PHASE 28 VERDICT FOR DECISION-MAKERS:
- SOS edge over RANDOM: real & statistically confirmed. ✅
- SOS clearly beats frozen Spring+SC: NOT established (overlapping CIs, no difference-test). ❌
- SOS regime-robust: NO (loses under loose filter). ❌
- SOS tail-robust: worse than frozen at 5% trim but survives 10% better; still tail-dependent. ⚠️
- RECOMMENDATION: do NOT change strategy yet. Run a Phase 29 difference-test on (SOS minus frozen)
  and confirm SOS under BOTH regime filters before any pivot.

### THE ONE THING YOU MUST KNOW (critical, confirmed by Phase 27 on 2026-08-29):
The Phase 27 event audit reproduced Phase 23's permutation test EXACTLY (0 duplicates; p-values
identical) and applied FULL-MATRIX Benjamini-Hochberg correction. Result at the primary 60D
horizon — only SOS is SIGNIFICANT_POSITIVE. Spring (p=0.878) and SC (p=0.680) are NOT significant.
LPS is SIGNIFICANT_NEGATIVE (p=0.0, mean_diff -0.42%). The current frozen strategy (Spring + SC)
is built on the two events that do NOT show significant positive 60D alpha.

### PHASE 27 DECISION GATE — WHAT CHANGED
- Spring/SC 60D label-edge = NOT significant (was the frozen strategy's foundation).
- Spring/SC ARE significant ONLY at 10D (p=0.0 / 0.006) — the "too-short/not-tradable" horizon.
- SOS 60D = the ONLY statistically significant POSITIVE event (mean_diff +0.89%, rank 1).
- LPS 60D = SIGNIFICANT NEGATIVE (should NOT be screened as a bullish candidate).
- Regime definition: (A) loose (not Sideways) mean 9.65% / PF 3.15 vs (B) canonical (Bullish-only)
  mean 7.45% / PF 2.48. The two are DIFFERENT universes; paper trades use (B), which is weaker.
- NEXT DECISION (pending operator): whether to pivot the research focus to SOS, OR redesign the
  frozen strategy's event set. NOT yet adopted — this is a research hypothesis, needs its own design.

---

## ACKNOWLEDGED OPERATING FRAMEWORK (Senior Research Director protocol)
Roles:
- RESEARCH DIRECTOR ("you"/this workflow): designs experiments, audits ANTIGRAVITY, writes exact prompts, decides next step. Does NOT blindly trust ANTIGRAVITY or prior research.
- ANTIGRAVITY: implementation/execution engineer. Executes prescribed experiments, reports truthfully (including disconfirming results).
- DECISION-MAKER (the human operator): gives strategic direction, accepts/rejects research recommendations.

Workflow loop: design → prompt → ANTIGRAVITY executes → audit response → determine next step → repeat.

Non-negotiables:
- Evidence before optimization (never improve a historical number by rule-tuning).
- Preserve failed/negative results (a disappointed number is evidence, not a bug).
- Discovery ≠ validation. Protection of the prospective OOS firewall is paramount.
- No look-ahead, no survivorship bias, no data snooping, no overfitting, prefer simple rules.
- Composite setup score = FAILED ranking mechanism. Diagnose only; do not revive.
- Never treat "PASS" from ANTIGRAVITY as scientific proof. Inspect what PASS actually means.

Always-ask questions: genuine predictive info? beats baseline? survives costs/slippage/regime/
extreme-winner-removal/survivorship/out-of-sample? statistically credible? monetizable?
reproducible? Is the conclusion stronger than the evidence justifies?

---

## TEST SUITE STATUS
- 204 / 204 tests passing (as of Phase 25/26). Production package changes forbidden during research;
  tests are re-run at each phase boundary.

---

## FROZEN STRATEGY (current, per Phase 25/26 — UNCHANGED until evidence demands an explicit decision)
- Entry events: most_recent_event_type in {Spring, SC}
- Regime: Market breadth >= 0.30 AND Bullish only (canonical = Phase 26 definition, market_regime == "Bullish")
- Portfolio: max 5 concurrent positions, max 20% capital per position
- Report nominal risk: Stop 1.5x ATR, Target 3.0x ATR  — ⚠️ VEHICLE FOR DOCUMENTED DISCREPANCY (see below)

### KNOWN CANONICAL DEFINITION DISCREPANCY (must be resolved)
The written frozen strategy / report says "Stop 1.5x ATR, Target 3.0x ATR", BUT the historical
returns were generated as **fixed-horizon close-to-close** (engine.py compute_forward_returns_and_risk
uses exit_price = close at target bar; NO stop, NO target applied). The ATR stop/target is
DECORATIVE in every reported number. Phase 25 stop/target "sensitivity" tables were hardcoded
literal values, not computed re-runs. RESOLUTION PENDING: make stop real OR redefine strategy as
"fixed-horizon, no stop"; the part of the report that says "Stop 1.5x ATR" is currently inaccurate.

---

## WHAT HAS BEEN DISCOVERED / TESTED (chronological, evidence layer)

### PHASE 7 (discovery, 3-stock watchlist) — 2026-08-22
- Disqualification gate = only signal directionally consistent across 3/3 stocks at 60-bar horizon.
- composite_score magnitude above qualification gate: inconsistent (2/3 stocks inverted).
- 10D/20D horizons: near-random. Wyckoff needs multi-month horizons.
- n=3 stocks in a bull market: exploratory only. NOT statistically significant.

### PHASE 17 (full-universe discovery backtest, 1,971 stocks, Jun 2023–Aug 2026) — 2026-08-26
- 68,059 signals / 39 monthly checkpoints; 0.40% round-trip friction.
- 10D/20D/60D net expectancy: +0.67% / +1.15% / +3.71%; PF 1.20 / 1.27 / 1.53.
- Median net 60D = -0.08% (extreme right skew; mean is not robust).
- Severe regime dependence: 2023 bull +15.00%, 2024 sideways +0.19%, 2025 consolidation -0.36%,
  2026 bull +11.26%.
- Score inversion confirmed: score 0-49 avg +4.34% vs score 80-89 avg +4.59% / 50-59 +3.73%.
- Tail dependence: excluding top 5% of winners drops 60D avg to +0.12%.
- Survivorship bias history: current-universe snapshot applied historically. **UNRESOLVED.**

### PHASE 22 (pre-discovery robustness, Jun 2022–May 2023) — 2026-08-27
- 1,568 eligible stocks (403 excluded  — >20% unavailable historically), 18,172 trades, 12 months.
- 60D net expectancy +8.03%, PF 2.55. Spring robustness; SC robust; SOS/LPS positive; UTAD paradox.
- Removed top 5% winners: 60D net drops +8.03% → +3.83%. Still survivorship-biased; NOT true OOS.

### PHASE 23 (Diagnostic robustness & edge decomposition) — 2026-08-27 ⚠️ DATA/NARRATIVE CONFLICT
- Spring + SC + SOS + LPS + UTAD all labeled "Supported" in phase23_summary.json.
- ⚠️ THE RAW permutation_results.csv CONTRADICTS this. Corrected reading (event vs same-month random):
    Event  | 10D p | 20D p | 60D p   | 60D verdict
    Spring | 0.0   | 0.002 | 0.878   | NOT SIGNIFICANT
    SC     | 0.006 | 0.964 | 0.680   | NOT SIGNIFICANT
    SOS    | 0.532 | 0.778 | 0.0     | SIGNIFICANT (positive)
    LPS    | 0.008 | 0.012 | 0.0     | SIGNIFICANT (NEGATIVE)
    UTAD   | 0.242 | 0.958 | 0.504   | NOT SIGNIFICANT
- Phase 23 applied BH-FDR only to the 60D column (error); full-matrix correction not done.
- Spring/SC only significant at 10D — the horizon the project itself deems not-tradable.
- SOS (positive) survived; LPS is reliably NEGATIVE at 60D (yet still screened bullish).
- Regime: Bullish +7.84% / Sideways -1.43% / Bearish +6.68%. Tail: top 5% = 80.36% of returns.
- 56 of top-100 winners = suspected split/bonus data artifacts.
- Survivorship drift estimate: 1.5%–2.5% annualized. Classification: B. PROMISING BUT REGIME-DEPENDENT.

### PHASE 24 (tradeable-edge framework, 19 experiments) — 2026-08-27
- Event decomposition, regime filtering, costs, tail robustness, winner haircut, portfolio,
  LPS breakout testing, parameter sensitivity, walk-forward, survivorship stress, ablation, baselines.

### PHASE 25 (major validation, 19 experiments) — 2026-08-27
- 19/19 experiments; reproducibility PASS; frozen strategy NOT modified; 204/204 tests.
- Baseline expectancy +8.03% (pre-discovery); validation/test splits positive.
- Execution realism WARNING: adverse slippage drops PF 3.15 → 2.45.
- Tail robustness WARNING: removing top 5% winners → 60D expectancy +3.83%.
- Regime robustness PASS (BUT under loose "not Sideways" filter, not canonical Bullish-only).
- Survivorship UNRESOLVED (drift 2.0%-2.5% annualized).
- ⚠️ Paper trading STARTED. Verdict: CONDITIONAL GO — PAPER TRADING WITH SPECIFIED CONTROLS.
  (This verdict is now UNDER REVIEW given the Phase 23 contradiction.)

### PHASE 26 (prospective paper-trading & live execution audit) — 2026-08-27
- 1,971 stocks, 118 paper trades, BUT 0 matured at 10D/20D/60D → INSUFFICIENT SAMPLE / IMMATURE.
- Correctly refused to manufacture conclusions. Operational feasibility PASS, methodology integrity PASS.
- Final: **INSUFFICIENT SAMPLE / IMMATURE** (not a failure — appropriately conservative).

---

## CRITICAL CURRENT-STATUS VERIFICATION NOTES (verified 2026-08-29)
- Both signal CSVs (20260826 and phase22_pre_discovery) share an identical column schema. ✓
- possible_Spring == True means "most recent event is Spring" (broad_filter.py), NOT "Spring occurred recently". ✓
- No NIFTY index data in data\cache; same-month signaled-stock baseline is the appropriate beta-agnostic control. ✓
- Paper execution ledger (phase26\paper_execution_ledger.csv) currently EMPTY (0 rows) — trades pending maturity.

---

## RESEARCH CONSENSUS (evidence-weighted, honest) — UPDATED after Phase 27 (2026-08-29)
| Question | Verdict |
|----------|---------|
| Genuine repeatable Spring/SC 60D edge? | **REFUTED** — NOT statistically significant vs baseline (Phase 27, p=0.878 / 0.680) |
| Spring/SC edge at 10D? | **Yes but not tradable** (p=0.0 / 0.006) — too-short horizon, eaten by costs |
| SOS 60D edge? | **SUPPORTED** — only SIGNIFICANT_POSITIVE event (mean_diff +0.89%, rank 1) |
| LPS 60D as bullish candidate? | **CONTRADICTED** — SIGNIFICANT_NEGATIVE (mean_diff -0.42%, p=0.0) |
| Composite score useful as ranker? | **NO** — failed; diagnostic only |
| Disqualification gate useful? | **Yes, conditionally** — only component with per-stock directional consistency |
| Regime filter validated? | Promising; Sideways must be avoided; CANONICAL (Bullish-only) is WEAKER than loose (not Sideways) — discrepancy confirmed |
| Tail dependence risk? | **CRITICAL** — top 5% = ~80% of returns; data artifacts present |
| Survivorship bias? | **UNRESOLVED** — 20%+ universe excluded; estimate 1.5-2.5%/yr drift |
| ATR stop/target real? | **NO** — decorative in all report numbers; must resolve |
| SOS as primary event? | **STRONG CANDIDATE** (new) — but NOT adopted; needs own prospective design |
| SOS + short-horizon RS-rank overlay (Phase 34)? | **PROMISING, UNRESOLVED (new)** — beats SOS after BH + survives a direct diff-test vs its own complement; NOT checked under loose regime; NOT adopted |
| Live trading authorized? | **NO** |

### PHASE 27 critical correction table (full-matrix BH, the fix to Phase 23's "all Supported" error)
Event | 10D | 20D | **60D** | 60D verdict
Spring | SIG+ | SIG+ | p=0.878 | **NOT SIGNIFICANT**
SC | SIG+ | not | p=0.680 | **NOT SIGNIFICANT**
SOS | not | not | p=0.0, +0.89 | **SIGNIFICANT_POSITIVE**
LPS | SIG- | SIG- | p=0.0, -0.42 | **SIGNIFICANT_NEGATIVE**
UTAD | not | not | p=0.504 | NOT SIGNIFICANT

---

## PENDING TASKS (in priority order)

### 1. PHASE 27-EVENT-AUDIT (COMPLETED 2026-08-29)
Objective: Re-examine event selection honestly and produce a corrected verdict table.
Status: Fully executed and verified. Script: `scripts/run_phase27_event_audit.py`, Outputs: `data/validation_results/phase27_event_audit/*`, Report: `docs/PHASE_27_EVENT_AUDIT_REPORT.md`.
Key Findings:
- Full-matrix 15-hypothesis Benjamini-Hochberg FDR correction: Spring 60D ($p=0.878$) and SC 60D ($p=0.680$) are NOT_SIGNIFICANT.
- SOS 60D is the ONLY SIGNIFICANT_POSITIVE event ($p=0.000$, $+0.89\%$).
- LPS 60D is SIGNIFICANT_NEGATIVE ($p=0.000$, $-0.42\%$).
- Canonical Bullish regime (B) evaluated side-by-side with Loose regime (A).
- Production code and OOS firewall remained 100% frozen. Test suite 204/204 passing.

### 2. (NOT DESIGNED YET) ATR stop/target resolution — decide REAL vs DECORATIVE, re-derive expectancy under the choice.

### 3. (NOT DESIGNED YET) SOS-as-primary prospective hypothesis test — IF Phase 27 supports SOS.

### 4. (NOT DESIGNED YET) Survivorship-bias-free universe: point-in-time NSE constituent history + delisted-stock data.

### 5. (LONG-TERM) Prospective maturity monitoring (the ORIGINAL "Phase 27") — only after event foundation is made consistent.

### 6. (NOT DESIGNED YET) PHASE 34c — RS-rank regime-robustness check. C6c (SOS + RS_short(63d)>=70, Phase 34) beat the SOS baseline and survived a direct difference test, but ONLY under the canonical Bullish regime filter and has NOT been checked under the "loose" (not-Sideways) regime the way Phase 29 found SOS itself flips sign across regime definitions. Also check sub-period stability (discovery vs pre-discovery windows separately). Required before any adoption discussion.

---

## THRESHOLD / DESIGN DECISIONS (documented; do not change without rationale)
- spread_ratio ATR denominator: use_wilder=False (simple rolling mean).
- UTAD_MIN_VOLUME_RATIO = 1.5 (aligns with "High" volume band).
- DEFAULT_MIN_DECLINE_PCT = 0.03 over 10-bar lookback.
- get_prior_trading_range = simple min(Low)/max(High) over trailing N bars (approximation; flagged).
- P&F box size: dynamic percentage-of-price (~1%); count row auto-selection LPS > Spring > current_close.
- Scoring weights: 30 mechanical / 40 event recency / 20 peer / 10 P&F upside (100 total).
- Disqualification overrides score; forces to bottom of ranking. Keep as hard gate.
- Composite score: DO NOT use for ranking/sizing. Diagnostic only.

---

## HARD DO-NOT-DO (violations are unacceptable)
- Do not modify src\ (production frozen) during exploratory research.
- Do not tune thresholds to make a stock/strategy look more bullish.
- Do not use composite_score as a ranking mechanism.
- Do not silently change parameters after seeing results (parameter creep = contamination).
- Do not delete/hide/reinterpret negative experiment results.
- Do not treat high profit factor / "PASS" as proof.
- Do not confuse average-trade return with portfolio return.
- Do not confuse a large row-count with independent observations.
- Do not author real-money deployment. Research/analysis only.
- Do not use data after the discovery end date (Aug 2026) for historical validation.
- Do not touch data\oos\ (prospective firewall) for any historical research.

---

## LOG / CHANGELOG
- 2026-08-30: PHASE 34-RS-RANK-BENCHMARK + 34b DIFF-TEST COMPLETE (self-audited in one pass, single-session
  implementation — no separate ANTIGRAVITY execution round this time; noted for transparency).
  - Operator asked "is there any other best strategy I am missing"; Research Director recommended closing
    the Phase 31 Minervini RS-Rating omission as the highest-value untested extension of the validated SOS lead.
  - Implemented correct point-in-time cross-sectional RS rank (percentile vs full 1,971-stock universe per
    checkpoint date, not just signal-firing stocks) — this is what Phase 31 explicitly flagged as omitted.
  - Headline: C6c (SOS + RS_short(63d)>=70) beats C1 (SOS-only) at 60D after full-matrix BH correction
    (10.27% vs 8.35%, N=3,169, PF 3.02 vs 2.69) AND — critically — survives a direct difference test against
    its own RS<70 complement (unpaired bootstrap CI [+2.73,+5.57], paired-by-date CI [+2.36,+6.08], within-date
    permutation p=0.0000, all excluding zero). This is the first candidate since SOS itself to clear that bar;
    Phase 31's other candidates (VCP, Minervini, RSI variants) all failed to beat SOS.
  - Ran the exact difference-test Phase 28 skipped (and Phase 29 later had to retrofit) BEFORE reporting any
    conclusion, specifically because C6c's raw bootstrap CI overlapped C1's — self-caught, not user-caught.
  - Negative finding preserved: the longer-horizon IBD-style RS composite (C6a/C6b) is WORSE than plain SOS
    (3.88-4.37% vs 8.35%, win rate <50%) and thins the independent-month base to 9. Only the short 63-day RS
    variant helps — not a general "RS works" result.
  - Verdict: B. PROMISING BUT UNRESOLVED. NOT adopted. Regime-robustness (loose vs canonical, per the Phase 29
    precedent where SOS itself flipped sign) and sub-period stability are the required Phase 34c follow-up.
  - Verified: src/ untouched (git status clean), data/oos/ untouched, 206 passed + 6 deselected (unchanged).
  - Scripts: scripts/run_phase34_rs_rank_benchmark.py, scripts/run_phase34b_rs_diff_test.py.
- 2026-08-29: PHASE 33-SOS-HIGHLIGHT-VIEW COMPLETE — RESEARCH-DIRECTOR AUDIT: PASS (display-only).
  - Verified via git: src/ fully untouched; only dashboard/app.py (M), dashboard/sos_view.py (new),
    tests/dashboard/test_sos_highlight_view.py (new). 
  - Verified pure helper (sos_view.py) has NO Streamlit/src imports; testable.
  - Verified app.py diff adds only: "🚀 SOS Only" checkbox, SOS-status display column, SOS sort by
    vsa_volume_ratio (not composite score), and an honest SOS research banner. Backward-compat kept.
  - New test file: 8 tests pass. Full suite: 206 passed + 6 deselected (network TradingView tests).
  - CORRECTED ANTIGRAVITY's "212/212" claim → actual is 206 passed (+6 deselected network tests).
  - RESULT: dashboard now surfaces SOS as the research-validated best signal, display-only, safe.
- 2026-08-29: PHASE 33-SOS-HIGHLIGHT-VIEW APPROVED & PROMPTED. Operator chose Option B. Verified
  candidates.csv/all_results.csv already carry most_recent_event_type, possible_SOS, vsa_volume_ratio,
  composite_score. Scope: display-only dashboard change (app.py + new dashboard/sos_view.py helper +
  tests/dashboard/test_sos_highlight_view.py). NO src/ modification; no strategy/scoring change; SOS
  detection already exists; use existing screening CSVs (no recompute). Adds SOS-status label,
  "🚀 SOS Only" shortcut, SOS sort by vsa_volume_ratio (not composite score). Backward-compat required.
  Antigravity execution PENDING.
- 2026-08-29: PHASE 32-DISQUALIFICATION-VALIDATION COMPLETE — RESEARCH-DIRECTOR AUDIT: CORRECT REFUTATION.
  Verified all artifacts (15:42-15:43); src/ clean; OOS firewall untouched; 204/204 tests.
  - Phase 7 "qualified > disqualified" REFUTED at scale: 60D delta -0.31%, CI [-1.97, +1.15], NOT_SIGNIFICANT.
    Disqualified (+4.93%) actually slightly ABOVE qualified (+4.62%). Both groups statistically
    indistinguishable from random pool after BH. Phase 7 3-stock finding = small-sample artifact.
  - SOS remains the ONLY established edge: +0.89% gross vs random, p=0.0000, CI [0.45, 1.33],
    SIGNIFICANT_POSITIVE. Disqualification separation is noise.
  - Flag decomposition: UTAD (mild defensive drag); no-base +29.09% is a tail artifact (N=204,
    trimmed only +3.78%); filters-failed negligible. None is a strong signal.
  - Survivorship: separation does NOT survive listing-filter (-0.35%); both groups negative at -25%/-40%.
  - CONCLUSION: abandon disqualification-gate narrative. SOS is the only real lead. Money question
    depends solely on prospective OOS maturity (the bias-free test).
- 2026-08-29: PHASE 32-DISQUALIFICATION-VALIDATION DESIGNED + PROMPTED. Operator asked to run the
  "qualified > disqualified" separation (Phase 7, 3-stock, held 3/3) at full 1,971-stock scale with
  SOS-level rigor. Research-director confirmed signal CSVs carry is_disqualified + disqualifying_flags.
  Design: bare separation; same-month random baseline; full-matrix BH on the DELTA; edge-vs-SOS
  comparison; listing-date filter + survivorship worst-case; disqualifying-flag decomposition.
  Anti-snooping enforced; no adoption; honest refutation allowed. Antigravity execution PENDING.
- 2026-08-29: PHASE 31-CANDIDATES-BENCHMARK COMPLETE — RESEARCH-DIRECTOR AUDIT: CLEAN & CORRECT.
  Verified artifacts directly (15:1x); BH applied across full m=24 matrix; Quallamaggie honestly
  NOT_IMPLEMENTED (no fabrication); RSI(14) vs RSI(25) both reported with winner-picking prohibited;
  Minervini honestly documented as partial (RS rating omitted). Headline verified: NO candidate beats
  C1 SOS after BH correction. Rankings: C1 SOS 8.35% (60D, #1) > C2b SOS+VCP 8.31% (#6) > C2a 8.02% (#9)
  > C3a Minervini 5.68% (#2) > C3b Minervini+SOS 5.51% (#7). Stacking VCP or Minervini on SOS does NOT
  add incremental alpha. RSI-25 (7.61%) vs RSI-14 (6.99%): parameter jitter, no winner. Survivorship:
  C1 survives -25% worst-case (+1.53%) but goes NEGATIVE (-1.54%) at -40% catastrophic. src/ clean,
  OOS firewall untouched, 204/204 tests. ANTIGRAVITY's PROGRESS entry this time ACCURATE.
  - KEY CONCLUSION: SOS remains the best validated signal. None of the new ideas (RSI-25, VCP filter,
    Minervini, Quallamaggie) beat it. RSI-25/variants = natural jitter. No strategy change.
- 2026-08-29: PHASE 31-CANDIDATES-BENCHMARK DESIGNED + PROMPTED. Operator asked to benchmark
  RSI(25) vs RSI(14), VCP, Minervini Trend Template, and "quallamaggie" vs what we've studied.
  Research-director: flagged as parameter-hunting risk; designed as ONE pre-registered BH-corrected
  benchmark vs the validated SOS baseline (C1). Anti-cherry-picking enforced; NO adoption.
  - C0 Frozen (Spring+SC), C1 SOS+Bullish (validated ref), C2 SOS+VCP (a=signal-cols, b=price-based),
    C3 Minervini (faithful, document omissions), C4 Quallamaggie (NOT_IMPLEMENTED allowed, no invention),
    C5 RSI(14) vs RSI(25) (both reported, no winner).
  - Two data paths: PATH A signal-CSV for event candidates; PATH B raw-cache point-in-time for new.
  - Guards: full-matrix BH; survivorship worst-case only for the BH-survivor; listing-date filter.
  - Antigravity execution PENDING. No production/OOS touch.
- 2026-08-29: PHASE 30-SURVIVOR-FREE COMPLETE. ANTIGRAVITY executed the best-effort survivorship
  reconstruction. Verified artifacts at data\validation_results\phase30_survivor_free\.
  - Listing-date filter: dropped 722 post-checkpoint IPO signals (0.84%); 0 symbols not in current
    universe (expected — universe was built from current-listed names; delisted stocks never in data).
  - SOS vs Random (filtered): p=0.002, +0.83% → survives. SOS vs Frozen paired (filtered): +1.98%,
    CI [0.33,3.51] → survives. Both consistent with Phase 29 un-filtered.
  - Worst-case bound: at -40% lost-stock collapse, absolute returns NEGATIVE (SOS -1.54%, frozen -2.37%,
    random -2.10%) — but relative order preserved (SOS still best). Edge is REAL but SMALL.
  - RESEARCH-DIRECTOR OVERRIDE/CLARIFICATION: The relative SOS edge survives even a blanket lost-stock
    penalty, confirming SOS > frozen and SOS > random. BUT absolute profitability under catastrophic
    survivorship (missing dead stocks collapse 40%) would have been NEGATIVE for the WHOLE approach.
    So: SOS = better-than-random and better-than-frozen, but NOT proven reliably profitable.
  - Production src/ untouched (git verified). OOS firewall untouched. 204/204 tests.
- 2026-08-29: PHASE 33-SOS-HIGHLIGHT-VIEW COMPLETE. ANTIGRAVITY implemented display-only SOS highlight view;
  added dashboard/sos_view.py, updated dashboard/app.py, added tests/dashboard/test_sos_highlight_view.py.
  - Pure helper: classify_sos_status, add_sos_status_column, prepare_sos_display_df.
  - Dashboard: "🚀 SOS Only" toggle, research banner, vsa_volume_ratio sorting when active, sos_status column in table.
  - 100% backward compatible. src/ untouched, strategy/scoring frozen, 212/212 tests pass.
- 2026-08-29: PHASE 32-DISQUALIFICATION-VALIDATION COMPLETE. ANTIGRAVITY executed full-universe validation (86,234 signals across 1,971 stocks);
  outputs at data\validation_results\phase32_disqualification_validation\, report at docs\PHASE_32_DISQUALIFICATION_VALIDATION_REPORT.md.
  - Phase 7 Separation Refuted at Scale: 60D Net separation delta = -0.31% (Qualified 4.62% vs Disqualified 4.93%, CI [-1.97%, +1.15%], NOT_SIGNIFICANT).
  - All hypotheses across 10D, 20D, 60D are NOT_SIGNIFICANT after full-matrix BH correction.
  - Comparison vs SOS: SOS excess edge (+0.89%, p=0.0000) is statistically established; unconditioned blanket disqualification is noise across all stocks.
  - Flag Decomposition: UTAD Distribution Warning (N=16,129, mean net +4.31%, drag -0.31%) provides genuine defensive filter drag.
  - Zero strategy change, zero production code modified under src/, 204/204 tests pass.
- 2026-08-29: PHASE 31-CANDIDATES-BENCHMARK COMPLETE. ANTIGRAVITY executed full benchmark across 8 candidates x 3 horizons (m=24 hypotheses);
  outputs at data\validation_results\phase31_candidates_benchmark\, report at docs\PHASE_31_CANDIDATES_BENCHMARK_REPORT.md.
  - Full-Matrix BH Correction (m=24, alpha=0.05): C1 SOS-Only (60D) remains the TOP setup (mean +8.35%, p=0.0000, SIGNIFICANT_POSITIVE).
  - Does ANY candidate beat SOS after BH? NO.
  - C2 SOS + VCP: +8.02% (CSV) / +8.31% (PIT price) vs +8.35% for pure SOS (no incremental edge).
  - C3 Minervini Trend Template: +5.68% (60D) alone, +5.51% stacked with SOS (degrades sample size without lifting returns).
  - C4 Quallamaggie: NOT_IMPLEMENTED (unverifiable rule set).
  - C5 RSI-14 vs RSI-25: 6.99% vs 7.61% (parameter jitter; winner-picking prohibited).
  - Strategy remains FROZEN. Zero production code modified under src/, 204/204 tests pass.
- 2026-08-29: PHASE 30-SURVIVOR-FREE COMPLETE. ANTIGRAVITY executed all 5 experiments (A-E); outputs at
  data\validation_results\phase30_survivor_free\, report at docs\PHASE_30_SURVIVOR_FREE_REPORT.md.
  - Exp A: 722 post-checkpoint IPO signals dropped (0.84%). 0 missing/NA symbols from current NSE source.
  - Exp B: SOS vs random on filtered universe holds at 60D (mean diff +0.83%, p=0.0020, 99.9th pct).
  - Exp C: SOS vs frozen paired on filtered universe holds (+1.98%, 95% CI [0.33%, 3.51%], SIGNIFICANT_POSITIVE).
    Unpaired diff remains NOT_ESTABLISHED (+1.04%, CI [-1.14%, 3.03%]).
  - Exp D: Under catastrophic -40% lost-stock collapse, SOS absolute return is -1.54%, but relative edge
    remains positive (+0.84% over frozen, +0.56% over random).
  - Exp E: Residual bias audit documented. Limitation confirmed: free historical data cannot recover dead stocks;
    prospective live OOS remains the only true bias-free validator. Zero production code modified, 204/204 tests pass.
- 2026-08-29: PHASE 29-SOS-DIFF-TEST COMPLETE. ANTIGRAVITY executed difference-test; outputs at
  data\validation_results\phase29_sos_diff_test\, report at docs\PHASE_29_SOS_DIFF_TEST_REPORT.md.
  - Exp Q1: Unpaired difference CI [-0.99%, +3.07%] contains 0 -> NOT_ESTABLISHED. Paired CI [+0.44%, +3.54%] SIG.
  - Exp Q2: Sign flips across regimes (SOS +1.10% under canonical vs -2.12% under loose).
  - Exp Q3: Robustness tests all return NOT_ESTABLISHED on unpaired diff.
  - SOS(6,359)>>Frozen(1,916) and different fire-months. Research-director flags this for operator decision.
- 2026-08-29: PHASE 29-SOS-DIFF-TEST APPROVED & PROMPTED. Operator accepted research-director's
  correction (Phase 28 "SOS beats frozen" was overstated; CIs overlap; no difference-test was run)
  and approved Phase 29. Antigravity execution PENDING.
- 2026-08-29: PHASE 28-SOS-RESEARCH COMPLETE + RESEARCH-DIRECTOR OVERRIDE of ANTIGRAVITY's over-claim.
  ANTIGRAVITY wrote "SOS strictly beats / outperforms Spring+SC" — OVERSTATED; research-director corrected.
  Facts verified vs raw CSVs in data\validation_results\phase28_sos_research\:
  - Exp A: SOS vs Random reproduced Phase 27 exact (60D gross mean diff +0.89%, p=0.0000, 100th pct). SOLID.
  - Exp B: SOS point-estimate beat frozen (+1.09% mean, +0.25 PF), BUT bootstrap CIs OVERLAP
    (SOS [4.46,12.84] vs frozen [3.72,11.03]; gap < SE) — NO difference-test was run. NOT significant.
  - Exp C: REGIME-UNSTABLE — SOS LOST to frozen under LOOSE filter (7.52% vs 9.65%); only wins under
    canonical Bullish (8.54% vs 7.45%). ANTIGRAVITY's "confirmed across both regimes" is FALSE for SOS.
  - Exp D: CI excludes 0 (proves SOS>0, NOT SOS>frozen); survives 2.5%/yr haircut (8.54→7.95) GOOD;
    still tail-dependent (top-10% trim collapses to 2.33%).
  - Exp E: LPS removal lifts mean 8.02→8.29 (+0.27%) but LOWERS PF 2.72→2.67 (-0.05). NET-WASH, not slam dunk.
  - Zero strategy change, zero production src/ modified (git verified), OOS firewall untouched. 204/204 tests.
  - DECISION: strategy UNCHANGED. Recommend Phase 29 difference-test on (SOS minus frozen) + both-regime confirmation.
- 2026-08-29: PHASE 29-SOS-DIFF-TEST APPROVED & PROMPTED. Operator accepted research-director's
  correction (Phase 28 "SOS beats frozen" was overstated; CIs overlap; no difference-test was run)
  and approved Phase 29. Antigravity execution PENDING.
- 2026-08-29: PHASE 28-SOS-RESEARCH APPROVED & PROMPTED. Operator + collaborator agreed to pivot
  research to SOS, add LPS-removal as a separate documented decision, and proceed with a focused
  SOS test. Phase 28 master prompt written.
- 2026-08-29: PHASE 27-EVENT-AUDIT COMPLETE. ANTIGRAVITY executed all 6 experiments; outputs at
  data\validation_results\phase27_event_audit\, report at docs\PHASE_27_EVENT_AUDIT_REPORT.md.
  - Reproduction of Phase 23 EXACT: 0 duplicates, all p-values match (Spring-60D=0.878, SC-60D=0.680,
    SOS-60D=0.0, LPS-60D=0.0, UTAD-60D=0.504). replace=False for phase parity, gross==net confirmed.
  - Full-matrix BH correction (15 hypotheses) reclassified: only SOS-60D SIGNIFICANT_POSITIVE;
    Spring-60D & SC-60D NOT_SIGNIFICANT; LPS-60D SIGNIFICANT_NEGATIVE.
  - Regime (A) not-Sideways mean 9.65%/PF 3.15 vs (B) Bullish-only mean 7.45%/PF 2.48 — different universes; (B) is what's traded.
  - SOS-only (d) mean 8.54%/PF 2.73 > Spring+SC (c) 7.45%/PF 2.48.
  - Independence: all events have >=51 distinct months (SUFFICIENT); row-count inflation confirmed
    (LPS 36,982 rows but only 51 independent months).
  - LPS flagged SIGNIFICANT_NEGATIVE at 60D; screening it as a bullish candidate is contrary to data.
  - No production src/ modified (git status clean under src/). Verdict downgraded to C. UNRESOLVED.
- 2026-08-29: Created consolidated memory file (this file). 
  - Discovered Phase 23 permutation p-values contradict its own summary (Spring/SC non-sig at 60D).
  - Wrote PHASE 27-EVENT-AUDIT prompt (not yet executed). Downgraded overall verdict to B. PROMISING BUT UNRESOLVED.
- 2026-08-27: Phase 25/26 completed (CONDITIONAL GO; INSUFFICIENT SAMPLE). PROGRESS.md prior entries reflect this and remain preserved above.
