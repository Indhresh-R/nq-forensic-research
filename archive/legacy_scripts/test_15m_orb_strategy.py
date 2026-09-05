import pandas as pd
import numpy as np
import time

print("Loading preprocessed session cache for 15-Min ORB simulation...", flush=True)
t0 = time.time()
df = pd.read_parquet('session_cached.parquet')
print(f"Loaded {len(df):,} rows in {time.time()-t0:.2f}s", flush=True)

# Filter for NY Session bars from 09:30 to 16:00 NY Time
df_ny = df[(df['ny_minutes'] >= 570) & (df['ny_minutes'] <= 960)].copy()

day_ids = df_ny['day_id'].to_numpy()
day_splits = np.where(day_ids[:-1] != day_ids[1:])[0] + 1
day_bounds = np.concatenate(([0], day_splits, [len(df_ny)]))

high_nq = df_ny['high_nq'].to_numpy(dtype=np.float64)
low_nq = df_ny['low_nq'].to_numpy(dtype=np.float64)
close_nq = df_ny['close_nq'].to_numpy(dtype=np.float64)
open_nq = df_ny['open_nq'].to_numpy(dtype=np.float64) if 'open_nq' in df_ny else close_nq
upper1 = df_ny['upper1'].to_numpy(dtype=np.float64)
lower1 = df_ny['lower1'].to_numpy(dtype=np.float64)
ny_minutes = df_ny['ny_minutes'].to_numpy()
years = df_ny['year'].to_numpy()
timestamps = df_ny['ts_event'].to_numpy()

def run_15m_orb_sim(mode="combined", num_accounts=3, contract_multiplier=2.0, max_trades_per_day=2):
    """
    15-Min NY Opening Range Breakout & Reversal Simulation Engine
    - 09:30 to 09:45 NY Time (ny_minutes 570 to 585): Build 15-min ORB High/Low
    - Max 1-2 trades per session limit enforced.
    """
    point_value = contract_multiplier * num_accounts  # e.g., 3 MNQ = $6/pt ($2/pt per MNQ x 3)
    friction_per_trade = 0.25 * point_value  # 1 tick friction total

    trades = []
    orb_ranges_hist = []

    for d_idx in range(len(day_bounds) - 1):
        start_idx = day_bounds[d_idx]
        end_idx = day_bounds[d_idx + 1]

        # 1. Establish 15-Min ORB (09:30 to 09:45 NY Time)
        orb_high = -1.0
        orb_low = 1e9
        orb_complete = False
        orb_end_bar = -1

        for i in range(start_idx, end_idx):
            m = ny_minutes[i]
            if 570 <= m < 585:
                if high_nq[i] > orb_high: orb_high = high_nq[i]
                if low_nq[i] < orb_low: orb_low = low_nq[i]
            elif m >= 585 and not orb_complete:
                orb_complete = True
                orb_end_bar = i
                break

        if not orb_complete or orb_high <= 0 or orb_low >= 1e8:
            continue

        orb_range = orb_high - orb_low
        orb_ranges_hist.append(orb_range)
        avg_orb_range = np.mean(orb_ranges_hist[-20:]) if len(orb_ranges_hist) >= 5 else 35.0

        # Classify ORB Regime: Wide ORB (Reversal) vs Normal ORB (Breakout)
        is_wide_orb = orb_range > (1.10 * avg_orb_range) or orb_range > 40.0

        pos_size, entry_price, entry_bar = 0, 0.0, -1
        stop_level, target_level = 0.0, 0.0
        trade_type = ""
        breakout_dir = 0
        retest_waiting = False
        daily_trades_count = 0

        for i in range(orb_end_bar, end_idx):
            m = ny_minutes[i]

            # Exit at 15:30 NY Time if open
            if m >= 930:
                if pos_size != 0:
                    pnl_pts = (close_nq[i] - entry_price) if pos_size == 1 else (entry_price - close_nq[i])
                    pnl_usd = (pnl_pts * point_value) - friction_per_trade
                    trades.append({
                        'entry_time': timestamps[entry_bar],
                        'exit_time': timestamps[i],
                        'trade_type': trade_type,
                        'pnl_pts': pnl_pts,
                        'pnl_usd': pnl_usd,
                        'year': int(years[i])
                    })
                    pos_size = 0
                break

            # 2. Position Management & Exit Check
            if pos_size != 0:
                if pos_size == 1:
                    hit_sl = low_nq[i] <= stop_level
                    hit_tp = high_nq[i] >= target_level
                    if hit_sl and hit_tp:
                        exit_price = stop_level
                    elif hit_sl:
                        exit_price = stop_level
                    elif hit_tp:
                        exit_price = target_level
                    else:
                        exit_price = None

                    if exit_price is not None:
                        pnl_pts = (exit_price - entry_price)
                        pnl_usd = (pnl_pts * point_value) - friction_per_trade
                        trades.append({
                            'entry_time': timestamps[entry_bar],
                            'exit_time': timestamps[i],
                            'trade_type': trade_type,
                            'pnl_pts': pnl_pts,
                            'pnl_usd': pnl_usd,
                            'year': int(years[i])
                        })
                        pos_size = 0

                elif pos_size == -1:
                    hit_sl = high_nq[i] >= stop_level
                    hit_tp = low_nq[i] <= target_level
                    if hit_sl and hit_tp:
                        exit_price = stop_level
                    elif hit_sl:
                        exit_price = stop_level
                    elif hit_tp:
                        exit_price = target_level
                    else:
                        exit_price = None

                    if exit_price is not None:
                        pnl_pts = (entry_price - exit_price)
                        pnl_usd = (pnl_pts * point_value) - friction_per_trade
                        trades.append({
                            'entry_time': timestamps[entry_bar],
                            'exit_time': timestamps[i],
                            'trade_type': trade_type,
                            'pnl_pts': pnl_pts,
                            'pnl_usd': pnl_usd,
                            'year': int(years[i])
                        })
                        pos_size = 0

            # 3. Entry Signal Logic (Max trades per session enforced)
            if pos_size == 0 and daily_trades_count < max_trades_per_day:

                # --- STRATEGY A: INVERSE ORB (Reversal on Wide ORB) ---
                if (mode in ["inverse_only", "combined"]) and is_wide_orb:
                    # Short at ORB High if Overbought relative to VWAP
                    if high_nq[i] >= orb_high and high_nq[i] >= upper1[i]:
                        pos_size = -1
                        entry_price = close_nq[i]
                        entry_bar = i
                        stop_level = orb_high + 15.0  # 15 pt stop above ORB High
                        target_level = orb_low + (0.2 * orb_range)  # Target opposite side of range
                        trade_type = "INVERSE_ORB_SHORT"
                        daily_trades_count += 1

                    # Long at ORB Low if Oversold relative to VWAP
                    elif low_nq[i] <= orb_low and low_nq[i] <= lower1[i]:
                        pos_size = 1
                        entry_price = close_nq[i]
                        entry_bar = i
                        stop_level = orb_low - 15.0  # 15 pt stop below ORB Low
                        target_level = orb_high - (0.2 * orb_range)  # Target opposite side of range
                        trade_type = "INVERSE_ORB_LONG"
                        daily_trades_count += 1

                # --- STRATEGY B: DEFAULT BREAKOUT & RETEST ORB (Normal ORB) ---
                if (mode in ["breakout_only", "combined"]) and not is_wide_orb:
                    # Detect Breakout
                    if close_nq[i] > orb_high:
                        breakout_dir = 1
                        retest_waiting = True
                    elif close_nq[i] < orb_low:
                        breakout_dir = -1
                        retest_waiting = True

                    # Detect Retest of ORB Level
                    if retest_waiting:
                        if breakout_dir == 1 and low_nq[i] <= orb_high + 2.0:
                            pos_size = 1
                            entry_price = close_nq[i]
                            entry_bar = i
                            stop_level = orb_high - 15.0  # 15 pt stop inside ORB
                            target_level = entry_price + 30.0  # 30 pt target (1:2 R:R)
                            trade_type = "BREAKOUT_RETEST_LONG"
                            retest_waiting = False
                            daily_trades_count += 1

                        elif breakout_dir == -1 and high_nq[i] >= orb_low - 2.0:
                            pos_size = -1
                            entry_price = close_nq[i]
                            entry_bar = i
                            stop_level = orb_low + 15.0  # 15 pt stop inside ORB
                            target_level = entry_price - 30.0  # 30 pt target (1:2 R:R)
                            trade_type = "BREAKOUT_RETEST_SHORT"
                            retest_waiting = False
                            daily_trades_count += 1

    return pd.DataFrame(trades)

def calc_stats(df_t, name):
    if len(df_t) == 0:
        return {'Strategy Variant': name, 'Trades': 0, 'Win Rate %': 0, 'Total PnL ($)': 0, 'Profit Factor': 0, 'Expectancy ($/tr)': 0, 'Max Drawdown ($)': 0, 'Win Days %': 0}
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
    
    # Calculate daily metrics across 3 accounts
    daily_pnl = df_t.groupby(df_t['entry_time'].dt.date)['pnl_usd'].sum()
    win_days = (daily_pnl > 0).mean() * 100.0

    return {
        'Strategy Variant': name,
        'Trades': n,
        'Win Rate %': round(wr, 2),
        'Total PnL ($)': round(pnl, 2),
        'Profit Factor': round(pf, 2),
        'Expectancy ($/tr)': round(exp, 2),
        'Max Drawdown ($)': round(dd, 2),
        'Win Days %': round(win_days, 1)
    }

print("\n" + "="*95)
print("   15-MINUTE NY OPENING RANGE BREAKOUT & REVERSAL (ORB) BACKTEST (2010 - 2026)")
print("   3 Copy-Traded Accounts | 1 MNQ per account ($6/pt total)")
print("="*95)

# 1 MNQ per account (3 MNQ total = $6/pt)
df_inv_mnq = run_15m_orb_sim("inverse_only", num_accounts=3, contract_multiplier=2.0)
df_brk_mnq = run_15m_orb_sim("breakout_only", num_accounts=3, contract_multiplier=2.0)
df_comb_mnq = run_15m_orb_sim("combined", num_accounts=3, contract_multiplier=2.0)

# Dec 2025 - Aug 2026 Recent Rangebound Window
df_recent_comb = df_comb_mnq[df_comb_mnq['year'] >= 2025]

stats = [
    calc_stats(df_inv_mnq, "1. Inverse ORB Only (Wide Range Reversals) [3 MNQ]"),
    calc_stats(df_brk_mnq, "2. Breakout & Retest ORB Only (Trend) [3 MNQ]"),
    calc_stats(df_comb_mnq, "3. Complete ORB Suite (Inverse + Breakout) [3 MNQ]"),
    calc_stats(df_recent_comb, "4. Recent Era (2025 - 2026 Range Regime) [3 MNQ]")
]

print(pd.DataFrame(stats).to_string(index=False), flush=True)

# Yearly breakdown of Complete ORB Suite across 3 accounts
print("\n" + "="*80)
print("  YEAR-BY-YEAR PERFORMANCE: 15-MIN COMPLETE ORB SUITE (3 COPY ACCOUNTS)")
print("="*80)

yearly_list = []
for yr, group in df_comb_mnq.groupby('year'):
    st = calc_stats(group, f"Year {yr}")
    yearly_list.append({
        'Year': yr,
        'Trades': st['Trades'],
        'Win Rate %': st['Win Rate %'],
        'Total PnL ($)': st['Total PnL ($)'],
        'Profit Factor': st['Profit Factor'],
        'Expectancy ($/tr)': st['Expectancy ($/tr)'],
        'Max DD ($)': st['Max Drawdown ($)']
    })

print(pd.DataFrame(yearly_list).to_string(index=False), flush=True)

# Save trades
df_comb_mnq.to_csv('orb_15m_trades.csv', index=False)
print("\nSaved full trade log to orb_15m_trades.csv!", flush=True)
