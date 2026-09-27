"""Strategy 29 Phase B/C — oracle + causal opposite dip/recovery scalps."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from common.nq_session import SESSION_START, load_nq
from common.paths import ROOT
from common.splits import IS_YEARS, OOS_YEARS, VAL_YEARS

ART = ROOT / "artifacts" / "29_830_900_hodlod_opposite"

W_LO, W_HI = 8 * 60 + 30, 9 * 60
RTH0, RTH1 = 9 * 60 + 30, 16 * 60
SEARCH_END = 10 * 60 + 30  # 10:30
COST = 1.0
DIP_PTS = (5.0, 10.0)
FIXED_TARGETS = (20.0, 25.0, 30.0)
HOLD_H = 30


def split_of(year: int) -> str:
    if year in IS_YEARS:
        return "Discovery"
    if year in VAL_YEARS:
        return "Validation"
    if year in OOS_YEARS:
        return "OOS"
    return "OTHER"


def path_exit(side: float, entry: float, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray,
              stop: float, target: float) -> tuple[float, str]:
    if not np.isfinite(entry) or side == 0:
        return float("nan"), "invalid"
    for i in range(len(highs)):
        hi, lo = highs[i], lows[i]
        if not (np.isfinite(hi) and np.isfinite(lo)):
            continue
        if side > 0:
            hit_stop = lo <= stop
            hit_tgt = hi >= target
        else:
            hit_stop = hi >= stop
            hit_tgt = lo <= target
        if hit_stop and hit_tgt:
            return (stop - entry) * side - COST, "stop_samebar"
        if hit_stop:
            return (stop - entry) * side - COST, "stop"
        if hit_tgt:
            return (target - entry) * side - COST, "target"
    last = closes[-1] if len(closes) else np.nan
    if not np.isfinite(last):
        return float("nan"), "invalid"
    return side * (last - entry) - COST, "time"


def find_entry(side: int, o930: float, bars: pd.DataFrame, dip_pts: float) -> tuple[int, float, float] | None:
    """
    Returns (entry_iloc_in_bars, entry_price, stop_price) or None.
    bars indexed 0.. with ny_min ascending from >= 09:30.
    """
    if len(bars) < 3 or not np.isfinite(o930):
        return None
    highs = bars["high"].to_numpy(np.float64)
    lows = bars["low"].to_numpy(np.float64)
    closes = bars["close"].to_numpy(np.float64)
    opens = bars["open"].to_numpy(np.float64)
    n = len(bars)
    dip_i = None
    extreme = None
    for i in range(n):
        if side > 0:
            if lows[i] <= o930 - dip_pts:
                dip_i = i
                extreme = float(lows[i])
                break
        else:
            if highs[i] >= o930 + dip_pts:
                dip_i = i
                extreme = float(highs[i])
                break
    if dip_i is None or extreme is None:
        return None
    # continue tracking worse extreme until recovery
    for j in range(dip_i, n):
        if side > 0:
            extreme = min(extreme, float(lows[j]))
            if closes[j] >= o930:
                ent = j + 1
                if ent >= n:
                    return None
                stop = extreme - 1.0
                return ent, float(opens[ent]), stop
        else:
            extreme = max(extreme, float(highs[j]))
            if closes[j] <= o930:
                ent = j + 1
                if ent >= n:
                    return None
                stop = extreme + 1.0
                return ent, float(opens[ent]), stop
    return None


def oracle_side(is_hod: bool, is_lod: bool) -> int:
    if is_hod and not is_lod:
        return -1
    if is_lod and not is_hod:
        return 1
    return 0


def causal_sides(w: pd.DataFrame, overnight: pd.DataFrame) -> dict[str, int]:
    wh = float(w["high"].max())
    wl = float(w["low"].min())
    w_open = float(w.iloc[0]["open"])
    out = {"fade_extent": 0, "fade_last_touch": 0, "fade_raid": 0}

    up = wh - w_open
    dn = w_open - wl
    if up > dn + 1e-12:
        out["fade_extent"] = -1
    elif dn > up + 1e-12:
        out["fade_extent"] = 1

    # last touch of hi vs lo
    last_hi = int(w.loc[w["high"] >= wh - 1e-12, "ny_min"].max())
    last_lo = int(w.loc[w["low"] <= wl + 1e-12, "ny_min"].max())
    if last_hi > last_lo:
        out["fade_last_touch"] = -1
    elif last_lo > last_hi:
        out["fade_last_touch"] = 1

    if len(overnight) >= 10:
        oh = float(overnight["high"].max())
        ol = float(overnight["low"].min())
        raid_hi = wh >= oh - 1e-12
        raid_lo = wl <= ol + 1e-12
        if raid_hi and not raid_lo:
            out["fade_raid"] = -1
        elif raid_lo and not raid_hi:
            out["fade_raid"] = 1
    return out


def simulate_day(
    g: pd.DataFrame,
    side: int,
    wh: float,
    wl: float,
    dip_pts: float,
    target_mode: str,
    target_pts: float | None,
) -> dict | None:
    if side == 0:
        return None
    rth = g[(g["ny_min"] >= RTH0) & (g["ny_min"] < SEARCH_END)].sort_values("ny_min").reset_index(drop=True)
    if len(rth) < 5:
        return None
    o930 = float(rth.iloc[0]["open"])
    found = find_entry(side, o930, rth, dip_pts)
    if found is None:
        return {"triggered": False}
    ent_i, entry, stop = found
    # hold path: next HOLD_H bars from entry within session RTH
    full = g[(g["ny_min"] >= RTH0) & (g["ny_min"] < RTH1)].sort_values("ny_min").reset_index(drop=True)
    # map entry timestamp
    ent_ny = int(rth.iloc[ent_i]["ny_min"])
    # entry bar in full is the bar at ent_ny
    pos = full.index[full["ny_min"] == ent_ny]
    if len(pos) == 0:
        return {"triggered": False}
    p0 = int(pos[0])
    p1 = min(p0 + HOLD_H, len(full))
    if p1 <= p0:
        return {"triggered": False}
    path = full.iloc[p0:p1]
    if target_mode == "fixed":
        assert target_pts is not None
        tgt = entry + side * target_pts
    else:
        # opposite window extreme
        tgt = wh if side > 0 else wl
        # if target already wrong side of entry, skip
        if side > 0 and tgt <= entry:
            return {"triggered": False}
        if side < 0 and tgt >= entry:
            return {"triggered": False}
    pnl, kind = path_exit(
        float(side),
        entry,
        path["high"].to_numpy(np.float64),
        path["low"].to_numpy(np.float64),
        path["close"].to_numpy(np.float64),
        stop,
        float(tgt),
    )
    if not np.isfinite(pnl):
        return {"triggered": False}
    return {
        "triggered": True,
        "pnl": pnl,
        "kind": kind,
        "entry": entry,
        "stop": stop,
        "target": float(tgt),
        "side": side,
        "stop_dist": abs(entry - stop),
        "tgt_dist": abs(float(tgt) - entry),
    }


def main() -> None:
    ART.mkdir(parents=True, exist_ok=True)
    nq = load_nq()
    # keep evening through RTH for overnight raid
    m = ((nq["ny_min"] >= SESSION_START) | (nq["ny_min"] < RTH1))
    df = nq.loc[m].copy()

    trade_rows = []
    for sess, g0 in df.groupby("session_date", sort=False):
        g = g0.sort_values("ny_min")
        year = int(g["year"].iloc[0])
        split = split_of(year)
        w = g[(g["ny_min"] >= W_LO) & (g["ny_min"] < W_HI)]
        day = g[(g["ny_min"] >= W_LO) & (g["ny_min"] < RTH1)]
        if len(w) < 20 or len(day) < 50:
            continue
        wh = float(w["high"].max())
        wl = float(w["low"].min())
        day_hi = float(day["high"].max())
        day_lo = float(day["low"].min())
        is_hod = abs(wh - day_hi) < 1e-8
        is_lod = abs(wl - day_lo) < 1e-8
        o_side = oracle_side(is_hod, is_lod)

        # overnight = prior evening after 18:00 roll through 08:29
        overnight = g[(g["ny_min"] >= SESSION_START) | (g["ny_min"] < W_LO)]
        c_sides = causal_sides(w, overnight)

        setups = [("oracle", o_side)] + [(k, v) for k, v in c_sides.items()]

        # use RTH+search portion of day frame with ny_min for simulate
        g_day = day
        for setup, side in setups:
            if side == 0:
                continue
            for dip in DIP_PTS:
                for tgt in FIXED_TARGETS:
                    sim = simulate_day(g_day, side, wh, wl, dip, "fixed", tgt)
                    if sim is None or not sim.get("triggered"):
                        trade_rows.append(
                            {
                                "session_date": str(sess),
                                "split": split,
                                "year": year,
                                "setup": setup,
                                "dip": dip,
                                "target_mode": "fixed",
                                "target": tgt,
                                "triggered": False,
                                "side": side,
                                "is_hod": is_hod,
                                "is_lod": is_lod,
                            }
                        )
                    else:
                        trade_rows.append(
                            {
                                "session_date": str(sess),
                                "split": split,
                                "year": year,
                                "setup": setup,
                                "dip": dip,
                                "target_mode": "fixed",
                                "target": tgt,
                                "triggered": True,
                                "side": side,
                                "pnl": sim["pnl"],
                                "kind": sim["kind"],
                                "stop_dist": sim["stop_dist"],
                                "tgt_dist": sim["tgt_dist"],
                                "is_hod": is_hod,
                                "is_lod": is_lod,
                            }
                        )
                # opposite-side range target
                sim = simulate_day(g_day, side, wh, wl, dip, "opposite", None)
                if sim is None or not sim.get("triggered"):
                    trade_rows.append(
                        {
                            "session_date": str(sess),
                            "split": split,
                            "year": year,
                            "setup": setup,
                            "dip": dip,
                            "target_mode": "opposite",
                            "target": np.nan,
                            "triggered": False,
                            "side": side,
                            "is_hod": is_hod,
                            "is_lod": is_lod,
                        }
                    )
                else:
                    trade_rows.append(
                        {
                            "session_date": str(sess),
                            "split": split,
                            "year": year,
                            "setup": setup,
                            "dip": dip,
                            "target_mode": "opposite",
                            "target": sim["tgt_dist"],
                            "triggered": True,
                            "side": side,
                            "pnl": sim["pnl"],
                            "kind": sim["kind"],
                            "stop_dist": sim["stop_dist"],
                            "tgt_dist": sim["tgt_dist"],
                            "is_hod": is_hod,
                            "is_lod": is_lod,
                        }
                    )

    trades = pd.DataFrame(trade_rows)
    trades.to_parquet(ART / "phase_bc_trades.parquet", index=False)

    # aggregate triggered only for E
    trig = trades[trades["triggered"] == True]  # noqa: E712
    rows = []
    for keys, g in trig.groupby(["setup", "dip", "target_mode", "target", "split"], dropna=False):
        setup, dip, tmode, tgt, split = keys
        x = g["pnl"].to_numpy(np.float64)
        rows.append(
            {
                "setup": setup,
                "dip": dip,
                "target_mode": tmode,
                "target": tgt,
                "split": split,
                "n": int(len(x)),
                "win": float(np.mean(x > 0)),
                "E_net": float(np.mean(x)),
                "median": float(np.median(x)),
                "target_hit": float(np.mean(g["kind"] == "target")),
                "stop_hit": float(np.mean(g["kind"].isin(["stop", "stop_samebar"]))),
                "time_exit": float(np.mean(g["kind"] == "time")),
            }
        )
    # also trigger rates
    rates = (
        trades.groupby(["setup", "dip", "target_mode", "target", "split"], dropna=False)
        .agg(n_days=("session_date", "nunique"), n_trig=("triggered", "sum"))
        .reset_index()
    )
    rates["trig_rate"] = rates["n_trig"] / rates["n_days"]
    grid = pd.DataFrame(rows)
    grid = grid.merge(rates, on=["setup", "dip", "target_mode", "target", "split"], how="left")
    grid.to_csv(ART / "phase_bc_grid.csv", index=False)

    # survivors: Val+OOS E_net>0, n>=30
    survivors = []
    if len(grid):
        piv = grid.pivot_table(
            index=["setup", "dip", "target_mode", "target"],
            columns="split",
            values="E_net",
            aggfunc="first",
        )
        cnt = grid.pivot_table(
            index=["setup", "dip", "target_mode", "target"],
            columns="split",
            values="n",
            aggfunc="first",
        )
        for idx in piv.index:
            e_v = piv.loc[idx].get("Validation", np.nan)
            e_o = piv.loc[idx].get("OOS", np.nan)
            e_d = piv.loc[idx].get("Discovery", np.nan)
            n_v = cnt.loc[idx].get("Validation", 0) or 0
            n_o = cnt.loc[idx].get("OOS", 0) or 0
            if np.isfinite(e_v) and np.isfinite(e_o) and e_v > 0 and e_o > 0 and n_v >= 30 and n_o >= 30:
                survivors.append(
                    {
                        "setup": idx[0],
                        "dip": idx[1],
                        "target_mode": idx[2],
                        "target": idx[3],
                        "E_Discovery": e_d,
                        "E_Validation": e_v,
                        "E_OOS": e_o,
                        "n_Validation": int(n_v),
                        "n_OOS": int(n_o),
                    }
                )
    surv = pd.DataFrame(survivors)
    surv.to_csv(ART / "phase_bc_survivors.csv", index=False)

    # headline tables
    def head_cell(setup: str, dip: float = 10.0, tmode: str = "fixed", tgt: float = 25.0) -> pd.DataFrame:
        return grid[
            (grid["setup"] == setup)
            & (grid["dip"] == dip)
            & (grid["target_mode"] == tmode)
            & (grid["target"] == tgt)
        ][["split", "n", "trig_rate", "win", "E_net", "target_hit", "stop_hit"]]

    oracle_h = head_cell("oracle")
    raid_h = head_cell("fade_raid")

    causal_surv = [s for s in survivors if s["setup"] != "oracle"]
    oracle_surv = [s for s in survivors if s["setup"] == "oracle"]

    if len(oracle_surv) == 0 and len(causal_surv) == 0:
        klass, label = "C", "NO_EDGE"
    elif len(causal_surv) == 0 and len(oracle_surv) > 0:
        klass, label = "C", "ORACLE_ONLY_NOT_TRADEABLE"
    elif len(causal_surv) > 0:
        klass, label = "B", "CAUSAL_REVIEW"
    else:
        klass, label = "C", "NO_EDGE"

    verdict = {
        "class": klass,
        "label": label,
        "n_survivors_total": len(survivors),
        "n_survivors_oracle": len(oracle_surv),
        "n_survivors_causal": len(causal_surv),
        "survivors": survivors,
        "headline_oracle_dip10_tgt25": oracle_h.to_dict(orient="records"),
        "headline_fade_raid_dip10_tgt25": raid_h.to_dict(orient="records"),
    }
    (ART / "phase_bc_verdict.json").write_text(json.dumps(verdict, indent=2, default=float), encoding="utf-8")

    md = [
        "# Strategy 29 — Phase B/C scalp",
        "",
        f"Verdict: `{klass}` — {label}",
        f"Survivors Val+OOS: total={len(survivors)} oracle={len(oracle_surv)} causal={len(causal_surv)}",
        "",
        "## Headline oracle dip=10 target=25",
        "",
        oracle_h.to_markdown(index=False) if len(oracle_h) else "_none_",
        "",
        "## Headline fade_raid dip=10 target=25",
        "",
        raid_h.to_markdown(index=False) if len(raid_h) else "_none_",
        "",
        "## Survivors",
        "",
        surv.to_markdown(index=False) if len(surv) else "_none_",
        "",
        "## Full grid (top by OOS E_net)",
        "",
    ]
    oos = grid[grid["split"] == "OOS"].sort_values("E_net", ascending=False).head(25)
    md.append(oos.to_markdown(index=False))
    (ART / "phase_bc_report.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps(verdict, indent=2, default=float))


if __name__ == "__main__":
    main()
