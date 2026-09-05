import pandas as pd
import numpy as np
import time

print("Running Full Forensic Audit Suite...", flush=True)
t0 = time.time()
df = pd.read_parquet('session_cached.parquet')
print(f"Loaded master cache: {len(df):,} rows in {time.time()-t0:.2f}s", flush=True)

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
upper2 = df_ny['upper2'].to_numpy(dtype=np.float64) if 'upper2' in df_ny else upper1 * 1.05
lower2 = df_ny['lower2'].to_numpy(dtype=np.float64) if 'lower2' in df_ny else lower1 * 0.95
ny_minutes = df_ny['ny_minutes'].to_numpy()
years = df_ny['year'].to_numpy()
timestamps = df_ny['ts_event'].to_numpy()

# Core Simulation Engine for Audit
def run_audit_sim(fill_mode="next_open", friction_pts=0.25, threshold_pts=40.0, sl_pts=15.0, target_frac=0.20, vwap_sd_band="SD1"):
    point_val = 6.0 # 3 MNQ = $6/pt
    friction_usd = friction_pts * point_val
    trades = []
    orb_ranges_hist = []

    upper_band = upper1 if vwap_sd_band == "SD1" else upper2
    lower_band = lower1 if vwap_sd_band == "SD1" else lower2

    for d_idx in range(len(day_bounds) - 1):
        start_idx = day_bounds[d_idx]
        end_idx = day_bounds[d_idx + 1]

        orb_bars = [k for k in range(start_idx, end_idx) if 570 <= ny_minutes[k] < 585]
        if len(orb_bars) < 15: continue

        orb_high = max([high_nq[k] for k in orb_bars])
        orb_low = min([low_nq[k] for k in orb_bars])
        orb_range = orb_high - orb_low

        orb_ranges_hist.append(orb_range)
        avg_orb = np.mean(orb_ranges_hist[-20:]) if len(orb_ranges_hist) >= 5 else 35.0
        is_wide = orb_range > (1.10 * avg_orb) or orb_range > threshold_pts

        pos_size, entry_price, entry_bar = 0, 0.0, -1
        stop_level, target_level = 0.0, 0.0
        trade_type = ""
        daily_count = 0
        pending_signal = None

        post_bars = [k for k in range(start_idx, end_idx) if ny_minutes[k] >= 585]

        for i in post_bars:
            m = ny_minutes[i]

            # Pending signal fill (Causal next-bar open fill)
            if pending_signal and pos_size == 0:
                sig_type, sig_price = pending_signal
                pos_size = -1 if sig_type == "SHORT" else 1
                entry_price = open_nq[i] if fill_mode == "next_open" else sig_price
                entry_bar = i
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
                        'year': int(years[i])
                    })
                    pos_size = 0
                break

            if pos_size != 0:
                if pos_size == 1:
                    hit_sl = low_nq[i] <= stop_level
                    hit_tp = high_nq[i] >= target_level
                    exit_price = stop_level if hit_sl else (target_level if hit_tp else None)
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
                            'year': int(years[i])
                        })
                        pos_size = 0

                elif pos_size == -1:
                    hit_sl = high_nq[i] >= stop_level
                    hit_tp = low_nq[i] <= target_level
                    exit_price = stop_level if hit_sl else (target_level if hit_tp else None)
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
                            'year': int(years[i])
                        })
                        pos_size = 0

            if pos_size == 0 and daily_count < 2 and not pending_signal:
                if is_wide:
                    if high_nq[i] >= orb_high and high_nq[i] >= upper_band[i]:
                        if fill_mode == "limit_exact":
                            pos_size, entry_price, entry_bar = -1, orb_high, i
                            stop_level = orb_high + sl_pts
                            target_level = orb_low + (target_frac * orb_range)
                            trade_type = "INVERSE_ORB_SHORT"
                            daily_count += 1
                        elif fill_mode == "next_open":
                            pending_signal = ("SHORT", orb_high)
                        elif fill_mode == "close_orig":
                            pos_size, entry_price, entry_bar = -1, close_nq[i], i
                            stop_level = orb_high + sl_pts
                            target_level = orb_low + (target_frac * orb_range)
                            trade_type = "INVERSE_ORB_SHORT"
                            daily_count += 1

                    elif low_nq[i] <= orb_low and low_nq[i] <= lower_band[i]:
                        if fill_mode == "limit_exact":
                            pos_size, entry_price, entry_bar = 1, orb_low, i
                            stop_level = orb_low - sl_pts
                            target_level = orb_high - (target_frac * orb_range)
                            trade_type = "INVERSE_ORB_LONG"
                            daily_count += 1
                        elif fill_mode == "next_open":
                            pending_signal = ("LONG", orb_low)
                        elif fill_mode == "close_orig":
                            pos_size, entry_price, entry_bar = 1, close_nq[i], i
                            stop_level = orb_low - sl_pts
                            target_level = orb_high - (target_frac * orb_range)
                            trade_type = "INVERSE_ORB_LONG"
                            daily_count += 1

    return pd.DataFrame(trades)

# Metric Calculator
def calc_audit_metrics(df_t):
    if len(df_t) == 0:
        return {'trades': 0, 'wr': 0, 'pnl': 0, 'pf': 0, 'exp': 0, 'max_dd': 0, 'avg_win': 0, 'avg_loss': 0, 'exp_r': 0}
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
    avg_w = wins['pnl_usd'].mean() if len(wins) > 0 else 0
    avg_l = losses['pnl_usd'].mean() if len(losses) > 0 else 0
    exp_r = (wr/100.0 * (avg_w/abs(avg_l))) - ((1 - wr/100.0)) if abs(avg_l) > 0 else 0
    return {
        'trades': n, 'wr': wr, 'pnl': pnl, 'pf': pf, 'exp': exp,
        'max_dd': dd, 'avg_win': avg_w, 'avg_loss': avg_l, 'exp_r': exp_r
    }

# ==============================================================================
# SECTION 4: REALISTIC EXECUTION COST AUDIT
# ==============================================================================
cost_levels = [
    ("Baseline (1 Tick = $0.25/pt)", 0.25),
    ("+1 NQ Point ($1.00/pt)", 1.00),
    ("+2 NQ Points ($2.00/pt)", 2.00),
    ("+4 NQ Points ($4.00/pt)", 4.00),
    ("+8 NQ Points ($8.00/pt)", 8.00),
]

cost_results = []
for label, c_pts in cost_levels:
    df_c = run_audit_sim("next_open", friction_pts=c_pts)
    m = calc_audit_metrics(df_c)
    cost_results.append({
        'Execution Cost Scenario': label,
        'Trades': m['trades'],
        'Win Rate %': round(m['wr'], 2),
        'Total PnL ($)': round(m['pnl'], 2),
        'Profit Factor': round(m['pf'], 2),
        'Expectancy ($/tr)': round(m['exp'], 2),
        'Max Drawdown ($)': round(m['max_dd'], 2)
    })

df_cost_table = pd.DataFrame(cost_results)

# ==============================================================================
# SECTION 5: YEAR-BY-YEAR ROBUSTNESS TABLE
# ==============================================================================
df_base_open = run_audit_sim("next_open", friction_pts=0.25)
yearly_rows = []
for yr, group in df_base_open.groupby('year'):
    m = calc_audit_metrics(group)
    yearly_rows.append({
        'Year': int(yr),
        'Trades': m['trades'],
        'Win Rate %': round(m['wr'], 2),
        'Exp (R)': round(m['exp_r'], 2),
        'Profit Factor': round(m['pf'], 2),
        'PnL ($)': round(m['pnl'], 2),
        'Max DD ($)': round(m['max_dd'], 2),
        'Avg Trade ($)': round(m['exp'], 2),
        'Avg Winner ($)': round(m['avg_win'], 2),
        'Avg Loser ($)': round(m['avg_loss'], 2)
    })
df_yearly_table = pd.DataFrame(yearly_rows)

# ==============================================================================
# SECTION 6: WALK-FORWARD / OOS VALIDATION
# ==============================================================================
df_is = df_base_open[df_base_open['year'] <= 2018]
df_val = df_base_open[(df_base_open['year'] >= 2019) & (df_base_open['year'] <= 2022)]
df_oos = df_base_open[df_base_open['year'] >= 2023]

m_is = calc_audit_metrics(df_is)
m_val = calc_audit_metrics(df_val)
m_oos = calc_audit_metrics(df_oos)

oos_summary = [
    {'Partition': 'In-Sample Training (2010 - 2018)', 'Years': '9.0', 'Trades': m_is['trades'], 'Win Rate %': round(m_is['wr'], 2), 'Total PnL ($)': round(m_is['pnl'], 2), 'Profit Factor': round(m_is['pf'], 2), 'Expectancy ($/tr)': round(m_is['exp'], 2), 'Max DD ($)': round(m_is['max_dd'], 2)},
    {'Partition': 'Validation Period (2019 - 2022)', 'Years': '4.0', 'Trades': m_val['trades'], 'Win Rate %': round(m_val['wr'], 2), 'Total PnL ($)': round(m_val['pnl'], 2), 'Profit Factor': round(m_val['pf'], 2), 'Expectancy ($/tr)': round(m_val['exp'], 2), 'Max DD ($)': round(m_val['max_dd'], 2)},
    {'Partition': 'Untouched Out-Of-Sample (2023 - 2026)', 'Years': '3.6', 'Trades': m_oos['trades'], 'Win Rate %': round(m_oos['wr'], 2), 'Total PnL ($)': round(m_oos['pnl'], 2), 'Profit Factor': round(m_oos['pf'], 2), 'Expectancy ($/tr)': round(m_oos['exp'], 2), 'Max DD ($)': round(m_oos['max_dd'], 2)},
]
df_oos_table = pd.DataFrame(oos_summary)

# ==============================================================================
# SECTION 7: PARAMETER SENSITIVITY MATRIX
# ==============================================================================
param_rows = []
for thresh in [30.0, 35.0, 40.0, 45.0, 50.0]:
    for sl in [10.0, 15.0, 20.0]:
        for frac in [0.15, 0.20, 0.25]:
            df_p = run_audit_sim("next_open", friction_pts=0.25, threshold_pts=thresh, sl_pts=sl, target_frac=frac)
            m = calc_audit_metrics(df_p)
            param_rows.append({
                'ORB Threshold (pts)': thresh,
                'Stop Loss (pts)': sl,
                'Target Frac': frac,
                'Trades': m['trades'],
                'Win Rate %': round(m['wr'], 2),
                'Total PnL ($)': round(m['pnl'], 2),
                'Profit Factor': round(m['pf'], 2),
                'Expectancy ($)': round(m['exp'], 2)
            })

df_param_table = pd.DataFrame(param_rows)

# ==============================================================================
# SECTION 9: MONTE CARLO SIMULATION (10,000 RUNS)
# ==============================================================================
pnl_returns = df_base_open['pnl_usd'].to_numpy()
n_trades = len(pnl_returns)
n_sims = 10000

mc_max_dds = []
mc_final_pnls = []

np.random.seed(42)
for _ in range(n_sims):
    sim_pnl = np.random.choice(pnl_returns, size=n_trades, replace=True)
    cum = np.cumsum(sim_pnl)
    dd = np.max(np.maximum.accumulate(cum) - cum)
    mc_max_dds.append(dd)
    mc_final_pnls.append(cum[-1])

mc_dds = np.array(mc_max_dds)
mc_pnls = np.array(mc_final_pnls)

mc_results = {
    'Median Max DD ($)': np.percentile(mc_dds, 50),
    '95th Percentile Max DD ($)': np.percentile(mc_dds, 95),
    '99th Percentile Max DD ($)': np.percentile(mc_dds, 99),
    'Prob of Net Loss (%)': (mc_pnls <= 0).mean() * 100.0,
    'Statistical p-value': (mc_pnls <= 0).mean()
}

# ==============================================================================
# SECTION 10: PROP-FIRM SURVIVABILITY & CORRELATION
# ==============================================================================
single_acct_pnl = df_base_open['pnl_usd'] / 3.0  # 1 MNQ per account
single_cum = single_acct_pnl.cumsum()
single_dd = (single_cum.cummax() - single_cum).max()

# Daily loss limit check ($500 daily limit per account)
daily_single = df_base_open.groupby(df_base_open['entry_time'].dt.date)['pnl_usd'].sum() / 3.0
daily_breaches = (daily_single <= -500.0).sum()
total_days = len(daily_single)
daily_breach_pct = (daily_breaches / total_days) * 100.0 if total_days > 0 else 0

prop_summary = {
    'Single Account Max DD ($)': round(single_dd, 2),
    'Single Account Worst Day ($)': round(daily_single.min(), 2),
    'Single Account Best Day ($)': round(daily_single.max(), 2),
    'Daily Loss Limit Breaches (<-$500)': daily_breaches,
    'Daily Loss Limit Breach Rate (%)': round(daily_breach_pct, 2),
    'Prop Account Drawdown Violations ($1,500 Max DD Limit)': (single_dd > 1500.0)
}

# Print summaries
print("\n=== EXECUTION COST TABLE ===")
print(df_cost_table.to_string(index=False))

print("\n=== YEARLY ROBUSTNESS TABLE ===")
print(df_yearly_table.to_string(index=False))

print("\n=== WALK-FORWARD OOS TABLE ===")
print(df_oos_table.to_string(index=False))

print("\n=== MONTE CARLO SUMMARY ===")
for k, v in mc_results.items():
    print(f"{k:35s}: {v}")

print("\n=== PROP FIRM SURVIVABILITY ===")
for k, v in prop_summary.items():
    print(f"{k:35s}: {v}")

# Save full results to parquet/csv for report generation
df_yearly_table.to_csv('audit_yearly_table.csv', index=False)
df_cost_table.to_csv('audit_cost_table.csv', index=False)
df_oos_table.to_csv('audit_oos_table.csv', index=False)
df_param_table.to_csv('audit_param_table.csv', index=False)

print("\nAll forensic audit data successfully computed!", flush=True)
