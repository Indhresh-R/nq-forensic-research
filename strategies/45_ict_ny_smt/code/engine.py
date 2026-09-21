"""Look-ahead-free signal generation and trade simulation."""
from __future__ import annotations

import numpy as np
import pandas as pd

from config import BacktestConfig
from market_data import resample_7h, resample_daily, resample_fixed
from indexes import FVGIndex, SwingIndex, smt_from_index
from structure import (
    CandleStore,
    classify_c2_vs_c1,
    confirmed_swings,
    detect_fvgs,
    equal_liquidity_levels,
    find_engulfing_protected,
    nearest_swing_target,
    nearest_unmitigated_fvg,
)


def build_store(df: pd.DataFrame, cfg: BacktestConfig, label: str = "") -> CandleStore:
    print(f"Building multi-TF candles ({label})...")
    daily = resample_daily(df, cfg.session_anchor_hour)
    h7 = resample_7h(df, cfg)
    h4 = resample_fixed(df, 240, cfg.session_anchor_hour)
    h1 = resample_fixed(df, 60, cfg.session_anchor_hour)
    m15 = resample_fixed(df, 15, cfg.session_anchor_hour)
    m5 = resample_fixed(df, cfg.smt_confirm_minutes, cfg.session_anchor_hour)
    print(
        f"  daily={len(daily)} 7H={len(h7)} 4H={len(h4)} 1H={len(h1)} "
        f"15m={len(m15)} {cfg.smt_confirm_minutes}m={len(m5)}"
    )
    return CandleStore(daily=daily, h7=h7, h4=h4, h1=h1, m15=m15, m5=m5, m1=df)


def _swing_pack(ohlc: pd.DataFrame, lookback: int) -> tuple[list, list]:
    if ohlc is None or ohlc.empty:
        return [], []
    return confirmed_swings(
        ohlc["high"].to_numpy(float),
        ohlc["low"].to_numpy(float),
        ohlc["close_ts"].to_numpy(),
        lookback,
    )


def _ny_mins(h: int, m: int) -> int:
    return h * 60 + m


def daily_bias_and_fvg_state(
    daily: pd.DataFrame,
    daily_fvgs: pd.DataFrame,
    asof_ts,
    ts_ns: np.ndarray,
    opens: np.ndarray,
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
) -> dict:
    d = daily[daily["close_ts"] <= asof_ts].reset_index(drop=True)
    if len(d) < 2:
        return {"ok": False, "reason": "insufficient_daily"}
    c1, c2 = d.iloc[-2], d.iloc[-1]
    cls = classify_c2_vs_c1(c1, c2)
    if cls["direction"] == 0:
        bias = 1 if float(c2["close"]) >= float(c2["open"]) else -1
        cls_kind = "fallback_close"
    else:
        bias = int(cls["direction"])
        cls_kind = cls["kind"]

    ref = float(c2["close"])
    fvg = nearest_unmitigated_fvg(daily_fvgs, bias, asof_ts, ref, d)

    fvg_state = "no_fvg"
    if fvg is not None:
        formed = np.datetime64(pd.Timestamp(fvg["formed_at"]).to_datetime64())
        asof = np.datetime64(pd.Timestamp(asof_ts).to_datetime64())
        i0 = int(np.searchsorted(ts_ns, formed, side="right"))
        i1 = int(np.searchsorted(ts_ns, asof, side="right"))
        if i1 - i0 > 20000:
            i0 = i1 - 20000
        if i1 > i0:
            h = highs[i0:i1]
            l = lows[i0:i1]
            c = closes[i0:i1]
            touch = (l <= fvg["top"]) & (h >= fvg["bottom"])
            if not touch.any():
                fvg_state = "untested"
            else:
                t0 = int(np.flatnonzero(touch)[0])
                after_c = c[t0:]
                if bias > 0:
                    res_m = after_c > fvg["top"]
                    ag_m = after_c < fvg["bottom"]
                else:
                    res_m = after_c < fvg["bottom"]
                    ag_m = after_c > fvg["top"]
                resumed = bool(res_m.any())
                against = bool(ag_m.any())
                if resumed and against:
                    fvg_state = (
                        "confirmed"
                        if int(np.flatnonzero(res_m)[-1]) > int(np.flatnonzero(ag_m)[-1])
                        else "unconfirmed"
                    )
                elif resumed:
                    fvg_state = "confirmed"
                elif against:
                    fvg_state = "unconfirmed"
                else:
                    fvg_state = "touched_pending"
        else:
            fvg_state = "untested"

    return {
        "ok": True,
        "bias": bias,
        "daily_kind": cls_kind,
        "fvg": fvg,
        "fvg_state": fvg_state,
    }


def seven_h_ny_ok(h7: pd.DataFrame, bias: int, asof_ts) -> dict:
    """C1=18:00-01:00 (bin0), C2=01:00-08:00 (bin1). Both closed before 08:30."""
    avail = h7[h7["close_ts"] <= asof_ts]
    if avail.empty:
        return {"ok": False, "reason": "no_7h"}
    for sd in sorted(avail["session_date"].unique(), reverse=True)[:8]:
        g = avail[avail["session_date"] == sd]
        b0 = g[g["bin"] == 0]
        b1 = g[g["bin"] == 1]
        if len(b0) and len(b1):
            cls = classify_c2_vs_c1(b0.iloc[-1], b1.iloc[-1])
            cont_ok = cls["kind"] == "continuation" and cls["direction"] == bias
            return {
                "ok": bool(cont_ok),
                "reason": "cont_match" if cont_ok else "no_cont",
                "session_date": sd,
            }
    return {"ok": False, "reason": "incomplete_bins"}


def _in_fvg_zone(bar: pd.Series, fvgs: pd.DataFrame, bias: int, asof) -> bool:
    if fvgs is None or fvgs.empty:
        return False
    sub = fvgs[(fvgs["direction"] == bias) & (fvgs["formed_at"] <= asof)]
    for _, f in sub.iterrows():
        if float(bar["low"]) <= float(f["top"]) and float(bar["high"]) >= float(f["bottom"]):
            return True
    return False


def simulate_trade(
    day: pd.DataFrame,
    direction: int,
    entry_price: float,
    entry_ts,
    sl: float,
    tp: float,
    cfg: BacktestConfig,
    partial: bool = False,
    runner_r: float = 2.0,
) -> dict:
    risk = abs(entry_price - sl)
    if risk <= 0:
        return {"ok": False, "reason": "zero_risk"}

    slip = cfg.slippage_ticks * cfg.tick
    fill = entry_price + direction * slip
    sl_use = sl
    commission = 2 * cfg.commission_per_side
    remaining = 1.0
    realized = 0.0
    be = False
    exit_price = exit_ts = exit_reason = None
    force_min = _ny_mins(*cfg.force_flat)

    # numpy path for speed
    ts = day["ts"].to_numpy()
    highs = day["high"].to_numpy(float)
    lows = day["low"].to_numpy(float)
    closes = day["close"].to_numpy(float)
    ny = day["ny_min"].to_numpy(int)
    entry_ts = pd.Timestamp(entry_ts)

    for i in range(len(day)):
        if pd.Timestamp(ts[i]) <= entry_ts:
            continue
        h, l, c = highs[i], lows[i], closes[i]
        if direction > 0:
            hit_sl = l <= sl_use
            hit_tp = h >= tp
        else:
            hit_sl = h >= sl_use
            hit_tp = l <= tp

        if hit_sl and hit_tp:
            exit_price = sl_use - direction * slip
            exit_ts = ts[i]
            exit_reason = "SL_samebar_priority"
            realized += remaining * direction * (exit_price - fill)
            remaining = 0.0
            break
        if hit_sl:
            exit_price = sl_use - direction * slip
            exit_ts = ts[i]
            exit_reason = "SL"
            realized += remaining * direction * (exit_price - fill)
            remaining = 0.0
            break
        if hit_tp:
            if partial and remaining > 0.5 and not be:
                px = tp - direction * slip
                realized += 0.5 * direction * (px - fill)
                remaining = 0.5
                sl_use = fill
                be = True
                tp = fill + direction * runner_r * risk
                continue
            exit_price = tp - direction * slip
            exit_ts = ts[i]
            exit_reason = "TP"
            realized += remaining * direction * (exit_price - fill)
            remaining = 0.0
            break
        if int(ny[i]) >= force_min:
            exit_price = c - direction * slip
            exit_ts = ts[i]
            exit_reason = "FORCE_FLAT"
            realized += remaining * direction * (exit_price - fill)
            remaining = 0.0
            break

    if remaining > 0:
        exit_price = float(closes[-1]) - direction * slip
        exit_ts = ts[-1]
        exit_reason = "EOD_DATA"
        realized += remaining * direction * (exit_price - fill)

    return {
        "ok": True,
        "entry_fill": fill,
        "exit_price": float(exit_price),
        "exit_ts": exit_ts,
        "exit_reason": exit_reason,
        "pnl_pts": float(realized),
        "pnl_nq": float(realized) * cfg.point_value_nq - commission,
        "pnl_mnq": float(realized) * cfg.point_value_mnq - commission,
        "r_mult": float(realized) / risk,
        "risk_pts": risk,
        "sl_final": sl_use,
        "tp_final": tp,
    }


def _liquidity_tp(m15: pd.DataFrame, entry: float, direction: int, asof, cfg: BacktestConfig):
    sub = m15[m15["close_ts"] <= asof]
    sh, sl = _swing_pack(sub, cfg.swing_lookback)
    tol = cfg.equal_liq_tol_ticks * cfg.tick
    eq = equal_liquidity_levels(
        [{"price": s["price"], "confirmed_at": s["confirmed_at"]} for s in (sh if direction < 0 else sl)],
        tol,
        asof,
        direction,
        entry,
    )
    sw = nearest_swing_target(
        [{"price": s["price"], "confirmed_at": s["confirmed_at"], "kind": "high"} for s in sh]
        + [{"price": s["price"], "confirmed_at": s["confirmed_at"], "kind": "low"} for s in sl],
        asof,
        direction,
        entry,
    )
    cands = [x for x in (eq, sw) if x is not None]
    if not cands:
        return None, "none"
    return (min(cands) if direction > 0 else max(cands)), "liquidity"


def scan_setups(
    nq: pd.DataFrame,
    nq_store: CandleStore,
    es_store: CandleStore,
    cfg: BacktestConfig,
) -> tuple[pd.DataFrame, dict]:
    """Single causal scan producing setup rows with filter flags and SL anchors."""
    entry_lo = _ny_mins(*cfg.entry_start)
    entry_hi = _ny_mins(*cfg.entry_end)
    buf = cfg.sl_buffer_ticks * cfg.tick

    daily_fvgs = detect_fvgs(nq_store.daily)
    h1_fvgs_df = detect_fvgs(nq_store.h1)
    h1_fvg_idx = FVGIndex(h1_fvgs_df)

    m5_nq_sh, m5_nq_sl = _swing_pack(nq_store.m5, cfg.swing_lookback)
    m5_es_sh, m5_es_sl = _swing_pack(es_store.m5, cfg.swing_lookback)
    h1_nq_sh, h1_nq_sl = _swing_pack(nq_store.h1, cfg.swing_lookback)
    h1_es_sh, h1_es_sl = _swing_pack(es_store.h1, cfg.swing_lookback)

    idx_m5_nq_h = SwingIndex(m5_nq_sh)
    idx_m5_nq_l = SwingIndex(m5_nq_sl)
    idx_m5_es_h = SwingIndex(m5_es_sh)
    idx_m5_es_l = SwingIndex(m5_es_sl)
    idx_h1_nq_h = SwingIndex(h1_nq_sh)
    idx_h1_nq_l = SwingIndex(h1_nq_sl)
    idx_h1_es_h = SwingIndex(h1_es_sh)
    idx_h1_es_l = SwingIndex(h1_es_sl)

    fvg_state_counts: dict[str, int] = {}
    setups: list[dict] = []
    nq_by_sd = {sd: g.reset_index(drop=True) for sd, g in nq.groupby("session_date", sort=False)}
    m5_by_sd = {sd: g for sd, g in nq_store.m5.groupby("session_date", sort=False)}

    ts_ns = nq["ts"].to_numpy(dtype="datetime64[ns]")
    highs_1m = nq["high"].to_numpy(float)
    lows_1m = nq["low"].to_numpy(float)
    closes_1m = nq["close"].to_numpy(float)
    opens_1m = nq["open"].to_numpy(float)

    h1 = nq_store.h1.reset_index(drop=True)
    h1_start = h1["start_ts"].to_numpy(dtype="datetime64[ns]")
    h1_close = h1["close_ts"].to_numpy(dtype="datetime64[ns]")

    n_sess = len(nq_by_sd)
    for si, (sd, day) in enumerate(nq_by_sd.items()):
        if si % 500 == 0:
            print(f"  scan session {si}/{n_sess} setups={len(setups)}", flush=True)
        window = day[(day["ny_min"] >= entry_lo) & (day["ny_min"] < entry_hi)]
        if window.empty:
            continue
        pre = day[day["ny_min"] < entry_lo]
        asof0 = (
            pd.Timestamp(pre["ts"].iloc[-1]) + pd.Timedelta(minutes=1)
            if len(pre)
            else pd.Timestamp(window["ts"].iloc[0])
        )

        daily_info = daily_bias_and_fvg_state(
            nq_store.daily, daily_fvgs, asof0, ts_ns, opens_1m, highs_1m, lows_1m, closes_1m
        )
        if not daily_info["ok"]:
            continue
        bias = int(daily_info["bias"])
        fvg_state = daily_info["fvg_state"]
        fvg_state_counts[fvg_state] = fvg_state_counts.get(fvg_state, 0) + 1

        pass_daily_confirmed = fvg_state == "confirmed"
        need_htf = fvg_state != "confirmed"

        h7 = seven_h_ny_ok(nq_store.h7, bias, asof0)
        pass_7h = bool(h7["ok"])
        h7_state = h7.get("reason", "")

        prot = find_engulfing_protected(nq_store.h1, bias, asof0)
        if prot is None:
            prot = find_engulfing_protected(nq_store.h4, bias, asof0)
        if prot is None:
            continue

        h1_closed = h1[h1["close_ts"] <= asof0]
        htf_c1c2 = False
        if len(h1_closed) >= 2:
            cls = classify_c2_vs_c1(h1_closed.iloc[-2], h1_closed.iloc[-1])
            htf_c1c2 = cls["kind"] in ("continuation", "reversal") and cls["direction"] == bias
        if len(h1_closed) < 1:
            continue
        c1_close = pd.Timestamp(h1_closed.iloc[-1]["close_ts"])

        m5_day = m5_by_sd.get(sd)
        if m5_day is None or m5_day.empty:
            continue
        invalidated = False

        for _, m5 in m5_day.iterrows():
            if invalidated:
                break
            close_ts = pd.Timestamp(m5["close_ts"])
            decision_ts = close_ts - pd.Timedelta(minutes=1)
            dec_ny = decision_ts.hour * 60 + decision_ts.minute
            if dec_ny < entry_lo or dec_ny >= entry_hi:
                continue
            if close_ts <= c1_close:
                continue

            # Live 1H C2: started <= decision < close
            live = h1[(h1["start_ts"] <= decision_ts) & (h1["close_ts"] > decision_ts)]
            if live.empty:
                continue

            path_so_far = day[day["ts"] <= decision_ts]
            if bias > 0 and (path_so_far["low"].to_numpy() < prot["level"]).any():
                invalidated = True
                break
            if bias < 0 and (path_so_far["high"].to_numpy() > prot["level"]).any():
                invalidated = True
                break

            in_fvg = h1_fvg_idx.overlaps(
                decision_ts, bias, float(m5["low"]), float(m5["high"])
            )

            smt_1h = smt_from_index(
                idx_h1_nq_h, idx_h1_nq_l, idx_h1_es_h, idx_h1_es_l, decision_ts, bias
            )
            smt_5m = smt_from_index(
                idx_m5_nq_h, idx_m5_nq_l, idx_m5_es_h, idx_m5_es_l, close_ts, bias
            )
            smt_ok = smt_1h is not None and smt_5m is not None and in_fvg

            last_sw = (idx_m5_nq_l if bias > 0 else idx_m5_nq_h).last_one(close_ts)
            mss = False
            if last_sw is not None:
                if bias > 0:
                    mss = float(m5["close"]) > last_sw and float(m5["low"]) <= last_sw
                else:
                    mss = float(m5["close"]) < last_sw and float(m5["high"]) >= last_sw
            fvg_react = in_fvg and (
                (bias > 0 and float(m5["close"]) > float(m5["open"]))
                or (bias < 0 and float(m5["close"]) < float(m5["open"]))
            )
            nosmt_ok = mss or fvg_react
            if not (smt_ok or nosmt_ok):
                continue

            entry_price = float(m5["close"])
            entry_ts = decision_ts
            sw_a = smt_5m["nq_swing"] if smt_5m is not None else last_sw
            if sw_a is None:
                continue
            sl_a = sw_a - buf if bias > 0 else sw_a + buf

            so_far = day[(day["ts"] >= live.iloc[0]["start_ts"]) & (day["ts"] <= decision_ts)]
            if so_far.empty:
                continue
            extreme = float(so_far["low"].min()) if bias > 0 else float(so_far["high"].max())
            sl_b = extreme - buf if bias > 0 else extreme + buf
            sl_c = prot["level"] - buf if bias > 0 else prot["level"] + buf

            setups.append(
                {
                    "session_date": sd,
                    "bias": bias,
                    "daily_fvg_state": fvg_state,
                    "pass_daily_confirmed": pass_daily_confirmed,
                    "need_htf": need_htf,
                    "htf_c1c2": htf_c1c2,
                    "pass_7h": pass_7h,
                    "h7_state": h7_state,
                    "smt_ok": smt_ok,
                    "nosmt_ok": nosmt_ok,
                    "entry_ts": entry_ts,
                    "entry_price": entry_price,
                    "sl_a": sl_a,
                    "sl_b": sl_b,
                    "sl_c": sl_c,
                    "protected": prot["level"],
                    "weekday": pd.Timestamp(str(sd)).weekday(),
                    "entry_hour": int(pd.Timestamp(entry_ts).hour),
                }
            )

    return pd.DataFrame(setups), fvg_state_counts


def materialize_variant(
    setups: pd.DataFrame,
    nq: pd.DataFrame,
    nq_store: CandleStore,
    cfg: BacktestConfig,
    variant: str,
    sl_mode: str,
    tp_mode: str,
    m15_swings: tuple[list, list] | None = None,
) -> pd.DataFrame:
    if setups is None or setups.empty:
        return pd.DataFrame()

    s = setups
    if variant == "A":
        s = s[s["smt_ok"]]
        s = s[s["pass_7h"]]
        s = s[s["pass_daily_confirmed"] | ((s["need_htf"]) & s["htf_c1c2"])]
    elif variant == "B":
        s = s[s["nosmt_ok"]]
        s = s[s["pass_7h"]]
        s = s[s["pass_daily_confirmed"] | ((s["need_htf"]) & s["htf_c1c2"])]
    elif variant == "C":
        s = s[s["smt_ok"]]
        s = s[s["pass_7h"]]
    elif variant == "D":
        s = s[s["smt_ok"]]
        s = s[s["pass_daily_confirmed"] | ((s["need_htf"]) & s["htf_c1c2"])]
    else:
        raise ValueError(variant)

    if s.empty:
        return pd.DataFrame()

    s = s.sort_values("entry_ts")
    s = s.groupby("session_date", sort=False).head(cfg.max_trades_per_session)

    nq_by_sd = {sd: g.reset_index(drop=True) for sd, g in nq.groupby("session_date", sort=False)}
    if m15_swings is None:
        m15_swings = _swing_pack(nq_store.m15, cfg.swing_lookback)
    sh15, sl15 = m15_swings
    tol = cfg.equal_liq_tol_ticks * cfg.tick

    trades = []
    for row in s.itertuples(index=False):
        day = nq_by_sd.get(row.session_date)
        if day is None:
            continue
        sl = {"A": row.sl_a, "B": row.sl_b, "C": row.sl_c}[sl_mode]
        entry = float(row.entry_price)
        bias = int(row.bias)
        risk = abs(entry - sl)
        if risk <= 0 or risk > cfg.max_risk_points:
            continue
        if bias > 0 and sl >= entry:
            continue
        if bias < 0 and sl <= entry:
            continue

        asof = pd.Timestamp(row.entry_ts)
        if tp_mode == "liquidity":
            eq = equal_liquidity_levels(
                [
                    {"price": x["price"], "confirmed_at": x["confirmed_at"]}
                    for x in (sh15 if bias < 0 else sl15)
                    if pd.Timestamp(x["confirmed_at"]) <= asof
                ][-40:],
                tol,
                asof,
                bias,
                entry,
            )
            sw = nearest_swing_target(
                [
                    {"price": x["price"], "confirmed_at": x["confirmed_at"], "kind": "high"}
                    for x in sh15
                    if pd.Timestamp(x["confirmed_at"]) <= asof
                ][-40:]
                + [
                    {"price": x["price"], "confirmed_at": x["confirmed_at"], "kind": "low"}
                    for x in sl15
                    if pd.Timestamp(x["confirmed_at"]) <= asof
                ][-40:],
                asof,
                bias,
                entry,
            )
            cands = [x for x in (eq, sw) if x is not None]
            if not cands:
                tp = entry + bias * 2.0 * risk
                tp_used = "liquidity_fallback_2R"
            else:
                tp = min(cands) if bias > 0 else max(cands)
                tp_used = "liquidity"
        else:
            r = float(tp_mode.replace("R", ""))
            tp = entry + bias * r * risk
            tp_used = tp_mode

        sim = simulate_trade(
            day,
            bias,
            entry,
            row.entry_ts,
            float(sl),
            float(tp),
            cfg,
            partial=cfg.partial_tp,
            runner_r=cfg.runner_r,
        )
        if not sim["ok"]:
            continue
        trades.append(
            {
                "session_date": row.session_date,
                "variant": variant,
                "sl_mode": sl_mode,
                "tp_mode": tp_mode,
                "bias": bias,
                "daily_fvg_state": row.daily_fvg_state,
                "h7_state": row.h7_state,
                "entry_ts": row.entry_ts,
                "entry_price": entry,
                "sl": float(sl),
                "tp": float(tp),
                "tp_used": tp_used,
                "exit_ts": sim["exit_ts"],
                "exit_price": sim["exit_price"],
                "exit_reason": sim["exit_reason"],
                "r_mult": sim["r_mult"],
                "pnl_pts": sim["pnl_pts"],
                "pnl_nq": sim["pnl_nq"],
                "pnl_mnq": sim["pnl_mnq"],
                "risk_pts": sim["risk_pts"],
                "weekday": row.weekday,
                "entry_hour": row.entry_hour,
            }
        )
    return pd.DataFrame(trades)


def random_baseline(
    nq: pd.DataFrame,
    cfg: BacktestConfig,
    sl_mode: str,
    tp_mode: str,
    n_runs: int,
) -> pd.DataFrame:
    rng = np.random.default_rng(cfg.random_seed)
    entry_lo = _ny_mins(*cfg.entry_start)
    entry_hi = _ny_mins(*cfg.entry_end)
    nq_by_sd = {sd: g.reset_index(drop=True) for sd, g in nq.groupby("session_date", sort=False)}
    sessions = [sd for sd, g in nq_by_sd.items() if ((g["ny_min"] >= entry_lo) & (g["ny_min"] < entry_hi)).any()]

    rows = []
    for run in range(n_runs):
        pnls, rs = [], []
        # Sample ~400 random session entries per run for speed
        sample_sd = rng.choice(sessions, size=min(400, len(sessions)), replace=False)
        for sd in sample_sd:
            day = nq_by_sd[sd]
            window = day[(day["ny_min"] >= entry_lo) & (day["ny_min"] < entry_hi)]
            if len(window) < 5:
                continue
            bar = window.iloc[int(rng.integers(0, len(window)))]
            direction = 1 if rng.random() < 0.5 else -1
            entry_price = float(bar["close"])
            entry_ts = bar["ts"]
            hist = day[day["ts"] <= entry_ts].tail(30)
            if hist.empty:
                continue
            if sl_mode == "A":
                risk = min(max(float(hist["high"].max() - hist["low"].min()) * 0.35, 3.0), cfg.max_risk_points)
                sl = entry_price - direction * risk
            elif sl_mode == "B":
                sl = float(hist["low"].min()) - cfg.tick if direction > 0 else float(hist["high"].max()) + cfg.tick
                risk = abs(entry_price - sl)
            else:
                sl = float(hist["low"].min()) - 2 * cfg.tick if direction > 0 else float(hist["high"].max()) + 2 * cfg.tick
                risk = abs(entry_price - sl)
            if risk <= 0 or risk > cfg.max_risk_points:
                continue
            if tp_mode == "liquidity":
                tp = entry_price + direction * 2.0 * risk
            else:
                r = float(tp_mode.replace("R", ""))
                tp = entry_price + direction * r * risk
            sim = simulate_trade(day, direction, entry_price, entry_ts, sl, tp, cfg)
            if sim["ok"]:
                pnls.append(sim["pnl_nq"])
                rs.append(sim["r_mult"])
        rows.append(
            {
                "run": run,
                "n_trades": len(pnls),
                "total_pnl_nq": float(np.sum(pnls)) if pnls else 0.0,
                "expectancy_r": float(np.mean(rs)) if rs else 0.0,
                "expectancy_usd": float(np.mean(pnls)) if pnls else 0.0,
            }
        )
    return pd.DataFrame(rows)
