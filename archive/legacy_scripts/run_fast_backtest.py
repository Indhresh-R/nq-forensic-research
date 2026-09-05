import pandas as pd
import numpy as np
import math
import time

def load_and_preprocess(band_choice="SD1", pivot_len=2):
    t0 = time.time()
    print("Loading continuous parquets...")
    df_nq = pd.read_parquet('nq_1m_continuous.parquet')
    df_es = pd.read_parquet('es_1m_continuous.parquet')

    df = pd.merge(
        df_nq[['ts_event', 'open', 'high', 'low', 'close', 'volume']],
        df_es[['ts_event', 'open', 'high', 'low', 'close']],
        on='ts_event',
        suffixes=('_nq', '_es'),
        how='inner'
    ).sort_values('ts_event').reset_index(drop=True)

    # Convert timestamps to NY Timezone
    ts_ny = pd.to_datetime(df['ts_event']).dt.tz_convert('America/New_York')
    df['year'] = ts_ny.dt.year
    df['day_id'] = ts_ny.dt.strftime('%Y-%m-%d')
    df['ny_minutes'] = ts_ny.dt.hour * 60 + ts_ny.dt.minute

    # Vectorized Daily VWAP & SD
    print("Vectorizing VWAP calculation...")
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

    if band_choice == "SD1":
        df['overbought'] = df['high_nq'] >= df['upper1']
        df['oversold'] = df['low_nq'] <= df['lower1']
    elif band_choice == "SD2":
        df['overbought'] = df['high_nq'] >= df['upper2']
        df['oversold'] = df['low_nq'] <= df['lower2']
    else:
        df['overbought'] = df['high_nq'] >= df['upper3']
        df['oversold'] = df['low_nq'] <= df['lower3']

    # Vectorized Pivot High / Low (pivot_len = 2)
    print("Vectorizing Pivot High/Low and MSS/iFVG...")
    h = df['high_nq'].to_numpy()
    l = df['low_nq'].to_numpy()
    c = df['close_nq'].to_numpy()
    n = len(df)

    pivot_h = np.full(n, np.nan)
    pivot_l = np.full(n, np.nan)

    # h[i-2] > h[i-4], h[i-3], h[i-1], h[i]
    is_ph = (h[2:-2] > h[:-4]) & (h[2:-2] > h[1:-3]) & (h[2:-2] > h[3:-1]) & (h[2:-2] > h[4:])
    is_pl = (l[2:-2] < l[:-4]) & (l[2:-2] < l[1:-3]) & (l[2:-2] < l[3:-1]) & (l[2:-2] < l[4:])

    # Notice pivot is identified at index i (which is 2 bars after the pivot peak)
    ph_indices = np.where(is_ph)[0] + 4
    pl_indices = np.where(is_pl)[0] + 4

    pivot_h[ph_indices] = h[ph_indices - 2]
    pivot_l[pl_indices] = l[pl_indices - 2]

    # ffill pivot levels
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

    t1 = time.time()
    print(f"Preprocessing completed in {t1 - t0:.2f} seconds.")
    return df

def run_simulation(
    df,
    confirm_bars=30,
    confirmation="MSS Only",
    stop_points=20.0,
    target_points=30.0,
    commission_pts=0.25
):
    t0 = time.time()

    high_nq = df['high_nq'].to_numpy(dtype=np.float64)
    low_nq = df['low_nq'].to_numpy(dtype=np.float64)
    close_nq = df['close_nq'].to_numpy(dtype=np.float64)
    open_nq = df['open_nq'].to_numpy(dtype=np.float64)

    high_es = df['high_es'].to_numpy(dtype=np.float64)
    low_es = df['low_es'].to_numpy(dtype=np.float64)

    overbought = df['overbought'].to_numpy(dtype=bool)
    oversold = df['oversold'].to_numpy(dtype=bool)

    bearish_mss = df['bearish_mss'].to_numpy(dtype=bool)
    bullish_mss = df['bullish_mss'].to_numpy(dtype=bool)
    bearish_ifvg = df['bearish_ifvg'].to_numpy(dtype=bool)
    bullish_ifvg = df['bullish_ifvg'].to_numpy(dtype=bool)

    ny_minutes = df['ny_minutes'].to_numpy(dtype=np.int32)
    day_ids = df['day_id'].to_numpy()
    years = df['year'].to_numpy(dtype=np.int32)
    timestamps = df['ts_event'].to_numpy()

    n = len(df)

    trades = []
    pos_size = 0
    entry_price = 0.0
    entry_idx = 0

    setup_dir = 0
    setup_start_bar = -1

    q1HighNQ, q1LowNQ, q1HighES, q1LowES = np.nan, np.nan, np.nan, np.nan
    q2HighNQ, q2LowNQ, q2HighES, q2LowES = np.nan, np.nan, np.nan, np.nan
    q3HighNQ, q3LowNQ, q3HighES, q3LowES = np.nan, np.nan, np.nan, np.nan

    currQHighNQ, currQLowNQ, currQHighES, currQLowES = np.nan, np.nan, np.nan, np.nan

    q1HighUsed, q1LowUsed = False, False
    q2HighUsed, q2LowUsed = False, False
    q3HighUsed, q3LowUsed = False, False

    curr_day = None
    prev_q = 0

    for i in range(n):
        m = ny_minutes[i]
        day = day_ids[i]

        # Reset daily
        if day != curr_day:
            curr_day = day
            setup_dir = 0
            setup_start_bar = -1

            q1HighNQ, q1LowNQ, q1HighES, q1LowES = np.nan, np.nan, np.nan, np.nan
            q2HighNQ, q2LowNQ, q2HighES, q2LowES = np.nan, np.nan, np.nan, np.nan
            q3HighNQ, q3LowNQ, q3HighES, q3LowES = np.nan, np.nan, np.nan, np.nan
            currQHighNQ, currQLowNQ, currQHighES, currQLowES = np.nan, np.nan, np.nan, np.nan

            q1HighUsed, q1LowUsed = False, False
            q2HighUsed, q2LowUsed = False, False
            q3HighUsed, q3LowUsed = False, False
            prev_q = 0

        # Session Quarters
        if 360 <= m < 450:
            currentQ = 1
        elif 450 <= m < 540:
            currentQ = 2
        elif 540 <= m < 630:
            currentQ = 3
        elif 630 <= m < 720:
            currentQ = 4
        else:
            currentQ = 0

        inSession = (currentQ > 0)
        newQ = inSession and (currentQ != prev_q)

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
        elif inSession:
            currQHighNQ = high_nq[i] if np.isnan(currQHighNQ) else max(currQHighNQ, high_nq[i])
            currQLowNQ = low_nq[i] if np.isnan(currQLowNQ) else min(currQLowNQ, low_nq[i])
            currQHighES = high_es[i] if np.isnan(currQHighES) else max(currQHighES, high_es[i])
            currQLowES = low_es[i] if np.isnan(currQLowES) else min(currQLowES, low_es[i])

        prev_q = currentQ

        # Exit management
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
                    pnl_pts = (exit_price - entry_price) - commission_pts
                    pnl_usd = pnl_pts * 20.0
                    trades.append({
                        'entry_time': timestamps[entry_idx],
                        'exit_time': timestamps[i],
                        'type': 'LONG',
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'exit_type': exit_type,
                        'pnl_pts': pnl_pts,
                        'pnl_usd': pnl_usd,
                        'bars_held': i - entry_idx,
                        'year': years[i]
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
                    pnl_pts = (entry_price - exit_price) - commission_pts
                    pnl_usd = pnl_pts * 20.0
                    trades.append({
                        'entry_time': timestamps[entry_idx],
                        'exit_time': timestamps[i],
                        'type': 'SHORT',
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'exit_type': exit_type,
                        'pnl_pts': pnl_pts,
                        'pnl_usd': pnl_usd,
                        'bars_held': i - entry_idx,
                        'year': years[i]
                    })
                    pos_size = 0

        # Evaluate SMT Signals
        bearishSMT = False
        bullishSMT = False

        if currentQ >= 2:
            if not q1HighUsed and not np.isnan(q1HighNQ):
                nqSweep = high_nq[i] > q1HighNQ
                esSweep = high_es[i] > q1HighES
                if (nqSweep and not esSweep) or (esSweep and not nqSweep):
                    if overbought[i]:
                        bearishSMT = True
                        q1HighUsed = True

            if not q1LowUsed and not np.isnan(q1LowNQ):
                nqSweep = low_nq[i] < q1LowNQ
                esSweep = low_es[i] < q1LowES
                if (nqSweep and not esSweep) or (esSweep and not nqSweep):
                    if oversold[i]:
                        bullishSMT = True
                        q1LowUsed = True

        if currentQ >= 3:
            if not q2HighUsed and not np.isnan(q2HighNQ):
                nqSweep = high_nq[i] > q2HighNQ
                esSweep = high_es[i] > q2HighES
                if (nqSweep and not esSweep) or (esSweep and not nqSweep):
                    if overbought[i]:
                        bearishSMT = True
                        q2HighUsed = True

            if not q2LowUsed and not np.isnan(q2LowNQ):
                nqSweep = low_nq[i] < q2LowNQ
                esSweep = low_es[i] < q2LowES
                if (nqSweep and not esSweep) or (esSweep and not nqSweep):
                    if oversold[i]:
                        bullishSMT = True
                        q2LowUsed = True

        if currentQ == 4:
            if not q3HighUsed and not np.isnan(q3HighNQ):
                nqSweep = high_nq[i] > q3HighNQ
                esSweep = high_es[i] > q3HighES
                if (nqSweep and not esSweep) or (esSweep and not nqSweep):
                    if overbought[i]:
                        bearishSMT = True
                        q3HighUsed = True

            if not q3LowUsed and not np.isnan(q3LowNQ):
                nqSweep = low_nq[i] < q3LowNQ
                esSweep = low_es[i] < q3LowES
                if (nqSweep and not esSweep) or (esSweep and not nqSweep):
                    if oversold[i]:
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
            entry_idx = i
            setup_dir = 0
            setup_start_bar = -1

        elif shortSignal:
            pos_size = -1
            entry_price = close_nq[i]
            entry_idx = i
            setup_dir = 0
            setup_start_bar = -1

    t1 = time.time()
    print(f"Simulation executed in {t1 - t0:.2f} seconds. Total Trades: {len(trades)}")
    return pd.DataFrame(trades)

if __name__ == "__main__":
    df = load_and_preprocess(band_choice="SD1")
    df_trades = run_simulation(df, confirmation="MSS Only")
    print(df_trades.head())
