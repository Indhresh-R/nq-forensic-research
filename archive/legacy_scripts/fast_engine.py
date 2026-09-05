import pandas as pd
import numpy as np
import math
import time
import sys

def build_dataset(band_choice="SD1"):
    t0 = time.time()
    print("Loading continuous parquets...", flush=True)
    df_nq = pd.read_parquet('nq_1m_continuous.parquet')
    df_es = pd.read_parquet('es_1m_continuous.parquet')

    df = pd.merge(
        df_nq[['ts_event', 'open', 'high', 'low', 'close', 'volume']],
        df_es[['ts_event', 'open', 'high', 'low', 'close', 'volume']],
        on='ts_event',
        suffixes=('_nq', '_es'),
        how='inner'
    ).sort_values('ts_event').reset_index(drop=True)

    ts_ny = pd.to_datetime(df['ts_event']).dt.tz_convert('America/New_York')
    df['year'] = ts_ny.dt.year.astype(np.int16)
    df['day_id'] = ts_ny.dt.strftime('%Y-%m-%d')
    df['ny_minutes'] = (ts_ny.dt.hour * 60 + ts_ny.dt.minute).astype(np.int16)

    # Precalculate VWAP & SD
    print("Calculating VWAP...", flush=True)
    df['hl2'] = (df['high_nq'] + df['low_nq']) * 0.5
    df['pv'] = df['hl2'] * df['volume_nq']
    df['v'] = df['volume_nq']
    df['pv2'] = df['hl2'] * df['hl2'] * df['volume_nq']

    df['cum_pv'] = df.groupby('day_id')['pv'].cumsum()
    df['cum_v'] = df.groupby('day_id')['v'].cumsum()
    df['cum_pv2'] = df.groupby('day_id')['pv2'].cumsum()

    vwap = df['cum_pv'] / df['cum_v']
    variance = np.maximum(df['cum_pv2'] / df['cum_v'] - vwap * vwap, 0.0)
    stdev = np.sqrt(variance)

    dev1, dev2, dev3 = 1.28, 2.01, 2.51
    df['upper1'] = vwap + dev1 * stdev
    df['lower1'] = vwap - dev1 * stdev
    df['upper2'] = vwap + dev2 * stdev
    df['lower2'] = vwap - dev2 * stdev
    df['upper3'] = vwap + dev3 * stdev
    df['lower3'] = vwap - dev3 * stdev

    # Pivot High / Low (pivotLen = 2)
    print("Calculating Pivots & MSS/iFVG...", flush=True)
    h = df['high_nq'].to_numpy()
    l = df['low_nq'].to_numpy()
    c = df['close_nq'].to_numpy()
    n = len(df)

    pivot_h = np.full(n, np.nan, dtype=np.float32)
    pivot_l = np.full(n, np.nan, dtype=np.float32)

    is_ph = (h[2:-2] > h[:-4]) & (h[2:-2] > h[1:-3]) & (h[2:-2] > h[3:-1]) & (h[2:-2] > h[4:])
    is_pl = (l[2:-2] < l[:-4]) & (l[2:-2] < l[1:-3]) & (l[2:-2] < l[3:-1]) & (l[2:-2] < l[4:])

    ph_indices = np.where(is_ph)[0] + 4
    pl_indices = np.where(is_pl)[0] + 4

    pivot_h[ph_indices] = h[ph_indices - 2]
    pivot_l[pl_indices] = l[pl_indices - 2]

    df['pivot_h'] = pd.Series(pivot_h).ffill()
    df['pivot_l'] = pd.Series(pivot_l).ffill()

    # MSS
    df['bearish_mss'] = (c < df['pivot_l']) & (np.roll(c, 1) >= df['pivot_l'])
    df['bullish_mss'] = (c > df['pivot_h']) & (np.roll(c, 1) <= df['pivot_h'])

    # iFVG
    df['bull_fvg'] = df['low_nq'] > df['high_nq'].shift(2)
    df['bear_fvg'] = df['high_nq'] < df['low_nq'].shift(2)

    df['last_bull_fvg'] = np.where(df['bull_fvg'], df['high_nq'].shift(2), np.nan)
    df['last_bear_fvg'] = np.where(df['bear_fvg'], df['low_nq'].shift(2), np.nan)

    df['last_bull_fvg'] = df['last_bull_fvg'].ffill()
    df['last_bear_fvg'] = df['last_bear_fvg'].ffill()

    df['bearish_ifvg'] = (c < df['last_bull_fvg']) & (np.roll(c, 1) >= df['last_bull_fvg'])
    df['bullish_ifvg'] = (c > df['last_bear_fvg']) & (np.roll(c, 1) <= df['last_bear_fvg'])

    # Keep session bars (06:00 to 12:00 NY time)
    session_df = df[(df['ny_minutes'] >= 360) & (df['ny_minutes'] < 720)].copy().reset_index(drop=True)

    t1 = time.time()
    print(f"Dataset preprocessed in {t1 - t0:.2f}s | Session rows: {len(session_df):,}", flush=True)
    return session_df

def run_fast_simulation(
    df,
    band_choice="SD1",
    confirm_bars=30,
    confirmation="MSS Only",
    stop_points=20.0,
    target_points=30.0,
    friction_pts=0.25
):
    t0 = time.time()

    if band_choice == "SD1":
        overbought_arr = (df['high_nq'] >= df['upper1']).to_numpy()
        oversold_arr = (df['low_nq'] <= df['lower1']).to_numpy()
    elif band_choice == "SD2":
        overbought_arr = (df['high_nq'] >= df['upper2']).to_numpy()
        oversold_arr = (df['low_nq'] <= df['lower2']).to_numpy()
    else:
        overbought_arr = (df['high_nq'] >= df['upper3']).to_numpy()
        oversold_arr = (df['low_nq'] <= df['lower3']).to_numpy()

    high_nq = df['high_nq'].to_numpy(dtype=np.float64)
    low_nq = df['low_nq'].to_numpy(dtype=np.float64)
    close_nq = df['close_nq'].to_numpy(dtype=np.float64)

    high_es = df['high_es'].to_numpy(dtype=np.float64)
    low_es = df['low_es'].to_numpy(dtype=np.float64)

    bearish_mss = df['bearish_mss'].to_numpy()
    bullish_mss = df['bullish_mss'].to_numpy()
    bearish_ifvg = df['bearish_ifvg'].to_numpy()
    bullish_ifvg = df['bullish_ifvg'].to_numpy()

    ny_minutes = df['ny_minutes'].to_numpy()
    day_ids = df['day_id'].to_numpy()
    years = df['year'].to_numpy()
    timestamps = df['ts_event'].to_numpy()

    trades = []

    day_splits = np.where(day_ids[:-1] != day_ids[1:])[0] + 1
    day_bounds = np.concatenate(([0], day_splits, [len(df)]))

    nan_val = float('nan')

    for d_idx in range(len(day_bounds) - 1):
        start_idx = day_bounds[d_idx]
        end_idx = day_bounds[d_idx + 1]

        pos_size = 0
        entry_price = 0.0
        entry_bar = -1

        setup_dir = 0
        setup_start_bar = -1

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

            if m < 450:
                currentQ = 1
            elif m < 540:
                currentQ = 2
            elif m < 630:
                currentQ = 3
            else:
                currentQ = 4

            newQ = (currentQ != prev_q)

            if newQ:
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
                currQHighNQ = high_nq[i] if (currQHighNQ != currQHighNQ) else (high_nq[i] if high_nq[i] > currQHighNQ else currQHighNQ)
                currQLowNQ = low_nq[i] if (currQLowNQ != currQLowNQ) else (low_nq[i] if low_nq[i] < currQLowNQ else currQLowNQ)
                currQHighES = high_es[i] if (currQHighES != currQHighES) else (high_es[i] if high_es[i] > currQHighES else currQHighES)
                currQLowES = low_es[i] if (currQLowES != currQLowES) else (low_es[i] if low_es[i] < currQLowES else currQLowES)

            prev_q = currentQ

            # Position Exit Check
            if pos_size != 0:
                if pos_size == 1:
                    sl = entry_price - stop_points
                    tp = entry_price + target_points
                    hit_sl = low_nq[i] <= sl
                    hit_tp = high_nq[i] >= tp

                    if hit_sl and hit_tp:
                        exit_price = sl
                        exit_type = "SL"
                    elif hit_sl:
                        exit_price = sl
                        exit_type = "SL"
                    elif hit_tp:
                        exit_price = tp
                        exit_type = "TP"
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
                    sl = entry_price + stop_points
                    tp = entry_price - target_points
                    hit_sl = high_nq[i] >= sl
                    hit_tp = low_nq[i] <= tp

                    if hit_sl and hit_tp:
                        exit_price = sl
                        exit_type = "SL"
                    elif hit_sl:
                        exit_price = sl
                        exit_type = "SL"
                    elif hit_tp:
                        exit_price = tp
                        exit_type = "TP"
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

            # Evaluate SMT Signals
            bearishSMT = False
            bullishSMT = False

            if currentQ >= 2:
                if not q1HighUsed and (q1HighNQ == q1HighNQ):
                    nqSweep = high_nq[i] > q1HighNQ
                    esSweep = high_es[i] > q1HighES
                    if (nqSweep and not esSweep) or (esSweep and not nqSweep):
                        if overbought_arr[i]:
                            bearishSMT = True
                            q1HighUsed = True

                if not q1LowUsed and (q1LowNQ == q1LowNQ):
                    nqSweep = low_nq[i] < q1LowNQ
                    esSweep = low_es[i] < q1LowES
                    if (nqSweep and not esSweep) or (esSweep and not nqSweep):
                        if oversold_arr[i]:
                            bullishSMT = True
                            q1LowUsed = True

            if currentQ >= 3:
                if not q2HighUsed and (q2HighNQ == q2HighNQ):
                    nqSweep = high_nq[i] > q2HighNQ
                    esSweep = high_es[i] > q2HighES
                    if (nqSweep and not esSweep) or (esSweep and not nqSweep):
                        if overbought_arr[i]:
                            bearishSMT = True
                            q2HighUsed = True

                if not q2LowUsed and (q2LowNQ == q2LowNQ):
                    nqSweep = low_nq[i] < q2LowNQ
                    esSweep = low_es[i] < q2LowES
                    if (nqSweep and not esSweep) or (esSweep and not nqSweep):
                        if oversold_arr[i]:
                            bullishSMT = True
                            q2LowUsed = True

            if currentQ == 4:
                if not q3HighUsed and (q3HighNQ == q3HighNQ):
                    nqSweep = high_nq[i] > q3HighNQ
                    esSweep = high_es[i] > q3HighES
                    if (nqSweep and not esSweep) or (esSweep and not nqSweep):
                        if overbought_arr[i]:
                            bearishSMT = True
                            q3HighUsed = True

                if not q3LowUsed and (q3LowNQ == q3LowNQ):
                    nqSweep = low_nq[i] < q3LowNQ
                    esSweep = low_es[i] < q3LowES
                    if (nqSweep and not esSweep) or (esSweep and not nqSweep):
                        if oversold_arr[i]:
                            bullishSMT = True
                            q3LowUsed = True

            # Setup State Machine
            if pos_size == 0 and setup_dir == 0:
                if bearishSMT:
                    setup_dir = -1
                    setup_start_bar = i
                elif bullishSMT:
                    setup_dir = 1
                    setup_start_bar = i

            if setup_dir != 0 and (i - setup_start_bar > confirm_bars):
                setup_dir = 0
                setup_start_bar = -1

            waitingShort = (setup_dir == -1) and (i > setup_start_bar)
            waitingLong = (setup_dir == 1) and (i > setup_start_bar)

            if confirmation == "MSS Only":
                shortConfirm = bearish_mss[i]
                longConfirm = bullish_mss[i]
            elif confirmation == "iFVG Only":
                shortConfirm = bearish_ifvg[i]
                longConfirm = bullish_ifvg[i]
            else: # MSS OR iFVG
                shortConfirm = bearish_mss[i] or bearish_ifvg[i]
                longConfirm = bullish_mss[i] or bullish_ifvg[i]

            longSignal = (pos_size == 0) and waitingLong and longConfirm
            shortSignal = (pos_size == 0) and waitingShort and shortConfirm

            if longSignal:
                pos_size = 1
                entry_price = close_nq[i]
                entry_bar = i
                setup_dir = 0
                setup_start_bar = -1

            elif shortSignal:
                pos_size = -1
                entry_price = close_nq[i]
                entry_bar = i
                setup_dir = 0
                setup_start_bar = -1

    t1 = time.time()
    print(f"Simulation completed in {t1 - t0:.2f}s | Total Trades: {len(trades)}", flush=True)
    return pd.DataFrame(trades)

def get_stats(df_t):
    if len(df_t) == 0:
        return {'trades': 0, 'win_rate': 0.0, 'pnl_pts': 0.0, 'pnl_usd': 0.0, 'pf': 0.0, 'exp_usd': 0.0, 'max_dd': 0.0}
    n_t = len(df_t)
    wins = (df_t['pnl_pts'] > 0).sum()
    wr = wins / n_t * 100.0
    pnl_pts = df_t['pnl_pts'].sum()
    pnl_usd = df_t['pnl_usd'].sum()
    gp = df_t[df_t['pnl_pts'] > 0]['pnl_pts'].sum()
    gl = abs(df_t[df_t['pnl_pts'] < 0]['pnl_pts'].sum())
    pf = gp / gl if gl > 0 else np.nan
    exp_usd = pnl_usd / n_t
    cum = df_t['pnl_usd'].cumsum()
    max_dd = (cum.cummax() - cum).max()
    return {
        'trades': n_t,
        'win_rate': wr,
        'pnl_pts': pnl_pts,
        'pnl_usd': pnl_usd,
        'pf': pf,
        'exp_usd': exp_usd,
        'max_dd': max_dd
    }

if __name__ == "__main__":
    df = build_dataset(band_choice="SD1")
    df_trades = run_fast_simulation(df, band_choice="SD1", confirm_bars=30, confirmation="MSS Only", stop_points=20.0, target_points=30.0)

    print("\n--- BASELINE RESULTS (2010 - 2026) ---", flush=True)
    res = get_stats(df_trades)
    for k, v in res.items():
        print(f"{k}: {v:.2f}" if isinstance(v, float) else f"{k}: {v}", flush=True)

    # Splits
    df_is = df_trades[df_trades['year'] <= 2020]
    df_oos = df_trades[df_trades['year'] >= 2021]

    print("\n--- IN-SAMPLE (2010 - 2020) ---", flush=True)
    res_is = get_stats(df_is)
    for k, v in res_is.items():
        print(f"{k}: {v:.2f}" if isinstance(v, float) else f"{k}: {v}", flush=True)

    print("\n--- OUT-OF-SAMPLE (2021 - 2026) ---", flush=True)
    res_oos = get_stats(df_oos)
    for k, v in res_oos.items():
        print(f"{k}: {v:.2f}" if isinstance(v, float) else f"{k}: {v}", flush=True)

    # Yearly Table
    print("\n--- YEARLY PERFORMANCE ---", flush=True)
    years = sorted(df_trades['year'].unique())
    y_list = []
    for y in years:
        sub = df_trades[df_trades['year'] == y]
        st = get_stats(sub)
        y_list.append({
            'Year': y, 'Trades': st['trades'], 'WinRate%': round(st['win_rate'], 1),
            'PnL_Pts': round(st['pnl_pts'], 1), 'PnL_USD': round(st['pnl_usd'], 0),
            'PF': round(st['pf'], 2), 'Expectancy_$': round(st['exp_usd'], 1),
            'MaxDD_$': round(st['max_dd'], 0)
        })
    print(pd.DataFrame(y_list).to_string(index=False), flush=True)

    df_trades.to_csv('baseline_trades.csv', index=False)
