import pandas as pd
import numpy as np
import time

print("Starting Hostile Forensic Audit Engine...", flush=True)
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
ny_minutes = df_ny['ny_minutes'].to_numpy()
years = df_ny['year'].to_numpy()
timestamps = df_ny['ts_event'].to_numpy()

# ==============================================================================
# 1. ORIGINAL IMPLEMENTATION REPRODUCTION
# ==============================================================================
def run_original_engine(friction_pts=0.25):
    """Original implementation logic from test_15m_orb_strategy.py"""
    point_val = 6.0  # 3 MNQ = $6/pt
    friction_usd = friction_pts * point_val
    trades = []
    orb_ranges_hist = []

    for d_idx in range(len(day_bounds) - 1):
        start_idx = day_bounds[d_idx]
        end_idx = day_bounds[d_idx + 1]

        orb_high, orb_low = -1.0, 1e9
        orb_complete, orb_end_bar = False, -1

        for i in range(start_idx, end_idx):
            m = ny_minutes[i]
            if 570 <= m < 585:
                if high_nq[i] > orb_high: orb_high = high_nq[i]
                if low_nq[i] < orb_low: orb_low = low_nq[i]
            elif m >= 585 and not orb_complete:
                orb_complete = True
                orb_end_bar = i
                break

        if not orb_complete or orb_high <= 0 or orb_low >= 1e8: continue

        orb_range = orb_high - orb_low
        orb_ranges_hist.append(orb_range)
        avg_orb_range = np.mean(orb_ranges_hist[-20:]) if len(orb_ranges_hist) >= 5 else 35.0
        is_wide_orb = orb_range > (1.10 * avg_orb_range) or orb_range > 40.0

        pos_size, entry_price, entry_bar = 0, 0.0, -1
        stop_level, target_level = 0.0, 0.0
        trade_type = ""
        daily_trades_count = 0

        for i in range(orb_end_bar, end_idx):
            m = ny_minutes[i]
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

            if pos_size == 0 and daily_trades_count < 2:
                if is_wide_orb:
                    if high_nq[i] >= orb_high and high_nq[i] >= upper1[i]:
                        pos_size, entry_price, entry_bar = -1, close_nq[i], i
                        stop_level, target_level = orb_high + 15.0, orb_low + (0.2 * orb_range)
                        trade_type = "INVERSE_ORB_SHORT"
                        daily_trades_count += 1
                    elif low_nq[i] <= orb_low and low_nq[i] <= lower1[i]:
                        pos_size, entry_price, entry_bar = 1, close_nq[i], i
                        stop_level, target_level = orb_low - 15.0, orb_high - (0.2 * orb_range)
                        trade_type = "INVERSE_ORB_LONG"
                        daily_trades_count += 1

    return pd.DataFrame(trades)

# ==============================================================================
# 2. INDEPENDENT SECOND IMPLEMENTATION (STRICT CAUSAL & NO-LOOKAHEAD ENGINE)
# ==============================================================================
def run_independent_engine(fill_mode="limit_exact", friction_pts=0.25, threshold_pts=40.0, sl_pts=15.0, target_frac=0.20, vwap_sd=1.28):
    """
    Second independent implementation built from scratch.
    fill_mode: 'limit_exact' (limit fill at orb_high/low), 'next_open' (market order on open of next bar)
    """
    point_val = 6.0 # 3 MNQ = $6/pt
    friction_usd = friction_pts * point_val
    trades = []
    orb_ranges_hist = []

    for d_idx in range(len(day_bounds) - 1):
        start_idx = day_bounds[d_idx]
        end_idx = day_bounds[d_idx + 1]

        # Strictly build ORB on closed bars 09:30 to 09:44
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

        # Post-ORB evaluation starts at bar index 585 (09:45:00)
        post_bars = [k for k in range(start_idx, end_idx) if ny_minutes[k] >= 585]

        pending_signal = None  # To test next_open fill without lookahead

        for idx_pos, i in enumerate(post_bars):
            m = ny_minutes[i]

            # 1. Fill pending signal from previous bar if next_open mode
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

            # 2. Session Close Check (15:30)
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

            # 3. Active Position Exit Evaluation
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
                    hit_tp = high_nq[i] <= target_level  # Correct target low
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

            # 4. Causal Entry Evaluation
            if pos_size == 0 and daily_count < 2 and not pending_signal:
                if is_wide:
                    if high_nq[i] >= orb_high and high_nq[i] >= upper1[i]:
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

                    elif low_nq[i] <= orb_low and low_nq[i] <= lower1[i]:
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

# Save test outputs for analysis
df_orig = run_original_engine(friction_pts=0.25)
df_indep_limit = run_independent_engine(fill_mode="limit_exact", friction_pts=0.25)
df_indep_open = run_independent_engine(fill_mode="next_open", friction_pts=0.25)
df_indep_close = run_independent_engine(fill_mode="close_orig", friction_pts=0.25)

print("\n--- REIMPLEMENTATION COMPARISON ---")
print(f"Original Engine (close fill) : Trades={len(df_orig)} | PnL=${df_orig['pnl_usd'].sum():,.2f}")
print(f"Indep Engine (close_orig)    : Trades={len(df_indep_close)} | PnL=${df_indep_close['pnl_usd'].sum():,.2f}")
print(f"Indep Engine (limit_exact)   : Trades={len(df_indep_limit)} | PnL=${df_indep_limit['pnl_usd'].sum():,.2f}")
print(f"Indep Engine (next_bar open) : Trades={len(df_indep_open)} | PnL=${df_indep_open['pnl_usd'].sum():,.2f}")

# Store data for reporting script
df_orig.to_parquet('audit_orig_trades.parquet')
df_indep_limit.to_parquet('audit_limit_trades.parquet')
df_indep_open.to_parquet('audit_open_trades.parquet')
print("Completed base run saved to parquet cache!", flush=True)
