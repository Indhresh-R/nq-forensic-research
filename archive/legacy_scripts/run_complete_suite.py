import pandas as pd
import numpy as np
import time

def run_sim_numpy(
    data,
    band_choice="SD1",
    confirm_bars=30,
    confirmation="MSS Only",
    stop_points=20.0,
    target_points=30.0,
    friction_pts=0.25
):
    if band_choice == "SD1":
        overbought_arr = data['high_nq'] >= data['upper1']
        oversold_arr = data['low_nq'] <= data['lower1']
    elif band_choice == "SD2":
        overbought_arr = data['high_nq'] >= data['upper2']
        oversold_arr = data['low_nq'] <= data['lower2']
    else:
        overbought_arr = data['high_nq'] >= data['upper3']
        oversold_arr = data['low_nq'] <= data['lower3']

    high_nq = data['high_nq']
    low_nq = data['low_nq']
    close_nq = data['close_nq']
    high_es = data['high_es']
    low_es = data['low_es']

    bearish_mss = data['bearish_mss']
    bullish_mss = data['bullish_mss']
    bearish_ifvg = data['bearish_ifvg']
    bullish_ifvg = data['bullish_ifvg']

    ny_minutes = data['ny_minutes']
    years = data['years']
    timestamps = data['timestamps']
    day_bounds = data['day_bounds']

    trades = []
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

    return pd.DataFrame(trades)

def get_stats(df_t):
    if len(df_t) == 0:
        return {
            'trades': 0, 'win_rate': 0.0, 'pnl_pts': 0.0, 'pnl_usd': 0.0,
            'pf': 0.0, 'exp_usd': 0.0, 'max_dd': 0.0, 'avg_bars': 0.0
        }
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
    avg_bars = df_t['bars_held'].mean()
    return {
        'trades': n_t,
        'win_rate': wr,
        'pnl_pts': pnl_pts,
        'pnl_usd': pnl_usd,
        'pf': pf,
        'exp_usd': exp_usd,
        'max_dd': max_dd,
        'avg_bars': avg_bars
    }

if __name__ == "__main__":
    t_start = time.time()
    print("Loading preprocessed session cache...", flush=True)
    df = pd.read_parquet('session_cached.parquet')
    print(f"Loaded {len(df):,} session rows in {time.time() - t_start:.2f}s", flush=True)

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
        'upper2': df['upper2'].to_numpy(dtype=np.float64),
        'lower2': df['lower2'].to_numpy(dtype=np.float64),
        'upper3': df['upper3'].to_numpy(dtype=np.float64),
        'lower3': df['lower3'].to_numpy(dtype=np.float64),
        'bearish_mss': df['bearish_mss'].to_numpy(),
        'bullish_mss': df['bullish_mss'].to_numpy(),
        'bearish_ifvg': df['bearish_ifvg'].to_numpy(),
        'bullish_ifvg': df['bullish_ifvg'].to_numpy(),
        'ny_minutes': df['ny_minutes'].to_numpy(),
        'years': df['year'].to_numpy(),
        'timestamps': df['ts_event'].to_numpy(),
        'day_bounds': day_bounds
    }

    # =========================================================================
    # 1. BASELINE BACKTEST (Pine Script Settings: SD1, MSS Only, SL 20, TP 30)
    # =========================================================================
    df_trades_base = run_sim_numpy(
        data, band_choice="SD1", confirm_bars=30, confirmation="MSS Only",
        stop_points=20.0, target_points=30.0, friction_pts=0.25
    )
    df_trades_base.to_csv('baseline_trades.csv', index=False)

    print("\n" + "="*80, flush=True)
    print("      1. BASELINE STRATEGY PERFORMANCE (JUNE 2010 - AUGUST 2026)", flush=True)
    print("="*80, flush=True)
    st = get_stats(df_trades_base)
    print(f"Total Trades: {st['trades']}", flush=True)
    print(f"Win Rate: {st['win_rate']:.2f}%", flush=True)
    print(f"Total PnL (Points NQ): {st['pnl_pts']:.2f} pts", flush=True)
    print(f"Total PnL ($): ${st['pnl_usd']:,.2f}", flush=True)
    print(f"Profit Factor: {st['pf']:.2f}", flush=True)
    print(f"Expectancy ($ / trade): ${st['exp_usd']:.2f}", flush=True)
    print(f"Max Drawdown ($): ${st['max_dd']:,.2f}", flush=True)
    print(f"Avg Duration: {st['avg_bars']:.1f} mins", flush=True)

    # =========================================================================
    # 2. DATASET SPLIT ANALYSIS (IN-SAMPLE VS OUT-OF-SAMPLE)
    # =========================================================================
    print("\n" + "="*80, flush=True)
    print("      2. DATASET SPLIT ANALYSIS (IN-SAMPLE VS OUT-OF-SAMPLE)", flush=True)
    print("="*80, flush=True)

    df_is = df_trades_base[df_trades_base['year'] <= 2020]
    df_oos = df_trades_base[df_trades_base['year'] >= 2021]

    st_is = get_stats(df_is)
    st_oos = get_stats(df_oos)

    split_2p = [
        {'Period': 'In-Sample (2010-2020)', 'Years': '10.5', 'Trades': st_is['trades'], 'WinRate%': round(st_is['win_rate'],2), 'PnL_Pts': round(st_is['pnl_pts'],1), 'PnL_$': round(st_is['pnl_usd'],0), 'PF': round(st_is['pf'],2), 'Exp_$': round(st_is['exp_usd'],2), 'MaxDD_$': round(st_is['max_dd'],0)},
        {'Period': 'Out-Of-Sample (2021-2026)', 'Years': '5.6', 'Trades': st_oos['trades'], 'WinRate%': round(st_oos['win_rate'],2), 'PnL_Pts': round(st_oos['pnl_pts'],1), 'PnL_$': round(st_oos['pnl_usd'],0), 'PF': round(st_oos['pf'],2), 'Exp_$': round(st_oos['exp_usd'],2), 'MaxDD_$': round(st_oos['max_dd'],0)},
    ]
    print(pd.DataFrame(split_2p).to_string(index=False), flush=True)

    # 3-Era Breakdown
    df_p1 = df_trades_base[df_trades_base['year'] <= 2015]
    df_p2 = df_trades_base[(df_trades_base['year'] >= 2016) & (df_trades_base['year'] <= 2020)]
    df_p3 = df_trades_base[df_trades_base['year'] >= 2021]

    st_p1, st_p2, st_p3 = get_stats(df_p1), get_stats(df_p2), get_stats(df_p3)
    split_3p = [
        {'Era': 'Early Horizon (2010-2015)', 'Trades': st_p1['trades'], 'WinRate%': round(st_p1['win_rate'],2), 'PnL_Pts': round(st_p1['pnl_pts'],1), 'PnL_$': round(st_p1['pnl_usd'],0), 'PF': round(st_p1['pf'],2), 'Exp_$': round(st_p1['exp_usd'],2), 'MaxDD_$': round(st_p1['max_dd'],0)},
        {'Era': 'Mid Horizon (2016-2020)', 'Trades': st_p2['trades'], 'WinRate%': round(st_p2['win_rate'],2), 'PnL_Pts': round(st_p2['pnl_pts'],1), 'PnL_$': round(st_p2['pnl_usd'],0), 'PF': round(st_p2['pf'],2), 'Exp_$': round(st_p2['exp_usd'],2), 'MaxDD_$': round(st_p2['max_dd'],0)},
        {'Era': 'Recent Horizon (2021-2026)', 'Trades': st_p3['trades'], 'WinRate%': round(st_p3['win_rate'],2), 'PnL_Pts': round(st_p3['pnl_pts'],1), 'PnL_$': round(st_p3['pnl_usd'],0), 'PF': round(st_p3['pf'],2), 'Exp_$': round(st_p3['exp_usd'],2), 'MaxDD_$': round(st_p3['max_dd'],0)},
    ]
    print("\n--- 3-ERA BREAKDOWN ---", flush=True)
    print(pd.DataFrame(split_3p).to_string(index=False), flush=True)

    # =========================================================================
    # 3. YEAR-BY-YEAR DETAILED LEDGER
    # =========================================================================
    print("\n" + "="*80, flush=True)
    print("      3. YEAR-BY-YEAR PERFORMANCE LEDGER (2010 - 2026)", flush=True)
    print("="*80, flush=True)
    years = sorted(df_trades_base['year'].unique())
    y_rows = []
    for y in years:
        sub = df_trades_base[df_trades_base['year'] == y]
        st_y = get_stats(sub)
        y_rows.append({
            'Year': y,
            'Trades': st_y['trades'],
            'WinRate%': round(st_y['win_rate'], 1),
            'PnL_Pts': round(st_y['pnl_pts'], 1),
            'PnL_USD': round(st_y['pnl_usd'], 0),
            'PF': round(st_y['pf'], 2),
            'Expectancy_$': round(st_y['exp_usd'], 1),
            'MaxDD_$': round(st_y['max_dd'], 0)
        })
    df_yearly = pd.DataFrame(y_rows)
    print(df_yearly.to_string(index=False), flush=True)
    df_yearly.to_csv('yearly_performance.csv', index=False)

    # =========================================================================
    # 4. FRICTION & SLIPPAGE SENSITIVITY
    # =========================================================================
    print("\n" + "="*80, flush=True)
    print("      4. FRICTION & SLIPPAGE SENSITIVITY", flush=True)
    print("="*80, flush=True)
    frictions = [
        ("Zero Friction (Ideal)", 0.0),
        ("1 Tick Friction ($5/rt)", 0.25),
        ("2 Ticks Friction ($10/rt)", 0.50),
        ("4 Ticks Friction ($20/rt)", 1.00)
    ]
    f_rows = []
    for f_label, f_pts in frictions:
        df_f = run_sim_numpy(data, friction_pts=f_pts)
        st_f = get_stats(df_f)
        f_rows.append({
            'Friction Level': f_label,
            'Trades': st_f['trades'],
            'WinRate%': round(st_f['win_rate'], 1),
            'Total PnL ($)': round(st_f['pnl_usd'], 0),
            'PF': round(st_f['pf'], 2),
            'Expectancy ($)': round(st_f['exp_usd'], 1),
            'MaxDD ($)': round(st_f['max_dd'], 0)
        })
    print(pd.DataFrame(f_rows).to_string(index=False), flush=True)

    # =========================================================================
    # 5. PARAMETER SENSITIVITY MATRIX
    # =========================================================================
    print("\n" + "="*80, flush=True)
    print("      5. PARAMETER SENSITIVITY & CONFIRMATION METHOD COMPARISON", flush=True)
    print("="*80, flush=True)

    sens_rows = []
    confirmations = ["MSS Only", "iFVG Only", "MSS OR iFVG"]
    band_choices = ["SD1", "SD2", "SD3"]
    tp_sl_pairs = [(20.0, 30.0), (15.0, 30.0), (20.0, 40.0), (25.0, 50.0)]

    for c_choice in confirmations:
        for b_choice in band_choices:
            for sl, tp in tp_sl_pairs:
                df_sim = run_sim_numpy(
                    data, band_choice=b_choice, confirmation=c_choice,
                    stop_points=sl, target_points=tp, friction_pts=0.25
                )
                st_sim = get_stats(df_sim)
                sens_rows.append({
                    'Confirmation': c_choice,
                    'VWAP Band': b_choice,
                    'SL (pts)': sl,
                    'TP (pts)': tp,
                    'R:R': f"1:{tp/sl:.1f}",
                    'Trades': st_sim['trades'],
                    'WinRate%': round(st_sim['win_rate'], 1),
                    'Total PnL ($)': round(st_sim['pnl_usd'], 0),
                    'PF': round(st_sim['pf'], 2),
                    'Exp ($)': round(st_sim['exp_usd'], 1),
                    'MaxDD ($)': round(st_sim['max_dd'], 0)
                })

    df_sens = pd.DataFrame(sens_rows)
    df_sens.to_csv('parameter_sensitivity.csv', index=False)

    print("\nTop 10 Performing Configurations by Total PnL ($):", flush=True)
    print(df_sens.sort_values('Total PnL ($)', ascending=False).head(10).to_string(index=False), flush=True)

    print("\n" + "="*80, flush=True)
    print(f"ALL SIMULATIONS FINISHED IN {time.time() - t_start:.2f} SECONDS!", flush=True)
    print("="*80, flush=True)
