"""
Comprehensive Forensic Testing Suite for Strategy 44: Hypothesis H02
Implements:
  - Benjamini-Hochberg (FDR) & Holm-Bonferroni Multiple-Testing Corrections
  - H02-A: Generic CVD Unconditional Information (Rank IC, Quintiles, Monotonicity)
  - H02-B: Range-Conditioned CVD & Incremental Information (Model A vs. Model B: ΔIC)
  - H02-C: Price-Flow Divergence with 30s Event Cooldown & Incremental IC
  - H02-D: Passive Absorption Candidates (Trade-Only vs. L3 MBO Grounding)
  - Execution Feasibility Test (Mid-price vs. Net Taker Execution with Friction)
"""

import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

PROJECT_ROOT = Path(__file__).resolve().parents[3]
FEATURES_DIR = PROJECT_ROOT / "strategies" / "44_mbo_orderflow" / "results" / "engineered_features"
REPORTS_DIR = PROJECT_ROOT / "strategies" / "44_mbo_orderflow" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

IS_SESSIONS = [
    "2026-07-08", "2026-07-09", "2026-07-10", "2026-07-13", "2026-07-14", "2026-07-15",
    "2026-07-16", "2026-07-17", "2026-07-20", "2026-07-21", "2026-07-22", "2026-07-23",
    "2026-07-24", "2026-07-27", "2026-07-28", "2026-07-29", "2026-07-30", "2026-07-31",
    "2026-08-03", "2026-08-04", "2026-08-05", "2026-08-06", "2026-08-07", "2026-08-10",
    "2026-08-11", "2026-08-12"
]

HORIZONS = ["fwd_ret_1s", "fwd_ret_5s", "fwd_ret_15s", "fwd_ret_60s", "fwd_ret_300s"]


def benjamini_hochberg(p_values: list) -> list:
    """Adjusts p-values using the Benjamini-Hochberg FDR procedure."""
    p = np.array(p_values)
    n = len(p)
    if n == 0:
        return []
    sorted_order = np.argsort(p)
    sorted_p = p[sorted_order]
    adjusted = np.zeros(n)
    cum_min = 1.0
    for i in range(n - 1, -1, -1):
        rank = i + 1
        adj = (n / rank) * sorted_p[i]
        cum_min = min(cum_min, adj)
        adjusted[i] = min(cum_min, 1.0)
    rev_order = np.empty(n, dtype=int)
    rev_order[sorted_order] = np.arange(n)
    return adjusted[rev_order].tolist()


def holm_bonferroni(p_values: list) -> list:
    """Adjusts p-values using the Holm-Bonferroni step-down FWER procedure."""
    p = np.array(p_values)
    n = len(p)
    if n == 0:
        return []
    sorted_order = np.argsort(p)
    sorted_p = p[sorted_order]
    adjusted = np.zeros(n)
    cum_max = 0.0
    for i in range(n):
        rank = i + 1
        adj = (n - rank + 1) * sorted_p[i]
        cum_max = max(cum_max, adj)
        adjusted[i] = min(cum_max, 1.0)
    rev_order = np.empty(n, dtype=int)
    rev_order[sorted_order] = np.arange(n)
    return adjusted[rev_order].tolist()


def load_all_features() -> pd.DataFrame:
    dfs = []
    for d in IS_SESSIONS:
        f = FEATURES_DIR / f"h02_features_{d}.parquet"
        if f.exists():
            df = pd.read_parquet(f)
            df["date"] = d
            dfs.append(df)
    if not dfs:
        raise FileNotFoundError("No engineered feature files found.")
    return pd.concat(dfs, ignore_index=True)


# ==============================================================================
# 1. H02-A: GENERIC CVD UNCONDITIONAL TESTS
# ==============================================================================
def test_h02_a(pooled_df: pd.DataFrame) -> pd.DataFrame:
    features = [
        "cvd_1s", "cvd_5s", "cvd_15s", "cvd_60s",
        "nfr_1s", "nfr_5s", "nfr_15s", "nfr_60s",
        "tcd_1s", "tcd_5s", "tcd_15s", "tcd_60s"
    ]
    rows = []

    for feat in features:
        for h in HORIZONS:
            valid = pooled_df.dropna(subset=[feat, h, "date"])
            daily_ics = []
            for d, group in valid.groupby("date"):
                if len(group) > 50:
                    corr, _ = stats.spearmanr(group[feat], group[h])
                    if not np.isnan(corr):
                        daily_ics.append(corr)

            if len(daily_ics) < 5:
                continue

            mean_ic = float(np.mean(daily_ics))
            std_ic = float(np.std(daily_ics, ddof=1)) if len(daily_ics) > 1 else 1e-6
            t_stat = (mean_ic / (std_ic / np.sqrt(len(daily_ics)))) if std_ic > 0 else 0.0
            p_val = float(2 * (1 - stats.t.cdf(abs(t_stat), df=len(daily_ics) - 1)))

            # Quintile analysis
            ranks = valid[feat].rank(method="first")
            valid_q = pd.qcut(ranks, q=5, labels=["Q1", "Q2", "Q3", "Q4", "Q5"])
            q_means = valid.groupby(valid_q)[h].mean()
            is_monotonic = bool(q_means.is_monotonic_increasing or q_means.is_monotonic_decreasing)
            q1 = float(q_means.get("Q1", np.nan))
            q5 = float(q_means.get("Q5", np.nan))
            spread = q5 - q1

            rows.append({
                "sub_hypothesis": "H02-A",
                "feature": feat,
                "horizon": h.replace("fwd_ret_", ""),
                "mean_ic": round(mean_ic, 4),
                "std_ic": round(std_ic, 4),
                "t_stat": round(t_stat, 2),
                "p_raw": p_val,
                "monotonic": is_monotonic,
                "q1_pts": round(q1, 3),
                "q5_pts": round(q5, 3),
                "spread_q5_q1": round(spread, 3),
            })

    res_df = pd.DataFrame(rows)
    if not res_df.empty:
        res_df["p_bh_fdr"] = benjamini_hochberg(res_df["p_raw"].tolist())
        res_df["p_holm"] = holm_bonferroni(res_df["p_raw"].tolist())
        res_df["gate_pass"] = (
            (res_df["mean_ic"].abs() >= 0.02) &
            (res_df["p_bh_fdr"] < 0.01) &
            res_df["monotonic"]
        )
    return res_df


# ==============================================================================
# 2. H02-B: RANGE-CONDITIONED INCREMENTAL INFORMATION
# ==============================================================================
def test_h02_b(pooled_df: pd.DataFrame) -> pd.DataFrame:
    features = ["cvd_5s", "cvd_15s", "cvd_60s", "nfr_15s"]
    test_horizons = ["fwd_ret_5s", "fwd_ret_15s", "fwd_ret_60s"]
    rows = []

    for feat in features:
        for h in test_horizons:
            valid = pooled_df.dropna(subset=[feat, "range_loc_15m", h, "date"]).copy()
            if len(valid) < 1000:
                continue

            # State Baseline Model A: Ret ~ range_loc_15m
            slope_a, intercept_a, r_a, p_a, _ = stats.linregress(valid["range_loc_15m"], valid[h])
            pred_a = intercept_a + slope_a * valid["range_loc_15m"]
            res_a = valid[h] - pred_a
            ic_a, _ = stats.spearmanr(pred_a, valid[h])

            # Full Model B: Ret ~ range_loc_15m + Feature
            X = np.column_stack([np.ones(len(valid)), valid["range_loc_15m"].values, valid[feat].values])
            y = valid[h].values
            beta, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
            pred_b = X @ beta
            ic_b, _ = stats.spearmanr(pred_b, y)

            delta_ic = ic_b - ic_a

            # Daily delta IC series for statistical t-test
            daily_d_ics = []
            for d, group in valid.groupby("date"):
                if len(group) > 50:
                    ic_grp_a, _ = stats.spearmanr(group["range_loc_15m"], group[h])
                    X_g = np.column_stack([np.ones(len(group)), group["range_loc_15m"].values, group[feat].values])
                    beta_g, _, _, _ = np.linalg.lstsq(X_g, group[h].values, rcond=None)
                    pred_g = X_g @ beta_g
                    ic_grp_b, _ = stats.spearmanr(pred_g, group[h].values)
                    daily_d_ics.append(ic_grp_b - ic_grp_a)

            mean_d_ic = float(np.mean(daily_d_ics))
            std_d_ic = float(np.std(daily_d_ics, ddof=1)) if len(daily_d_ics) > 1 else 1e-6
            t_stat = (mean_d_ic / (std_d_ic / np.sqrt(len(daily_d_ics)))) if std_d_ic > 0 else 0.0
            p_val = float(2 * (1 - stats.t.cdf(abs(t_stat), df=len(daily_d_ics) - 1)))

            # Extreme range conditioned IC (Upper Extreme >= 0.90, Lower Extreme <= 0.10)
            upper = valid[valid["range_extreme_high"] == 1]
            lower = valid[valid["range_extreme_low"] == 1]
            ic_upper, _ = stats.spearmanr(upper[feat], upper[h]) if len(upper) > 50 else (np.nan, np.nan)
            ic_lower, _ = stats.spearmanr(lower[feat], lower[h]) if len(lower) > 50 else (np.nan, np.nan)

            rows.append({
                "sub_hypothesis": "H02-B",
                "feature": feat,
                "horizon": h.replace("fwd_ret_", ""),
                "ic_model_a": round(ic_a, 4),
                "ic_model_b": round(ic_b, 4),
                "delta_ic": round(mean_d_ic, 4),
                "t_stat": round(t_stat, 2),
                "p_raw": p_val,
                "ic_upper_extreme": round(ic_upper, 4),
                "ic_lower_extreme": round(ic_lower, 4),
            })

    res_df = pd.DataFrame(rows)
    if not res_df.empty:
        res_df["p_bh_fdr"] = benjamini_hochberg(res_df["p_raw"].tolist())
        res_df["gate_pass"] = (res_df["delta_ic"] >= 0.015) & (res_df["p_bh_fdr"] < 0.01)
    return res_df


# ==============================================================================
# 3. H02-C: PRICE-FLOW DIVERGENCE (DE-DUPLICATED EVENTS)
# ==============================================================================
def test_h02_c(pooled_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    test_horizons = ["fwd_ret_15s", "fwd_ret_60s", "fwd_ret_300s"]

    for win in ["15s", "60s"]:
        sig_col = f"div_sig_{win}"
        dedup_col = f"div_dedup_{win}"
        dp_col = f"dp_{win}"

        # De-duplicated event subset
        events = pooled_df[pooled_df[dedup_col] == True].copy()
        n_events = len(events)
        n_bull = (events[sig_col] == 1).sum()
        n_bear = (events[sig_col] == -1).sum()

        for h in test_horizons:
            valid = events.dropna(subset=[sig_col, h, dp_col]).copy()
            if len(valid) < 20:
                continue

            # Reversal return: directionally signed
            signed_ret = valid[sig_col] * valid[h]
            mean_ret = float(signed_ret.mean())
            std_ret = float(signed_ret.std(ddof=1))
            t_stat = (mean_ret / (std_ret / np.sqrt(len(valid)))) if std_ret > 0 else 0.0
            p_val = float(2 * (1 - stats.t.cdf(abs(t_stat), df=len(valid) - 1)))

            # Incremental test over price excursion dp alone:
            ic_dp, _ = stats.spearmanr(-valid[dp_col], valid[h])
            ic_full, _ = stats.spearmanr(valid[sig_col], valid[h])
            delta_ic = ic_full - ic_dp

            rows.append({
                "sub_hypothesis": "H02-C",
                "divergence_window": win,
                "horizon": h.replace("fwd_ret_", ""),
                "n_independent_events": n_events,
                "n_bullish": n_bull,
                "n_bearish": n_bear,
                "mean_reversal_pts": round(mean_ret, 3),
                "std_ret_pts": round(std_ret, 3),
                "t_stat": round(t_stat, 2),
                "p_raw": p_val,
                "ic_dp_alone": round(ic_dp, 4),
                "ic_divergence": round(ic_full, 4),
                "delta_ic": round(delta_ic, 4),
            })

    res_df = pd.DataFrame(rows)
    if not res_df.empty:
        res_df["p_bh_fdr"] = benjamini_hochberg(res_df["p_raw"].tolist())
        res_df["gate_pass"] = (
            (res_df["n_independent_events"] >= 50) &
            (res_df["mean_reversal_pts"] > 0.25) &
            (res_df["p_bh_fdr"] < 0.01) &
            (res_df["delta_ic"] >= 0.015)
        )
    return res_df


# ==============================================================================
# 4. H02-D: PASSIVE ABSORPTION (TRADE-ONLY VS L3 MBO GROUNDING)
# ==============================================================================
def test_h02_d(pooled_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    test_horizons = ["fwd_ret_5s", "fwd_ret_15s", "fwd_ret_60s", "fwd_ret_300s"]

    for win in ["5s", "15s"]:
        # 1. Trade-Only
        col_trade_sig = f"absorb_trade_sig_{win}"
        col_trade_dedup = f"absorb_trade_dedup_{win}"
        ev_trade = pooled_df[pooled_df[col_trade_dedup] == True].copy()

        # 2. L3 MBO-Confirmed
        col_l3_sig = f"absorb_l3_sig_{win}"
        col_l3_dedup = f"absorb_l3_dedup_{win}"
        ev_l3 = pooled_df[pooled_df[col_l3_dedup] == True].copy()

        for h in test_horizons:
            # Trade-only metrics
            v_trade = ev_trade.dropna(subset=[col_trade_sig, h])
            ret_trade = v_trade[col_trade_sig] * v_trade[h]
            m_trade = float(ret_trade.mean()) if len(ret_trade) > 0 else np.nan
            t_trade = float(stats.ttest_1samp(ret_trade, 0).statistic) if len(ret_trade) > 10 else 0.0
            p_trade = float(stats.ttest_1samp(ret_trade, 0).pvalue) if len(ret_trade) > 10 else 1.0

            # L3 MBO metrics
            v_l3 = ev_l3.dropna(subset=[col_l3_sig, h])
            ret_l3 = v_l3[col_l3_sig] * v_l3[h]
            m_l3 = float(ret_l3.mean()) if len(ret_l3) > 0 else np.nan
            t_l3 = float(stats.ttest_1samp(ret_l3, 0).statistic) if len(ret_l3) > 10 else 0.0
            p_l3 = float(stats.ttest_1samp(ret_l3, 0).pvalue) if len(ret_l3) > 10 else 1.0

            # Direct comparison: does L3 add statistically significant return over trade-only?
            delta_ret = m_l3 - m_trade if not np.isnan(m_l3) and not np.isnan(m_trade) else np.nan
            diff_p = stats.ttest_ind(ret_l3, ret_trade, equal_var=False).pvalue if len(ret_l3) > 10 and len(ret_trade) > 10 else 1.0

            rows.append({
                "sub_hypothesis": "H02-D",
                "window": win,
                "horizon": h.replace("fwd_ret_", ""),
                "n_trade_events": len(ev_trade),
                "trade_mean_ret": round(m_trade, 3),
                "trade_t_stat": round(t_trade, 2),
                "trade_p_val": p_trade,
                "n_l3_events": len(ev_l3),
                "l3_mean_ret": round(m_l3, 3),
                "l3_t_stat": round(t_l3, 2),
                "l3_p_val": p_l3,
                "l3_minus_trade_pts": round(delta_ret, 3),
                "p_l3_vs_trade": diff_p,
            })

    res_df = pd.DataFrame(rows)
    if not res_df.empty:
        res_df["trade_p_bh"] = benjamini_hochberg(res_df["trade_p_val"].tolist())
        res_df["l3_p_bh"] = benjamini_hochberg(res_df["l3_p_val"].tolist())
        res_df["gate_pass"] = (
            (res_df["n_l3_events"] >= 100) &
            (res_df["l3_mean_ret"] > 0.50) &
            (res_df["l3_p_bh"] < 0.01) &
            (res_df["l3_minus_trade_pts"] > 0) &
            (res_df["p_l3_vs_trade"] < 0.05)
        )
    return res_df


# ==============================================================================
# 5. EXECUTION FEASIBILITY TEST
# ==============================================================================
def test_execution_feasibility(pooled_df: pd.DataFrame) -> pd.DataFrame:
    """
    Tests whether theoretical mid-price returns survive aggressive taker friction:
    Crossing the spread (paying half-spread on entry and exit) + 1.0 tick fee/slippage.
    """
    test_signals = ["cvd_5s", "div_sig_15s", "absorb_l3_sig_5s"]
    rows = []

    for sig in test_signals:
        for tau, h in [("5s", "fwd_ret_5s"), ("15s", "fwd_ret_15s"), ("60s", "fwd_ret_60s")]:
            bid_col = f"fwd_bid_{tau}"
            ask_col = f"fwd_ask_{tau}"
            valid = pooled_df.dropna(subset=[sig, h, "bid_px", "ask_px", bid_col, ask_col]).copy()
            if len(valid) < 100:
                continue

            # Define Long condition and Short condition
            if "cvd" in sig:
                p90 = valid[sig].quantile(0.90)
                p10 = valid[sig].quantile(0.10)
                long_mask = valid[sig] >= p90
                short_mask = valid[sig] <= p10
            else:
                long_mask = valid[sig] == 1
                short_mask = valid[sig] == -1

            # Long taker execution: Buy at Ask(t), Sell at Bid(t + tau) - 0.25 friction
            long_gross = valid.loc[long_mask, h]
            long_net = valid.loc[long_mask, bid_col] - valid.loc[long_mask, "ask_px"] - 0.25

            # Short taker execution: Sell at Bid(t), Buy at Ask(t + tau) - 0.25 friction
            short_gross = -valid.loc[short_mask, h]
            short_net = valid.loc[short_mask, "bid_px"] - valid.loc[short_mask, ask_col] - 0.25

            combined_gross = pd.concat([long_gross, short_gross])
            combined_net = pd.concat([long_net, short_net])

            if len(combined_gross) == 0:
                continue

            m_gross = float(combined_gross.mean())
            m_net = float(combined_net.mean())
            spread_cost = float((valid["spread"]).mean())

            rows.append({
                "signal": sig,
                "horizon": tau,
                "n_trades": len(combined_gross),
                "mean_spread_pts": round(spread_cost, 3),
                "gross_mid_pts": round(m_gross, 3),
                "net_taker_pts": round(m_net, 3),
                "profitable_after_friction": m_net > 0,
            })

    return pd.DataFrame(rows)


def run_all_information_tests():
    print("==========================================================")
    print("   H02 COMPREHENSIVE FORENSIC INFORMATION TESTING SUITE   ")
    print("==========================================================")
    t0 = time.time()
    pooled_df = load_all_features()
    print(f"Loaded {len(pooled_df):,} total feature rows across 26 In-Sample sessions in {time.time()-t0:.1f}s.\n")

    print("--> 1. Running H02-A: Generic CVD Unconditional Tests...")
    df_a = test_h02_a(pooled_df)
    print(df_a.head(10).to_string())

    print("\n--> 2. Running H02-B: Range-Conditioned Incremental Tests...")
    df_b = test_h02_b(pooled_df)
    print(df_b.to_string())

    print("\n--> 3. Running H02-C: Price-Flow Divergence Tests...")
    df_c = test_h02_c(pooled_df)
    print(df_c.to_string())

    print("\n--> 4. Running H02-D: Passive Absorption (Trade-Only vs. L3 MBO)...")
    df_d = test_h02_d(pooled_df)
    print(df_d.to_string())

    print("\n--> 5. Running Execution Feasibility Tests...")
    df_exec = test_execution_feasibility(pooled_df)
    print(df_exec.to_string())

    # Save outputs to CSV / Parquet
    df_a.to_csv(REPORTS_DIR / "h02_a_results.csv", index=False)
    df_b.to_csv(REPORTS_DIR / "h02_b_results.csv", index=False)
    df_c.to_csv(REPORTS_DIR / "h02_c_results.csv", index=False)
    df_d.to_csv(REPORTS_DIR / "h02_d_results.csv", index=False)
    df_exec.to_csv(REPORTS_DIR / "h02_execution_results.csv", index=False)
    print(f"\nAll reports generated in {REPORTS_DIR} successfully!")


if __name__ == "__main__":
    run_all_information_tests()
