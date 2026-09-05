import sys
from pathlib import Path

_CODE = Path(__file__).resolve().parent
_ROOT = _CODE.parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_CODE) not in sys.path:
    sys.path.insert(0, str(_CODE))

import pandas as pd

from common.paths import DATA, ROOT
import numpy as np
import time

print("Loading preprocessed session cache...", flush=True)
t0 = time.time()
_src = next((c for c in (DATA / "session_cached.parquet", ROOT / "session_cached.parquet") if c.exists()), None)
if _src is None:
    raise FileNotFoundError("session_cached.parquet not found")
df = pd.read_parquet(_src)
print(f"Loaded {len(df):,} rows in {time.time()-t0:.2f}s", flush=True)

day_ids = df['day_id'].to_numpy()
day_splits = np.where(day_ids[:-1] != day_ids[1:])[0] + 1
day_bounds = np.concatenate(([0], day_splits, [len(df)]))

data = {
    'high_nq': df['high_nq'].to_numpy(dtype=np.float64),
    'low_nq': df['low_nq'].to_numpy(dtype=np.float64),
    'close_nq': df['close_nq'].to_numpy(dtype=np.float64),
    'high_es': df['high_es'].to_numpy(dtype=np.float64),
    'low_es': df['low_es'].to_numpy(dtype=np.float64),
    'upper1': df['upper1'].to_numpy(dtype=np.float64),
    'lower1': df['lower1'].to_numpy(dtype=np.float64),
    'bearish_mss': df['bearish_mss'].to_numpy(),
    'bullish_mss': df['bullish_mss'].to_numpy(),
    'ny_minutes': df['ny_minutes'].to_numpy(),
    'years': df['year'].to_numpy(),
    'timestamps': df['ts_event'].to_numpy(),
    'day_bounds': day_bounds
}

def run_sequence_backtest(stop_mode="fixed", fixed_sl=20.0, fixed_tp=30.0, rr_ratio=1.5, friction_pts=0.25):
    """
    Exact Pine Script sequential state machine engine.
    stop_mode: "fixed", "dynamic_smt", or "dynamic_mss"
    """
    overbought_arr = data['high_nq'] >= data['upper1']
    oversold_arr = data['low_nq'] <= data['lower1']

    high_nq, low_nq, close_nq = data['high_nq'], data['low_nq'], data['close_nq']
    high_es, low_es = data['high_es'], data['low_es']
    bearish_mss, bullish_mss = data['bearish_mss'], data['bullish_mss']
    ny_minutes, years, timestamps = data['ny_minutes'], data['years'], data['timestamps']
    day_bounds = data['day_bounds']

    trades = []
    nan_val = float('nan')

    for d_idx in range(len(day_bounds) - 1):
        start_idx = day_bounds[d_idx]
        end_idx = day_bounds[d_idx + 1]

        pos_size, entry_price, entry_bar = 0, 0.0, -1
        stop_level, target_level = nan_val, nan_val

        setup_dir, setup_start_bar = 0, -1
        smt_extreme_price = nan_val

        q1HighNQ, q1LowNQ, q1HighES, q1LowES = nan_val, nan_val, nan_val, nan_val
        q2HighNQ, q2LowNQ, q2HighES, q2LowES = nan_val, nan_val, nan_val, nan_val
        q3HighNQ, q3LowNQ, q3HighES, q3LowES = nan_val, nan_val, nan_val, nan_val
        currQHighNQ, currQLowNQ, currQHighES, currQLowES = nan_val, nan_val, nan_val, nan_val

        q1HighUsed, q1LowUsed = False, False
        q2HighUsed, q2LowUsed = False, False
        q3HighUsed, q3LowUsed = False, False
        prev_q = 0

        for i in range(start_idx, end_idx):
            m = ny_minutes[i]
            if m < 450: currentQ = 1
            elif m < 540: currentQ = 2
            elif m < 630: currentQ = 3
            else: currentQ = 4

            if currentQ != prev_q:
                if currentQ == 2:
                    q1HighNQ, q1LowNQ = currQHighNQ, currQLowNQ
                    q1HighES, q1LowES = currQHighES, currQLowES
                elif currentQ == 3:
                    q2HighNQ, q2LowNQ = currQHighNQ, currQLowNQ
                    q2HighES, q2LowES = currQHighES, currQLowES
                elif currentQ == 4:
                    q3HighNQ, q3LowNQ = currQHighNQ, currQLowNQ
                    q3HighES, q3LowES = currQHighES, currQLowES

                currQHighNQ, currQLowNQ = high_nq[i], low_nq[i]
                currQHighES, currQLowES = high_es[i], low_es[i]
            else:
                currQHighNQ = high_nq[i] if (currQHighNQ != currQHighNQ) else max(currQHighNQ, high_nq[i])
                currQLowNQ = low_nq[i] if (currQLowNQ != currQLowNQ) else min(currQLowNQ, low_nq[i])
                currQHighES = high_es[i] if (currQHighES != currQHighES) else max(currQHighES, high_es[i])
                currQLowES = low_es[i] if (currQLowES != currQLowES) else min(currQLowES, low_es[i])
            prev_q = currentQ

            # Position Exit Check (Evaluated at open of bar, matching Pine process_orders_on_close)
            if pos_size != 0:
                if pos_size == 1:
                    hit_sl = low_nq[i] <= stop_level
                    hit_tp = high_nq[i] >= target_level

                    if hit_sl and hit_tp:
                        exit_price, exit_type = stop_level, "SL"
                    elif hit_sl:
                        exit_price, exit_type = stop_level, "SL"
                    elif hit_tp:
                        exit_price, exit_type = target_level, "TP"
                    else:
                        exit_type = None

                    if exit_type:
                        pnl_pts = (exit_price - entry_price) - friction_pts
                        trades.append({
                            'entry_time': timestamps[entry_bar],
                            'exit_time': timestamps[i],
                            'type': 'LONG',
                            'entry_price': entry_price,
                            'exit_price': exit_price,
                            'exit_type': exit_type,
                            'pnl_pts': pnl_pts,
                            'pnl_usd': pnl_pts * 20.0,
                            'bars_held': i - entry_bar,
                            'year': int(years[i])
                        })
                        pos_size = 0

                elif pos_size == -1:
                    hit_sl = high_nq[i] >= stop_level
                    hit_tp = low_nq[i] <= target_level

                    if hit_sl and hit_tp:
                        exit_price, exit_type = stop_level, "SL"
                    elif hit_sl:
                        exit_price, exit_type = stop_level, "SL"
                    elif hit_tp:
                        exit_price, exit_type = target_level, "TP"
                    else:
                        exit_type = None

                    if exit_type:
                        pnl_pts = (entry_price - exit_price) - friction_pts
                        trades.append({
                            'entry_time': timestamps[entry_bar],
                            'exit_time': timestamps[i],
                            'type': 'SHORT',
                            'entry_price': entry_price,
                            'exit_price': exit_price,
                            'exit_type': exit_type,
                            'pnl_pts': pnl_pts,
                            'pnl_usd': pnl_pts * 20.0,
                            'bars_held': i - entry_bar,
                            'year': int(years[i])
                        })
                        pos_size = 0

            # Evaluate SMT Signals (Matching Pine Script lines 222-299)
            bearishSMT, bullishSMT = False, False

            if currentQ >= 2:
                if not q1HighUsed and (q1HighNQ == q1HighNQ):
                    nqSweep, esSweep = high_nq[i] > q1HighNQ, high_es[i] > q1HighES
                    if (nqSweep and not esSweep) or (esSweep and not nqSweep):
                        if overbought_arr[i]:
                            bearishSMT = True
                            q1HighUsed = True
                            smt_extreme_price = high_nq[i]
                if not q1LowUsed and (q1LowNQ == q1LowNQ):
                    nqSweep, esSweep = low_nq[i] < q1LowNQ, low_es[i] < q1LowES
                    if (nqSweep and not esSweep) or (esSweep and not nqSweep):
                        if oversold_arr[i]:
                            bullishSMT = True
                            q1LowUsed = True
                            smt_extreme_price = low_nq[i]

            if currentQ >= 3:
                if not q2HighUsed and (q2HighNQ == q2HighNQ):
                    nqSweep, esSweep = high_nq[i] > q2HighNQ, high_es[i] > q2HighES
                    if (nqSweep and not esSweep) or (esSweep and not nqSweep):
                        if overbought_arr[i]:
                            bearishSMT = True
                            q2HighUsed = True
                            smt_extreme_price = high_nq[i]
                if not q2LowUsed and (q2LowNQ == q2LowNQ):
                    nqSweep, esSweep = low_nq[i] < q2LowNQ, low_es[i] < q2LowES
                    if (nqSweep and not esSweep) or (esSweep and not nqSweep):
                        if oversold_arr[i]:
                            bullishSMT = True
                            q2LowUsed = True
                            smt_extreme_price = low_nq[i]

            if currentQ == 4:
                if not q3HighUsed and (q3HighNQ == q3HighNQ):
                    nqSweep, esSweep = high_nq[i] > q3HighNQ, high_es[i] > q3HighES
                    if (nqSweep and not esSweep) or (esSweep and not nqSweep):
                        if overbought_arr[i]:
                            bearishSMT = True
                            q3HighUsed = True
                            smt_extreme_price = high_nq[i]
                if not q3LowUsed and (q3LowNQ == q3LowNQ):
                    nqSweep, esSweep = low_nq[i] < q3LowNQ, low_es[i] < q3LowES
                    if (nqSweep and not esSweep) or (esSweep and not nqSweep):
                        if oversold_arr[i]:
                            bullishSMT = True
                            q3LowUsed = True
                            smt_extreme_price = low_nq[i]

            # Setup State Machine (Matching Pine Script lines 349-359)
            if pos_size == 0 and setup_dir == 0:
                if bearishSMT:
                    setup_dir, setup_start_bar = -1, i
                elif bullishSMT:
                    setup_dir, setup_start_bar = 1, i

            if setup_dir != 0 and (i - setup_start_bar > 30):
                setup_dir, setup_start_bar = 0, -1

            waitingShort = (setup_dir == -1) and (i > setup_start_bar)
            waitingLong = (setup_dir == 1) and (i > setup_start_bar)

            longConfirm = bullish_mss[i]
            shortConfirm = bearish_mss[i]

            longSignal = (pos_size == 0) and waitingLong and longConfirm
            shortSignal = (pos_size == 0) and waitingShort and shortConfirm

            if longSignal:
                pos_size = 1
                entry_price = close_nq[i]
                entry_bar = i

                if stop_mode == "fixed":
                    stop_level = entry_price - fixed_sl
                    target_level = entry_price + fixed_tp
                elif stop_mode == "dynamic_smt":
                    sl_dist = max(entry_price - (smt_extreme_price - 2.0), 5.0) if (smt_extreme_price == smt_extreme_price) else fixed_sl
                    stop_level = entry_price - sl_dist
                    target_level = entry_price + (sl_dist * rr_ratio)
                elif stop_mode == "dynamic_mss":
                    s_idx = max(setup_start_bar, start_idx)
                    window_min = np.min(low_nq[s_idx:i+1]) if i >= s_idx else low_nq[i]
                    sl_dist = max(entry_price - (window_min - 2.0), 5.0)
                    stop_level = entry_price - sl_dist
                    target_level = entry_price + (sl_dist * rr_ratio)

                setup_dir, setup_start_bar = 0, -1

            elif shortSignal:
                pos_size = -1
                entry_price = close_nq[i]
                entry_bar = i

                if stop_mode == "fixed":
                    stop_level = entry_price + fixed_sl
                    target_level = entry_price - fixed_tp
                elif stop_mode == "dynamic_smt":
                    sl_dist = max((smt_extreme_price + 2.0) - entry_price, 5.0) if (smt_extreme_price == smt_extreme_price) else fixed_sl
                    stop_level = entry_price + sl_dist
                    target_level = entry_price - (sl_dist * rr_ratio)
                elif stop_mode == "dynamic_mss":
                    s_idx = max(setup_start_bar, start_idx)
                    window_max = np.max(high_nq[s_idx:i+1]) if i >= s_idx else high_nq[i]
                    sl_dist = max((window_max + 2.0) - entry_price, 5.0)
                    stop_level = entry_price + sl_dist
                    target_level = entry_price - (sl_dist * rr_ratio)

                setup_dir, setup_start_bar = 0, -1

    return pd.DataFrame(trades)

def calc_metrics(df_t):
    if len(df_t) == 0:
        return {'trades': 0, 'wr': 0, 'pnl': 0, 'pf': 0, 'exp': 0, 'max_dd': 0}
    n = len(df_t)
    wr = (df_t['pnl_pts'] > 0).mean() * 100.0
    pnl = df_t['pnl_usd'].sum()
    gp = df_t[df_t['pnl_pts'] > 0]['pnl_pts'].sum()
    gl = abs(df_t[df_t['pnl_pts'] < 0]['pnl_pts'].sum())
    pf = gp / gl if gl > 0 else np.nan
    exp = pnl / n
    cum = df_t['pnl_usd'].cumsum()
    dd = (cum.cummax() - cum).max()
    return {'trades': n, 'wr': wr, 'pnl': pnl, 'pf': pf, 'exp': exp, 'max_dd': dd}

print("\n" + "="*95)
print("  EXACT PINE SCRIPT SEQUENCE TEST (2010 - 2026): FIXED VS DYNAMIC STOP LOSS")
print("="*95)

# 1. Fixed Stop Loss (Exact Pine Script 20pt SL / 30pt TP)
df_fixed = run_sequence_backtest("fixed", fixed_sl=20.0, fixed_tp=30.0)
m_fixed = calc_metrics(df_fixed)

# 2. Dynamic Stop Loss (SMT Sweep High/Low + 2pt Buffer, 1:1.5 R:R)
df_dyn_smt_15 = run_sequence_backtest("dynamic_smt", rr_ratio=1.5)
m_dyn_smt_15 = calc_metrics(df_dyn_smt_15)

# 3. Dynamic Stop Loss (SMT Sweep High/Low + 2pt Buffer, 1:2.0 R:R)
df_dyn_smt_20 = run_sequence_backtest("dynamic_smt", rr_ratio=2.0)
m_dyn_smt_20 = calc_metrics(df_dyn_smt_20)

# 4. Dynamic Stop Loss (Setup Swing High/Low + 2pt Buffer, 1:1.5 R:R)
df_dyn_mss_15 = run_sequence_backtest("dynamic_mss", rr_ratio=1.5)
m_dyn_mss_15 = calc_metrics(df_dyn_mss_15)

# 5. Dynamic Stop Loss (Setup Swing High/Low + 2pt Buffer, 1:2.0 R:R)
df_dyn_mss_20 = run_sequence_backtest("dynamic_mss", rr_ratio=2.0)
m_dyn_mss_20 = calc_metrics(df_dyn_mss_20)

results = [
    {"Stop Loss Strategy": "Fixed Stop (Pine Script Default: 20pt SL / 30pt TP)", "Trades": m_fixed['trades'], "WinRate%": round(m_fixed['wr'],2), "Total PnL ($)": round(m_fixed['pnl'],0), "Profit Factor": round(m_fixed['pf'],2), "Expectancy ($)": round(m_fixed['exp'],2), "Max DD ($)": round(m_fixed['max_dd'],0)},
    {"Stop Loss Strategy": "Dynamic SMT Extreme Stop (1:1.5 R:R Target)", "Trades": m_dyn_smt_15['trades'], "WinRate%": round(m_dyn_smt_15['wr'],2), "Total PnL ($)": round(m_dyn_smt_15['pnl'],0), "Profit Factor": round(m_dyn_smt_15['pf'],2), "Expectancy ($)": round(m_dyn_smt_15['exp'],2), "Max DD ($)": round(m_dyn_smt_15['max_dd'],0)},
    {"Stop Loss Strategy": "Dynamic SMT Extreme Stop (1:2.0 R:R Target)", "Trades": m_dyn_smt_20['trades'], "WinRate%": round(m_dyn_smt_20['wr'],2), "Total PnL ($)": round(m_dyn_smt_20['pnl'],0), "Profit Factor": round(m_dyn_smt_20['pf'],2), "Expectancy ($)": round(m_dyn_smt_20['exp'],2), "Max DD ($)": round(m_dyn_smt_20['max_dd'],0)},
    {"Stop Loss Strategy": "Dynamic Setup Swing Stop (1:1.5 R:R Target)", "Trades": m_dyn_mss_15['trades'], "WinRate%": round(m_dyn_mss_15['wr'],2), "Total PnL ($)": round(m_dyn_mss_15['pnl'],0), "Profit Factor": round(m_dyn_mss_15['pf'],2), "Expectancy ($)": round(m_dyn_mss_15['exp'],2), "Max DD ($)": round(m_dyn_mss_15['max_dd'],0)},
    {"Stop Loss Strategy": "Dynamic Setup Swing Stop (1:2.0 R:R Target)", "Trades": m_dyn_mss_20['trades'], "WinRate%": round(m_dyn_mss_20['wr'],2), "Total PnL ($)": round(m_dyn_mss_20['pnl'],0), "Profit Factor": round(m_dyn_mss_20['pf'],2), "Expectancy ($)": round(m_dyn_mss_20['exp'],2), "Max DD ($)": round(m_dyn_mss_20['max_dd'],0)},
]

print(pd.DataFrame(results).to_string(index=False), flush=True)
