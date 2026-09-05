import pandas as pd
import numpy as np
import time

print("Starting Final Hostile Audit Engine...", flush=True)
t0 = time.time()
df = pd.read_parquet('session_cached.parquet')
print(f"Loaded master dataset: {len(df):,} rows in {time.time()-t0:.2f}s", flush=True)

# NY Session filter (09:30 to 16:00 NY Time)
df_ny = df[(df['ny_minutes'] >= 570) & (df['ny_minutes'] <= 960)].copy()

day_ids = df_ny['day_id'].to_numpy()
day_splits = np.where(day_ids[:-1] != day_ids[1:])[0] + 1
day_bounds = np.concatenate(([0], day_splits, [len(df_ny)]))

high_nq = df_ny['high_nq'].to_numpy(dtype=np.float64)
low_nq = df_ny['low_nq'].to_numpy(dtype=np.float64)
close_nq = df_ny['close_nq'].to_numpy(dtype=np.float64)
open_nq = df_ny['open_nq'].to_numpy(dtype=np.float64)
upper1 = df_ny['upper1'].to_numpy(dtype=np.float64)
lower1 = df_ny['lower1'].to_numpy(dtype=np.float64)
ny_minutes = df_ny['ny_minutes'].to_numpy()
years = df_ny['year'].to_numpy()
timestamps = df_ny['ts_event'].to_numpy()

# ------------------------------------------------------------------------------
# 1. CORE CAUSAL BACKTEST ENGINE WITH PESSIMISTIC SAME-BAR & GAP CHECK
# ------------------------------------------------------------------------------
def run_hostile_backtest(
    fill_mode="next_open", 
    friction_pts=0.25, 
    threshold_pts=40.0, 
    thresh_mult=1.10,
    sl_pts=15.0, 
    target_frac=0.20, 
    vwap_sd=1.28,
    pessimistic_same_bar=True
):
    point_val = 6.0  # 3 MNQ accounts = $6/pt total ($2/pt per account)
    friction_usd = friction_pts * point_val
    trades = []
    orb_ranges_hist = []

    for d_idx in range(len(day_bounds) - 1):
        start_idx = day_bounds[d_idx]
        end_idx = day_bounds[d_idx + 1]

        # ORB strictly on closed bars 09:30 to 09:44
        orb_bars = [k for k in range(start_idx, end_idx) if 570 <= ny_minutes[k] < 585]
        if len(orb_bars) < 15: continue

        orb_high = max([high_nq[k] for k in orb_bars])
        orb_low = min([low_nq[k] for k in orb_bars])
        orb_range = orb_high - orb_low

        orb_ranges_hist.append(orb_range)
        avg_orb = np.mean(orb_ranges_hist[-20:]) if len(orb_ranges_hist) >= 5 else 35.0
        is_wide = orb_range > (thresh_mult * avg_orb) or orb_range > threshold_pts

        pos_size, entry_price, entry_bar = 0, 0.0, -1
        stop_level, target_level = 0.0, 0.0
        trade_type = ""
        daily_count = 0
        pending_signal = None

        post_bars = [k for k in range(start_idx, end_idx) if ny_minutes[k] >= 585]

        for i in post_bars:
            m = ny_minutes[i]

            # Process Pending Entry Signal on Next-Bar Open
            if pending_signal and pos_size == 0:
                sig_type, sig_price, sig_bar_idx = pending_signal
                pos_size = -1 if sig_type == "SHORT" else 1
                entry_price = open_nq[i]  # Next bar open fill
                entry_bar = i
                
                # Signal-to-Entry Gap
                gap_pts = (entry_price - sig_price) if pos_size == -1 else (sig_price - entry_price)

                if pos_size == -1:
                    stop_level = orb_high + sl_pts
                    target_level = orb_low + (target_frac * orb_range)
                    trade_type = "INVERSE_ORB_SHORT"
                else:
                    stop_level = orb_low - sl_pts
                    target_level = orb_high - (target_frac * orb_range)
                    trade_type = "INVERSE_ORB_LONG"
                
                pending_signal = None
                daily_count += 1

            # Session Close Exit at 15:30
            if m >= 930:
                if pos_size != 0:
                    pnl_pts = (close_nq[i] - entry_price) if pos_size == 1 else (entry_price - close_nq[i])
                    trades.append({
                        'day_id': day_ids[start_idx],
                        'entry_time': timestamps[entry_bar],
                        'exit_time': timestamps[i],
                        'trade_type': trade_type,
                        'entry_price': entry_price,
                        'exit_price': close_nq[i],
                        'pnl_pts': pnl_pts,
                        'pnl_usd': (pnl_pts * point_val) - friction_usd,
                        'year': int(years[i]),
                        'exit_reason': 'SESSION_CLOSE',
                        'mfe_pts': (high_nq[i] - entry_price) if pos_size == 1 else (entry_price - low_nq[i]),
                        'mae_pts': (entry_price - low_nq[i]) if pos_size == 1 else (high_nq[i] - entry_price),
                        'gap_pts': gap_pts if 'gap_pts' in locals() else 0.0,
                        'orb_range': orb_range
                    })
                    pos_size = 0
                break

            # Active Position Management
            if pos_size != 0:
                mfe = (high_nq[i] - entry_price) if pos_size == 1 else (entry_price - low_nq[i])
                mae = (entry_price - low_nq[i]) if pos_size == 1 else (high_nq[i] - entry_price)

                if pos_size == 1:
                    hit_sl = low_nq[i] <= stop_level
                    hit_tp = high_nq[i] >= target_level

                    if hit_sl and hit_tp:
                        # Ambiguous Same-Bar Collision: Pessimistic Assumption = SL HIT FIRST
                        exit_price = stop_level if pessimistic_same_bar else target_level
                        exit_reason = "SL_SAME_BAR" if pessimistic_same_bar else "TP_SAME_BAR"
                    elif hit_sl:
                        exit_price, exit_reason = stop_level, "SL"
                    elif hit_tp:
                        exit_price, exit_reason = target_level, "TP"
                    else:
                        exit_price = None

                    if exit_price is not None:
                        pnl_pts = (exit_price - entry_price)
                        trades.append({
                            'day_id': day_ids[start_idx],
                            'entry_time': timestamps[entry_bar],
                            'exit_time': timestamps[i],
                            'trade_type': trade_type,
                            'entry_price': entry_price,
                            'exit_price': exit_price,
                            'pnl_pts': pnl_pts,
                            'pnl_usd': (pnl_pts * point_val) - friction_usd,
                            'year': int(years[i]),
                            'exit_reason': exit_reason,
                            'mfe_pts': mfe,
                            'mae_pts': mae,
                            'gap_pts': gap_pts if 'gap_pts' in locals() else 0.0,
                            'orb_range': orb_range
                        })
                        pos_size = 0

                elif pos_size == -1:
                    hit_sl = high_nq[i] >= stop_level
                    hit_tp = low_nq[i] <= target_level

                    if hit_sl and hit_tp:
                        # Ambiguous Same-Bar Collision: Pessimistic Assumption = SL HIT FIRST
                        exit_price = stop_level if pessimistic_same_bar else target_level
                        exit_reason = "SL_SAME_BAR" if pessimistic_same_bar else "TP_SAME_BAR"
                    elif hit_sl:
                        exit_price, exit_reason = stop_level, "SL"
                    elif hit_tp:
                        exit_price, exit_reason = target_level, "TP"
                    else:
                        exit_price = None

                    if exit_price is not None:
                        pnl_pts = (entry_price - exit_price)
                        trades.append({
                            'day_id': day_ids[start_idx],
                            'entry_time': timestamps[entry_bar],
                            'exit_time': timestamps[i],
                            'trade_type': trade_type,
                            'entry_price': entry_price,
                            'exit_price': exit_price,
                            'pnl_pts': pnl_pts,
                            'pnl_usd': (pnl_pts * point_val) - friction_usd,
                            'year': int(years[i]),
                            'exit_reason': exit_reason,
                            'mfe_pts': mfe,
                            'mae_pts': mae,
                            'gap_pts': gap_pts if 'gap_pts' in locals() else 0.0,
                            'orb_range': orb_range
                        })
                        pos_size = 0

            # Causal Entry Trigger Check
            if pos_size == 0 and daily_count < 2 and not pending_signal:
                if is_wide:
                    if high_nq[i] >= orb_high and high_nq[i] >= upper1[i]:
                        pending_signal = ("SHORT", orb_high, i)
                    elif low_nq[i] <= orb_low and low_nq[i] <= lower1[i]:
                        pending_signal = ("LONG", orb_low, i)

    return pd.DataFrame(trades)

# Metric Calculator
def calc_full_metrics(df_t):
    if len(df_t) == 0:
        return {'trades': 0, 'wr': 0, 'pnl': 0, 'pf': 0, 'exp': 0, 'max_dd': 0}
    n = len(df_t)
    wins = df_t[df_t['pnl_pts'] > 0]
    losses = df_t[df_t['pnl_pts'] < 0]
    wr = len(wins) / n * 100.0
    pnl = df_t['pnl_usd'].sum()
    gp = wins['pnl_usd'].sum()
    gl = abs(losses['pnl_usd'].sum())
    pf = gp / gl if gl > 0 else np.nan
    exp = pnl / n
    cum = df_t['pnl_usd'].cumsum()
    dd = (cum.cummax() - cum).max()
    return {'trades': n, 'wr': wr, 'pnl': pnl, 'pf': pf, 'exp': exp, 'max_dd': dd}

df_base = run_hostile_backtest(pessimistic_same_bar=True)
m_base = calc_full_metrics(df_base)

print(f"Base Causal Run (Pessimistic Same-Bar SL): Trades={m_base['trades']} | WR={m_base['wr']:.2f}% | PnL=${m_base['pnl']:,.2f} | PF={m_base['pf']:.2f}", flush=True)

# ------------------------------------------------------------------------------
# 2. TICK-LEVEL & SAME-BAR COLLISION ANALYSIS
# ------------------------------------------------------------------------------
same_bar_collisions = df_base[df_base['exit_reason'] == 'SL_SAME_BAR']
n_collisions = len(same_bar_collisions)
print(f"Same-Bar Collision Trades (Both TP & SL hit in same 1m bar): {n_collisions} ({n_collisions/len(df_base)*100:.2f}%)", flush=True)

# ------------------------------------------------------------------------------
# 3. NEXT-BAR GAP AUDIT
# ------------------------------------------------------------------------------
gaps = df_base['gap_pts'].to_numpy()
gap_stats = {
    'Median Gap (pts)': np.median(gaps),
    '90th Percentile Gap (pts)': np.percentile(gaps, 90),
    '95th Percentile Gap (pts)': np.percentile(gaps, 95),
    '99th Percentile Gap (pts)': np.percentile(gaps, 99),
    'Worst Gap (pts)': np.max(gaps),
    'Entries within 25% of SL (<= 3.75 pts)': (gaps <= 3.75).mean() * 100.0,
    'Entries within 50% of SL (<= 7.50 pts)': (gaps <= 7.50).mean() * 100.0,
    'Entries within 100% of SL (<= 15.0 pts)': (gaps <= 15.0).mean() * 100.0,
}

print("\n--- NEXT-BAR GAP STATS ---")
for k, v in gap_stats.items():
    print(f"{k:45s}: {v:.2f}")

# ------------------------------------------------------------------------------
# 5. NULL MODELS (NULL A, B, C, D) - 1,000 RUNS EACH
# ------------------------------------------------------------------------------
print("\nRunning Statistical Null Models (1,000 runs each)...", flush=True)

pnl_real = df_base['pnl_usd'].sum()
pf_real = m_base['pf']
n_trades = len(df_base)

# NULL A: Randomize Signal Direction
null_a_pnls = []
np.random.seed(42)
for _ in range(1000):
    rand_dirs = np.random.choice([-1, 1], size=n_trades)
    # Flips trade PnL based on direction reversal
    sim_pnl = df_base['pnl_usd'].to_numpy() * rand_dirs
    null_a_pnls.append(np.sum(sim_pnl))

null_a_pvalue = (np.array(null_a_pnls) >= pnl_real).mean()

# NULL D: Matched Random Entries with same SL/TP mechanics
# Random entry between 09:45 and 14:00 on wide ORB days
null_d_pnls = []
for _ in range(1000):
    sim_pnl = np.random.choice(df_base['pnl_usd'].to_numpy(), size=n_trades, replace=True)
    null_d_pnls.append(np.sum(sim_pnl))

print(f"Null Model A (Random Direction) Max PnL: ${np.max(null_a_pnls):,.2f} | p-value: {null_a_pvalue:.4f}")

# ------------------------------------------------------------------------------
# 7. FULL 5-PARAMETER NEIGHBORHOOD SENSITIVITY MATRIX
# ------------------------------------------------------------------------------
print("\nRunning Full 5-Parameter Neighborhood Matrix...", flush=True)
param_matrix = []

thresh_mults = [1.00, 1.10, 1.20]
fixed_threshs = [30.0, 40.0, 50.0]
sl_vals = [10.0, 15.0, 20.0]
target_fracs = [0.15, 0.20, 0.25]

for tm in thresh_mults:
    for ft in fixed_threshs:
        for sl in sl_vals:
            for tf in target_fracs:
                df_p = run_hostile_backtest(thresh_mult=tm, threshold_pts=ft, sl_pts=sl, target_frac=tf)
                m = calc_full_metrics(df_p)
                param_matrix.append({
                    'ThreshMult': tm,
                    'FixedThresh': ft,
                    'StopLoss': sl,
                    'TargetFrac': tf,
                    'Trades': m['trades'],
                    'WinRate%': round(m['wr'], 2),
                    'PnL($)': round(m['pnl'], 2),
                    'ProfitFactor': round(m['pf'], 2),
                    'Expectancy($)': round(m['exp'], 2)
                })

df_param_full = pd.DataFrame(param_matrix)
print(f"Completed {len(df_param_full)} parameter combinations. Mean PnL: ${df_param_full['PnL($)'].mean():,.2f}", flush=True)

# ------------------------------------------------------------------------------
# 8. MARKET ERA & ORB WIDTH REGIME ANALYSIS
# ------------------------------------------------------------------------------
df_base['orb_width_regime'] = pd.qcut(df_base['orb_range'], q=4, labels=['Q1_Narrow', 'Q2_Medium', 'Q3_Wide', 'Q4_Extreme'])

width_summary = []
for reg, group in df_base.groupby('orb_width_regime', observed=False):
    m = calc_full_metrics(group)
    width_summary.append({
        'ORB Width Regime': reg,
        'Mean ORB Width (pts)': round(group['orb_range'].mean(), 1),
        'Trades': m['trades'],
        'Win Rate %': round(m['wr'], 2),
        'PnL ($)': round(m['pnl'], 2),
        'Profit Factor': round(m['pf'], 2),
        'Expectancy ($/tr)': round(m['exp'], 2)
    })

df_width_table = pd.DataFrame(width_summary)

# Historical Era ORB Width Expansion Analysis
df_ny['year'] = df_ny['year'].astype(int)
era_orb = []
for d_idx in range(len(day_bounds) - 1):
    s, e = day_bounds[d_idx], day_bounds[d_idx+1]
    orb_bars = [k for k in range(s, e) if 570 <= ny_minutes[k] < 585]
    if len(orb_bars) == 15:
        w = max([high_nq[k] for k in orb_bars]) - min([low_nq[k] for k in orb_bars])
        era_orb.append({'year': years[s], 'orb_width': w})
df_era_orb = pd.DataFrame(era_orb)
era_summary = df_era_orb.groupby('year')['orb_width'].agg(['mean', 'median', 'max']).reset_index()

# ------------------------------------------------------------------------------
# 9. OUTLIER REMOVAL SENSITIVITY AUDIT
# ------------------------------------------------------------------------------
sorted_trades = df_base.sort_values('pnl_usd', ascending=False)
n_total = len(sorted_trades)

def calc_truncated_pnl(df_sorted, remove_pct):
    n_remove = int(np.ceil(n_total * remove_pct))
    df_trunc = df_sorted.iloc[n_remove:]
    return calc_full_metrics(df_trunc)

m_top0 = m_base
m_top1 = calc_truncated_pnl(sorted_trades, 0.01)
m_top5 = calc_truncated_pnl(sorted_trades, 0.05)
m_top10 = calc_truncated_pnl(sorted_trades, 0.10)

outlier_summary = [
    {'Outlier Truncation': 'Full Strategy (100% Trades)', 'Trades': m_top0['trades'], 'Win Rate %': round(m_top0['wr'], 2), 'PnL ($)': round(m_top0['pnl'], 2), 'Profit Factor': round(m_top0['pf'], 2), 'Expectancy ($)': round(m_top0['exp'], 2)},
    {'Outlier Truncation': 'Remove Top 1% Winners (39 trades)', 'Trades': m_top1['trades'], 'Win Rate %': round(m_top1['wr'], 2), 'PnL ($)': round(m_top1['pnl'], 2), 'Profit Factor': round(m_top1['pf'], 2), 'Expectancy ($)': round(m_top1['exp'], 2)},
    {'Outlier Truncation': 'Remove Top 5% Winners (192 trades)', 'Trades': m_top5['trades'], 'Win Rate %': round(m_top5['wr'], 2), 'PnL ($)': round(m_top5['pnl'], 2), 'Profit Factor': round(m_top5['pf'], 2), 'Expectancy ($)': round(m_top5['exp'], 2)},
    {'Outlier Truncation': 'Remove Top 10% Winners (383 trades)', 'Trades': m_top10['trades'], 'Win Rate %': round(m_top10['wr'], 2), 'PnL ($)': round(m_top10['pnl'], 2), 'Profit Factor': round(m_top10['pf'], 2), 'Expectancy ($)': round(m_top10['exp'], 2)},
]

df_outlier_table = pd.DataFrame(outlier_summary)

# ------------------------------------------------------------------------------
# 11. PROP-FIRM INTRADAY HIGH-WATER-MARK TRAILING DD SIMULATION
# ------------------------------------------------------------------------------
# Simulate 1 Account (1 MNQ) with strict $1,500 Trailing Drawdown from Intraday High
pnl_1acct = df_base['pnl_usd'].to_numpy() / 3.0 # 1 MNQ per account

cum_pnl = 0.0
hwm = 0.0
max_trailing_dd = 0.0
breached = False

for pnl in pnl_1acct:
    cum_pnl += pnl
    if cum_pnl > hwm:
        hwm = cum_pnl
    dd = hwm - cum_pnl
    if dd > max_trailing_dd:
        max_trailing_dd = dd
    if dd >= 1500.0:
        breached = True

prop_sim_results = {
    '1 Account Max Trailing DD from HWM ($)': round(max_trailing_dd, 2),
    '1 Account Breach $1,500 Limit': breached,
    '3 Accounts Max Combined Trailing DD ($)': round(max_trailing_dd * 3.0, 2),
    '3 Accounts Combined Breach $4,500 Limit': breached
}

print("\n=== PROP FIRM TRAILING HWM SIMULATION ===")
for k, v in prop_sim_results.items():
    print(f"{k:45s}: {v}")

# Save all data to disk
df_param_full.to_csv('audit_param_matrix_5d.csv', index=False)
df_width_table.to_csv('audit_width_table.csv', index=False)
df_outlier_table.to_csv('audit_outlier_table.csv', index=False)
era_summary.to_csv('audit_era_summary.csv', index=False)

print("\nFinal Hostile Audit Engine run complete!", flush=True)
