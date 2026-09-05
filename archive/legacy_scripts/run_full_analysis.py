import pandas as pd
import numpy as np
import time

def load_preprocessed_data():
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
    df['year'] = ts_ny.dt.year.astype(np.int16)
    df['day_id'] = ts_ny.dt.strftime('%Y-%m-%d')
    df['ny_minutes'] = (ts_ny.dt.hour * 60 + ts_ny.dt.minute).astype(np.int16)

    # Vectorized Daily VWAP & SD
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

    # Vectorized Pivot High / Low (pivot_len = 2)
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

    t1 = time.time()
    print(f"Data preprocessed in {t1 - t0:.2f} seconds.")
    return df

def simulate(df, band_choice="SD1", confirm_bars=30, confirmation="MSS Only", stop_points=20.0, target_points=30.0, friction_pts=0.25):
    t0 = time.time()

    if band_choice == "SD1":
        overbought = (df['high_nq'] >= df['upper1']).to_numpy()
        oversold = (df['low_nq'] <= df['lower1']).to_numpy()
    elif band_choice == "SD2":
        overbought = (df['high_nq'] >= df['upper2']).to_numpy()
        oversold = (df['low_nq'] <= df['lower2']).to_numpy()
    else:
        overbought = (df['high_nq'] >= df['upper3']).to_numpy()
        oversold = (df['low_nq'] <= df['lower3']).to_numpy()

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

        # Fast skip: if not in session (06:00 to 12:00) and no position is open, continue!
        if (m < 360 or m >= 720) and pos_size == 0:
            continue

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
                    pnl_pts = (exit_price - entry_price) - friction_pts
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
                        'year': int(years[i])
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
    # print(f"Simulation executed in {t1 - t0:.2f}s | Trades: {len(trades)}")
    return pd.DataFrame(trades)

def compute_metrics(df_t, initial_capital=100000.0):
    if len(df_t) == 0:
        return {
            'trades': 0, 'win_rate': 0.0, 'total_pnl_pts': 0.0, 'total_pnl_usd': 0.0,
            'profit_factor': 0.0, 'expectancy_usd': 0.0, 'max_drawdown_usd': 0.0, 'sharpe': 0.0
        }
    
    n_trades = len(df_t)
    wins = (df_t['pnl_pts'] > 0).sum()
    win_rate = wins / n_trades * 100.0
    total_pnl_pts = df_t['pnl_pts'].sum()
    total_pnl_usd = df_t['pnl_usd'].sum()
    
    gross_profit = df_t[df_t['pnl_pts'] > 0]['pnl_pts'].sum()
    gross_loss = abs(df_t[df_t['pnl_pts'] < 0]['pnl_pts'].sum())
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else np.nan
    expectancy_usd = total_pnl_usd / n_trades
    
    # Cumulative PnL and Drawdown
    cum_pnl = df_t['pnl_usd'].cumsum()
    peak = cum_pnl.cummax()
    dd = peak - cum_pnl
    max_dd = dd.max()
    
    # Return metrics
    return {
        'trades': n_trades,
        'win_rate': win_rate,
        'total_pnl_pts': total_pnl_pts,
        'total_pnl_usd': total_pnl_usd,
        'profit_factor': profit_factor,
        'expectancy_usd': expectancy_usd,
        'max_drawdown_usd': max_dd,
        'avg_bars_held': df_t['bars_held'].mean()
    }

if __name__ == "__main__":
    df = load_preprocessed_data()
    
    print("\n=======================================================")
    print("      RUNNING STRATEGY EVALUATION & DATASET SPLITS     ")
    print("=======================================================")
    
    # 1. Baseline Run (Pine Script Default: SD1, MSS Only, SL=20, TP=30)
    df_trades = simulate(df, band_choice="SD1", confirm_bars=30, confirmation="MSS Only", stop_points=20.0, target_points=30.0, friction_pts=0.25)
    
    print("\n--- BASELINE METRICS (FULL DATASET: JUNE 2010 - AUGUST 2026) ---")
    m_full = compute_metrics(df_trades)
    print(f"Total Trades: {m_full['trades']}")
    print(f"Win Rate: {m_full['win_rate']:.2f}%")
    print(f"Total PnL (Points NQ): {m_full['total_pnl_pts']:.2f} pts")
    print(f"Total PnL ($): ${m_full['total_pnl_usd']:,.2f}")
    print(f"Profit Factor: {m_full['profit_factor']:.2f}")
    print(f"Expectancy ($ / trade): ${m_full['expectancy_usd']:.2f}")
    print(f"Max Drawdown ($): ${m_full['max_drawdown_usd']:,.2f}")
    print(f"Avg Duration (bars): {m_full['avg_bars_held']:.1f} mins")

    # 2. IN-SAMPLE vs OUT-OF-SAMPLE SPLIT
    # In-Sample: 2010 to 2020 (10.5 years)
    # Out-Of-Sample: 2021 to 2026 (5.6 years)
    df_is = df_trades[df_trades['year'] <= 2020]
    df_oos = df_trades[df_trades['year'] >= 2021]

    m_is = compute_metrics(df_is)
    m_oos = compute_metrics(df_oos)

    print("\n--- IN-SAMPLE (2010 - 2020) METRICS ---")
    print(f"Trades: {m_is['trades']} | Win Rate: {m_is['win_rate']:.2f}% | PnL: ${m_is['total_pnl_usd']:,.2f} | PF: {m_is['profit_factor']:.2f} | Expectancy: ${m_is['expectancy_usd']:.2f} | Max DD: ${m_is['max_drawdown_usd']:,.2f}")

    print("\n--- OUT-OF-SAMPLE (2021 - 2026) METRICS ---")
    print(f"Trades: {m_oos['trades']} | Win Rate: {m_oos['win_rate']:.2f}% | PnL: ${m_oos['total_pnl_usd']:,.2f} | PF: {m_oos['profit_factor']:.2f} | Expectancy: ${m_oos['expectancy_usd']:.2f} | Max DD: ${m_oos['max_drawdown_usd']:,.2f}")

    # 3. YEAR-BY-YEAR BREAKDOWN
    print("\n--- YEAR-BY-YEAR BREAKDOWN ---")
    years = sorted(df_trades['year'].unique())
    yearly_rows = []
    for y in years:
        df_y = df_trades[df_trades['year'] == y]
        m_y = compute_metrics(df_y)
        yearly_rows.append({
            'Year': y,
            'Trades': m_y['trades'],
            'Win Rate (%)': round(m_y['win_rate'], 2),
            'PnL (Pts)': round(m_y['total_pnl_pts'], 2),
            'PnL ($)': round(m_y['total_pnl_usd'], 2),
            'Profit Factor': round(m_y['profit_factor'], 2),
            'Expectancy ($)': round(m_y['expectancy_usd'], 2),
            'Max DD ($)': round(m_y['max_drawdown_usd'], 2)
        })
    df_yearly = pd.DataFrame(yearly_rows)
    print(df_yearly.to_string(index=False))

    # Save results to CSV for reporting
    df_trades.to_csv('all_trades.csv', index=False)
    df_yearly.to_csv('yearly_performance.csv', index=False)
    print("\nTrades and yearly performance saved to all_trades.csv and yearly_performance.csv")
