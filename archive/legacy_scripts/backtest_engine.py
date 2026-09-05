import pandas as pd
import numpy as np
import math
import time

def run_backtest(
    band_choice="SD1",
    pivot_len=2,
    confirm_bars=30,
    confirmation="MSS Only",
    stop_points=20.0,
    target_points=30.0,
    fill_on_close=True,
    commission_pts=0.25 # 1 tick per contract friction (0.25 pts NQ = $5/contract)
):
    t0 = time.time()
    print(f"\n=======================================================")
    print(f"RUNNING BACKTEST: {band_choice} | Pivot={pivot_len} | Confirm={confirmation} | SL={stop_points} | TP={target_points}")
    print(f"=======================================================")

    # 1. Load aligned data
    print("Loading continuous parquet datasets...")
    df_nq = pd.read_parquet('nq_1m_continuous.parquet')
    df_es = pd.read_parquet('es_1m_continuous.parquet')

    # Merge NQ and ES on ts_event
    df = pd.merge(
        df_nq[['ts_event', 'open', 'high', 'low', 'close', 'volume']],
        df_es[['ts_event', 'open', 'high', 'low', 'close']],
        on='ts_event',
        suffixes=('_nq', '_es'),
        how='inner'
    ).sort_values('ts_event').reset_index(drop=True)

    print(f"Aligned dataset rows: {len(df):,}")

    # Convert timestamps to NY Timezone
    ts_ny = pd.to_datetime(df['ts_event']).dt.tz_convert('America/New_York')
    df['year'] = ts_ny.dt.year
    df['day_id'] = ts_ny.dt.strftime('%Y-%m-%d')
    df['ny_minutes'] = ts_ny.dt.hour * 60 + ts_ny.dt.minute

    # Arrays for super-fast simulation
    high_nq = df['high_nq'].to_numpy(dtype=np.float64)
    low_nq = df['low_nq'].to_numpy(dtype=np.float64)
    close_nq = df['close_nq'].to_numpy(dtype=np.float64)
    open_nq = df['open_nq'].to_numpy(dtype=np.float64)
    vol_nq = df['volume_nq'].to_numpy(dtype=np.float64)

    high_es = df['high_es'].to_numpy(dtype=np.float64)
    low_es = df['low_es'].to_numpy(dtype=np.float64)

    ny_minutes = df['ny_minutes'].to_numpy(dtype=np.int32)
    day_ids = df['day_id'].to_numpy()
    years = df['year'].to_numpy(dtype=np.int32)
    timestamps = df['ts_event'].to_numpy()

    n = len(df)

    # 2. Pre-calculate Daily VWAP and Standard Deviations
    print("Calculating Daily VWAP & SD Bands...")
    dev1, dev2, dev3 = 1.28, 2.01, 2.51

    upper1 = np.full(n, np.nan, dtype=np.float64)
    lower1 = np.full(n, np.nan, dtype=np.float64)
    upper2 = np.full(n, np.nan, dtype=np.float64)
    lower2 = np.full(n, np.nan, dtype=np.float64)
    upper3 = np.full(n, np.nan, dtype=np.float64)
    lower3 = np.full(n, np.nan, dtype=np.float64)

    sumPV = 0.0
    sumV = 0.0
    sumPV2 = 0.0
    curr_day = None

    for i in range(n):
        day = day_ids[i]
        if day != curr_day:
            curr_day = day
            hl2 = (high_nq[i] + low_nq[i]) * 0.5
            v = vol_nq[i]
            sumPV = hl2 * v
            sumV = v
            sumPV2 = hl2 * hl2 * v
        else:
            hl2 = (high_nq[i] + low_nq[i]) * 0.5
            v = vol_nq[i]
            sumPV += hl2 * v
            sumV += v
            sumPV2 += hl2 * hl2 * v

        if sumV > 0:
            vwap = sumPV / sumV
            var = max(sumPV2 / sumV - vwap * vwap, 0.0)
            stdev = math.sqrt(var)

            upper1[i] = vwap + dev1 * stdev
            lower1[i] = vwap - dev1 * stdev
            upper2[i] = vwap + dev2 * stdev
            lower2[i] = vwap - dev2 * stdev
            upper3[i] = vwap + dev3 * stdev
            lower3[i] = vwap - dev3 * stdev

    # Overbought / Oversold
    if band_choice == "SD1":
        overbought = high_nq >= upper1
        oversold = low_nq <= lower1
    elif band_choice == "SD2":
        overbought = high_nq >= upper2
        oversold = low_nq <= lower2
    else:
        overbought = high_nq >= upper3
        oversold = low_nq <= lower3

    # 3. MSS and iFVG Signals
    print("Calculating MSS and iFVG signals...")
    pivot_high = np.full(n, np.nan, dtype=np.float64)
    pivot_low = np.full(n, np.nan, dtype=np.float64)

    # Pivot Len = 2
    # At index i, check if high_nq[i-2] is pivot
    for i in range(4, n):
        # pivot high
        if (high_nq[i-2] > high_nq[i-4] and high_nq[i-2] > high_nq[i-3] and
            high_nq[i-2] > high_nq[i-1] and high_nq[i-2] > high_nq[i]):
            pivot_high[i] = high_nq[i-2]

        # pivot low
        if (low_nq[i-2] < low_nq[i-4] and low_nq[i-2] < low_nq[i-3] and
            low_nq[i-2] < low_nq[i-1] and low_nq[i-2] < low_nq[i]):
            pivot_low[i] = low_nq[i-2]

    last_pivot_high = np.full(n, np.nan, dtype=np.float64)
    last_pivot_low = np.full(n, np.nan, dtype=np.float64)

    curr_ph = np.nan
    curr_pl = np.nan
    for i in range(n):
        if not np.isnan(pivot_high[i]):
            curr_ph = pivot_high[i]
        if not np.isnan(pivot_low[i]):
            curr_pl = pivot_low[i]
        last_pivot_high[i] = curr_ph
        last_pivot_low[i] = curr_pl

    # Bearish MSS: close crossunder last_pivot_low
    bearish_mss = np.zeros(n, dtype=bool)
    bullish_mss = np.zeros(n, dtype=bool)
    for i in range(1, n):
        if not np.isnan(last_pivot_low[i]):
            if close_nq[i] < last_pivot_low[i] and close_nq[i-1] >= last_pivot_low[i]:
                bearish_mss[i] = True
        if not np.isnan(last_pivot_high[i]):
            if close_nq[i] > last_pivot_high[i] and close_nq[i-1] <= last_pivot_high[i]:
                bullish_mss[i] = True

    # iFVG
    last_bull_fvg = np.full(n, np.nan, dtype=np.float64)
    last_bear_fvg = np.full(n, np.nan, dtype=np.float64)
    curr_bull_fvg = np.nan
    curr_bear_fvg = np.nan

    for i in range(2, n):
        if low_nq[i] > high_nq[i-2]:
            curr_bull_fvg = high_nq[i-2]
        if high_nq[i] < low_nq[i-2]:
            curr_bear_fvg = low_nq[i-2]
        last_bull_fvg[i] = curr_bull_fvg
        last_bear_fvg[i] = curr_bear_fvg

    bearish_ifvg = np.zeros(n, dtype=bool)
    bullish_ifvg = np.zeros(n, dtype=bool)
    for i in range(1, n):
        if not np.isnan(last_bull_fvg[i]):
            if close_nq[i] < last_bull_fvg[i] and close_nq[i-1] >= last_bull_fvg[i]:
                bearish_ifvg[i] = True
        if not np.isnan(last_bear_fvg[i]):
            if close_nq[i] > last_bear_fvg[i] and close_nq[i-1] <= last_bear_fvg[i]:
                bullish_ifvg[i] = True

    # 4. Simulation Engine
    print("Executing strategy simulation across 16 years of data...")

    trades = []

    # Strategy state
    pos_size = 0  # 0, 1 (long), -1 (short)
    entry_price = 0.0
    entry_idx = 0

    setup_dir = 0  # 0, -1 (short), 1 (long)
    setup_start_bar = -1

    q1HighNQ, q1LowNQ, q1HighES, q1LowES = np.nan, np.nan, np.nan, np.nan
    q2HighNQ, q2LowNQ, q2HighES, q2LowES = np.nan, np.nan, np.nan, np.nan
    q3HighNQ, q3LowNQ, q3HighES, q3LowES = np.nan, np.nan, np.nan, np.nan

    currQHighNQ, currQLowNQ, currQHighES, currQLowES = np.nan, np.nan, np.nan, np.nan

    q1HighUsed, q1LowUsed = False, False
    q2HighUsed, q2LowUsed = False, False
    q3HighUsed, q3LowUsed = False, False

    curr_day_sim = None
    prev_q = 0

    for i in range(n):
        m = ny_minutes[i]
        day = day_ids[i]

        # Check newDay
        if day != curr_day_sim:
            curr_day_sim = day
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

        # Determine current Q
        # Q1: 360 to 449 (06:00 to 07:29)
        # Q2: 450 to 539 (07:30 to 08:59)
        # Q3: 540 to 629 (09:00 to 10:29)
        # Q4: 630 to 719 (10:30 to 11:59)
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

        # ----------------------------------------------------
        # 1. Manage Active Positions Exits
        # ----------------------------------------------------
        if pos_size != 0:
            if pos_size == 1:
                sl_price = entry_price - stop_points
                tp_price = entry_price + target_points

                hit_sl = low_nq[i] <= sl_price
                hit_tp = high_nq[i] >= tp_price

                if hit_sl and hit_tp: # Conservative assumption
                    exit_price = sl_price
                    exit_type = "SL"
                elif hit_sl:
                    exit_price = sl_price
                    exit_type = "SL"
                elif hit_tp:
                    exit_price = tp_price
                    exit_type = "TP"
                else:
                    exit_type = None

                if exit_type:
                    pnl_pts = (exit_price - entry_price) - commission_pts
                    pnl_usd = pnl_pts * 20.0 # $20 per point NQ
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
                sl_price = entry_price + stop_points
                tp_price = entry_price - target_points

                hit_sl = high_nq[i] >= sl_price
                hit_tp = low_nq[i] <= tp_price

                if hit_sl and hit_tp:
                    exit_price = sl_price
                    exit_type = "SL"
                elif hit_sl:
                    exit_price = sl_price
                    exit_type = "SL"
                elif hit_tp:
                    exit_price = tp_price
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

        # ----------------------------------------------------
        # 2. Evaluate SMT Signals
        # ----------------------------------------------------
        bearishSMT = False
        bullishSMT = False

        # Q1 Check
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

        # Q2 Check
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

        # Q3 Check
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

        # ----------------------------------------------------
        # 3. State Machine & Confirmations
        # ----------------------------------------------------
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

        # ----------------------------------------------------
        # 4. Process Entries
        # ----------------------------------------------------
        if longSignal:
            pos_size = 1
            entry_price = close_nq[i] if fill_on_close else open_nq[min(i+1, n-1)]
            entry_idx = i
            setup_dir = 0
            setup_start_bar = -1

        elif shortSignal:
            pos_size = -1
            entry_price = close_nq[i] if fill_on_close else open_nq[min(i+1, n-1)]
            entry_idx = i
            setup_dir = 0
            setup_start_bar = -1

    t1 = time.time()
    print(f"Simulation completed in {t1 - t0:.2f} seconds. Total Trades: {len(trades)}")

    # 5. Calculate Metrics
    df_trades = pd.DataFrame(trades)
    return df_trades

if __name__ == "__main__":
    df_trades = run_backtest()
    if len(df_trades) > 0:
        print("\nFirst 5 trades:")
        print(df_trades.head())
        print("\nOverall Stats:")
        wins = (df_trades['pnl_pts'] > 0).sum()
        total = len(df_trades)
        win_rate = wins / total * 100.0
        total_pnl = df_trades['pnl_pts'].sum()
        gross_profit = df_trades[df_trades['pnl_pts'] > 0]['pnl_pts'].sum()
        gross_loss = abs(df_trades[df_trades['pnl_pts'] < 0]['pnl_pts'].sum())
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else np.nan

        print(f"Total Trades: {total}")
        print(f"Win Rate: {win_rate:.2f}%")
        print(f"Total PnL (Points NQ): {total_pnl:.2f} pts (${total_pnl * 20:,.2f})")
        print(f"Profit Factor: {profit_factor:.2f}")
