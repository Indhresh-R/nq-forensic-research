import pandas as pd
import numpy as np
import time

print("Loading preprocessed session cache...", flush=True)
df = pd.read_parquet('session_cached.parquet')

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

def run_multi_smt_sim(allow_multiple_q_sweeps=False, allow_setup_override=False):
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
        setup_dir, setup_start_bar = 0, -1

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

            # Exit Check
            if pos_size != 0:
                if pos_size == 1:
                    sl, tp = entry_price - 20.0, entry_price + 30.0
                    hit_sl, hit_tp = low_nq[i] <= sl, high_nq[i] >= tp
                    exit_price = sl if hit_sl else (tp if hit_tp else None)
                    if exit_price:
                        pnl = (exit_price - entry_price) - 0.25
                        trades.append({'pnl_pts': pnl, 'pnl_usd': pnl * 20.0})
                        pos_size = 0
                elif pos_size == -1:
                    sl, tp = entry_price + 20.0, entry_price - 30.0
                    hit_sl, hit_tp = high_nq[i] >= sl, low_nq[i] <= tp
                    exit_price = sl if hit_sl else (tp if hit_tp else None)
                    if exit_price:
                        pnl = (entry_price - exit_price) - 0.25
                        trades.append({'pnl_pts': pnl, 'pnl_usd': pnl * 20.0})
                        pos_size = 0

            # Evaluate SMT Signals
            bearishSMT, bullishSMT = False, False

            if currentQ >= 2:
                if (not q1HighUsed or allow_multiple_q_sweeps) and (q1HighNQ == q1HighNQ):
                    nqSweep, esSweep = high_nq[i] > q1HighNQ, high_es[i] > q1HighES
                    if (nqSweep and not esSweep) or (esSweep and not nqSweep):
                        if overbought_arr[i]:
                            bearishSMT = True
                            q1HighUsed = True
                if (not q1LowUsed or allow_multiple_q_sweeps) and (q1LowNQ == q1LowNQ):
                    nqSweep, esSweep = low_nq[i] < q1LowNQ, low_es[i] < q1LowES
                    if (nqSweep and not esSweep) or (esSweep and not nqSweep):
                        if oversold_arr[i]:
                            bullishSMT = True
                            q1LowUsed = True

            if currentQ >= 3:
                if (not q2HighUsed or allow_multiple_q_sweeps) and (q2HighNQ == q2HighNQ):
                    nqSweep, esSweep = high_nq[i] > q2HighNQ, high_es[i] > q2HighES
                    if (nqSweep and not esSweep) or (esSweep and not nqSweep):
                        if overbought_arr[i]:
                            bearishSMT = True
                            q2HighUsed = True
                if (not q2LowUsed or allow_multiple_q_sweeps) and (q2LowNQ == q2LowNQ):
                    nqSweep, esSweep = low_nq[i] < q2LowNQ, low_es[i] < q2LowES
                    if (nqSweep and not esSweep) or (esSweep and not nqSweep):
                        if oversold_arr[i]:
                            bullishSMT = True
                            q2LowUsed = True

            if currentQ == 4:
                if (not q3HighUsed or allow_multiple_q_sweeps) and (q3HighNQ == q3HighNQ):
                    nqSweep, esSweep = high_nq[i] > q3HighNQ, high_es[i] > q3HighES
                    if (nqSweep and not esSweep) or (esSweep and not nqSweep):
                        if overbought_arr[i]:
                            bearishSMT = True
                            q3HighUsed = True
                if (not q3LowUsed or allow_multiple_q_sweeps) and (q3LowNQ == q3LowNQ):
                    nqSweep, esSweep = low_nq[i] < q3LowNQ, low_es[i] < q3LowES
                    if (nqSweep and not esSweep) or (esSweep and not nqSweep):
                        if oversold_arr[i]:
                            bullishSMT = True
                            q3LowUsed = True

            # Setup State Machine
            if pos_size == 0 and (setup_dir == 0 or allow_setup_override):
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

            if pos_size == 0 and waitingLong and longConfirm:
                pos_size, entry_price, entry_bar = 1, close_nq[i], i
                setup_dir, setup_start_bar = 0, -1
            elif pos_size == 0 and waitingShort and shortConfirm:
                pos_size, entry_price, entry_bar = -1, close_nq[i], i
                setup_dir, setup_start_bar = 0, -1

    return pd.DataFrame(trades)

df_base = run_multi_smt_sim(False, False)
df_multi_sweep = run_multi_smt_sim(True, False)
df_multi_override = run_multi_smt_sim(True, True)

def print_res(name, df_t):
    wr = (df_t['pnl_pts'] > 0).mean() * 100
    pnl = df_t['pnl_usd'].sum()
    print(f"{name:35s}: Trades={len(df_t):4d} | WR={wr:.2f}% | PnL=${pnl:,.2f}")

print("\n--- SMT UNFILTERED VARIANT COMPARISON ---")
print_res("Pine Script Baseline (1 per Q)", df_base)
print_res("Allow Multiple Sweeps per Q", df_multi_sweep)
print_res("Allow Multiple Sweeps + Override", df_multi_override)
