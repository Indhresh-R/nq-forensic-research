"""
Strategy 29 Phase E — expanded entry / risk / exit comparison on corrected causal setup.

Setup (frozen from Phase D):
  LOD/HOD of day-so-far in 08:30-09:00, reverse by 09:29 (rev=5 and 10),
  skip if 09:30 open still at extreme.

Compares entries × stops × targets × time-stops. Report all splits; survivors need Val+OOS.
"""
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

W0, W1 = 8 * 60 + 30, 9 * 60
OPEN = 9 * 60 + 30
SEARCH_END = 11 * 60  # allow longer search for slow entries
RTH_END = 16 * 60
COST = 1.0

REV_PTS = (5.0, 10.0)
# entries
IMPULSE = (10.0, 15.0, 20.0)
PB = (5.0, 10.0)
DIP = (5.0, 10.0, 15.0)
# risk / exit
FIXED_STOPS = (10.0, 15.0, 20.0, 25.0)  # used when stop_mode=fixed
RR = (1.0, 1.5, 2.0)  # target = rr * stop_dist
FIXED_TGTS = (15.0, 20.0, 25.0, 30.0, 40.0)  # when tgt_mode=fixed (with structural or fixed stop)
HOLD_HS = (15, 30, 60)


def split_of(year: int) -> str:
    if year in IS_YEARS:
        return "Discovery"
    if year in VAL_YEARS:
        return "Validation"
    if year in OOS_YEARS:
        return "OOS"
    return "OTHER"


def path_exit(side, entry, highs, lows, closes, stop, target):
    if not np.isfinite(entry) or side == 0:
        return np.nan, "invalid"
    for i in range(len(highs)):
        hi, lo = float(highs[i]), float(lows[i])
        if not (np.isfinite(hi) and np.isfinite(lo)):
            continue
        if side > 0:
            hit_stop = lo <= stop
            hit_tgt = hi >= target
        else:
            hit_stop = hi >= stop
            hit_tgt = lo <= target
        if hit_stop and hit_tgt:
            return side * (stop - entry) - COST, "stop_samebar"
        if hit_stop:
            return side * (stop - entry) - COST, "stop"
        if hit_tgt:
            return side * (target - entry) - COST, "target"
    last = float(closes[-1]) if len(closes) else np.nan
    if not np.isfinite(last):
        return np.nan, "invalid"
    return side * (last - entry) - COST, "time"


def classify(g: pd.DataFrame) -> dict | None:
    g = g.sort_values("ny_min")
    w = g[(g["ny_min"] >= W0) & (g["ny_min"] < W1)]
    pre900 = g[g["ny_min"] < W1]
    pre929 = g[g["ny_min"] < OPEN]
    rth_search = g[(g["ny_min"] >= OPEN) & (g["ny_min"] < SEARCH_END)]
    rth_full = g[(g["ny_min"] >= OPEN) & (g["ny_min"] < RTH_END)].reset_index(drop=True)
    if len(w) < 20 or len(pre900) < 30 or len(pre929) < 30 or len(rth_search) < 5:
        return None
    wh, wl = float(w["high"].max()), float(w["low"].min())
    sf_hi, sf_lo = float(pre900["high"].max()), float(pre900["low"].min())
    lod = abs(wl - sf_lo) < 1e-8 and abs(wh - sf_hi) >= 1e-8
    hod = abs(wh - sf_hi) < 1e-8 and abs(wl - sf_lo) >= 1e-8
    if lod == hod:
        return None
    side = 1 if lod else -1
    c929 = float(pre929.iloc[-1]["close"])
    sf_lo_929 = float(pre929["low"].min())
    sf_hi_929 = float(pre929["high"].max())
    o930 = float(rth_search.iloc[0]["open"])
    skip = (side > 0 and o930 <= sf_lo_929 + 1e-8) or (side < 0 and o930 >= sf_hi_929 - 1e-8)
    return {
        "side": side,
        "label": "LOD_SO_FAR" if lod else "HOD_SO_FAR",
        "W_hi": wh,
        "W_lo": wl,
        "c929": c929,
        "o930": o930,
        "skip": skip,
        "rth_search": rth_search.reset_index(drop=True),
        "rth_full": rth_full,
    }


def rev_ok(info, rev):
    if info["side"] > 0:
        return info["c929"] >= info["W_lo"] + rev
    return info["c929"] <= info["W_hi"] - rev


def find_impulse_pb(side, o, bars, impulse, pb):
    highs = bars["high"].to_numpy(np.float64)
    lows = bars["low"].to_numpy(np.float64)
    closes = bars["close"].to_numpy(np.float64)
    opens = bars["open"].to_numpy(np.float64)
    best = o
    seen = False
    pb_ext = None
    for i in range(len(bars)):
        if side > 0:
            best = max(best, highs[i])
            if not seen and best >= o + impulse:
                seen = True
                pb_ext = lows[i]
            if seen:
                pb_ext = min(pb_ext, lows[i])
                if best - pb_ext >= pb and closes[i] >= pb_ext + 1.0:
                    if i + 1 >= len(bars):
                        return None
                    return i + 1, float(opens[i + 1]), float(pb_ext - 1.0)
        else:
            best = min(best, lows[i])
            if not seen and best <= o - impulse:
                seen = True
                pb_ext = highs[i]
            if seen:
                pb_ext = max(pb_ext, highs[i])
                if pb_ext - best >= pb and closes[i] <= pb_ext - 1.0:
                    if i + 1 >= len(bars):
                        return None
                    return i + 1, float(opens[i + 1]), float(pb_ext + 1.0)
    return None


def find_reclaim(side, o, bars, dip):
    highs = bars["high"].to_numpy(np.float64)
    lows = bars["low"].to_numpy(np.float64)
    closes = bars["close"].to_numpy(np.float64)
    opens = bars["open"].to_numpy(np.float64)
    ext = None
    for i in range(len(bars)):
        if side > 0:
            if ext is None and lows[i] <= o - dip:
                ext = lows[i]
            if ext is not None:
                ext = min(ext, lows[i])
                if closes[i] >= o:
                    if i + 1 >= len(bars):
                        return None
                    return i + 1, float(opens[i + 1]), float(ext - 1.0)
        else:
            if ext is None and highs[i] >= o + dip:
                ext = highs[i]
            if ext is not None:
                ext = max(ext, highs[i])
                if closes[i] <= o:
                    if i + 1 >= len(bars):
                        return None
                    return i + 1, float(opens[i + 1]), float(ext + 1.0)
    return None


def find_open_break(side, o, bars, confirm_pts):
    """Enter on next open after first close confirm_pts beyond O in trade direction; structural stop = O -/+ buffer."""
    closes = bars["close"].to_numpy(np.float64)
    opens = bars["open"].to_numpy(np.float64)
    for i in range(len(bars)):
        if side > 0 and closes[i] >= o + confirm_pts:
            if i + 1 >= len(bars):
                return None
            return i + 1, float(opens[i + 1]), float(o - 1.0)
        if side < 0 and closes[i] <= o - confirm_pts:
            if i + 1 >= len(bars):
                return None
            return i + 1, float(opens[i + 1]), float(o + 1.0)
    return None


def find_at_open(side, o, bars, stop_beyond_extreme, w_lo, w_hi):
    """Enter at 09:30 open (bar 0 open); stop beyond W extreme or fixed handled later."""
    if len(bars) < 2:
        return None
    # entry is bar 0 open; path starts at bar 0
    if side > 0:
        stop = float(w_lo - 1.0) if stop_beyond_extreme else None
    else:
        stop = float(w_hi + 1.0) if stop_beyond_extreme else None
    return 0, float(o), stop


def apply_stop_target(side, entry, struct_stop, stop_mode, stop_pts, tgt_mode, tgt_pts, rr):
    if stop_mode == "structural":
        if struct_stop is None or not np.isfinite(struct_stop):
            return None
        stop = float(struct_stop)
    elif stop_mode == "fixed":
        stop = entry - side * stop_pts
    else:
        return None
    stop_dist = abs(entry - stop)
    if stop_dist < 1.0:
        return None
    if tgt_mode == "fixed":
        target = entry + side * tgt_pts
    elif tgt_mode == "rr":
        target = entry + side * (rr * stop_dist)
    else:
        return None
    return stop, target, stop_dist


def sim(info, ent_i, entry, stop, target, hold_h):
    full = info["rth_full"]
    search = info["rth_search"]
    ent_ny = int(search.iloc[ent_i]["ny_min"])
    pos = full.index[full["ny_min"] == ent_ny]
    if len(pos) == 0:
        return None
    p0 = int(pos[0])
    p1 = min(p0 + hold_h, len(full))
    if p1 <= p0:
        return None
    path = full.iloc[p0:p1]
    pnl, kind = path_exit(
        info["side"],
        entry,
        path["high"].to_numpy(),
        path["low"].to_numpy(),
        path["close"].to_numpy(),
        stop,
        target,
    )
    if not np.isfinite(pnl):
        return None
    sd = abs(entry - stop)
    return {"pnl": pnl, "kind": kind, "stop_dist": sd, "R": pnl / sd if sd > 1e-8 else np.nan}


def main() -> None:
    ART.mkdir(parents=True, exist_ok=True)
    nq = load_nq()
    m = (nq["ny_min"] >= SESSION_START) | (nq["ny_min"] < RTH_END)
    df = nq.loc[m]

    # Collect eligible day infos once
    days = []
    for sess, g0 in df.groupby("session_date", sort=False):
        info = classify(g0)
        if info is None or info["skip"]:
            continue
        year = int(g0["year"].iloc[0])
        for rev in REV_PTS:
            if not rev_ok(info, rev):
                continue
            days.append(
                {
                    "session_date": str(sess),
                    "split": split_of(year),
                    "year": year,
                    "rev": rev,
                    "info": info,
                }
            )
    print(f"eligible day-rev rows: {len(days)}", flush=True)

    # Precompute entry events per day (structural stop from entry rule)
    # entry_id -> list of (day_idx, ent_i, entry, struct_stop)
    entry_events: dict[str, list] = {}

    def add_entry(key, day_i, found):
        if found is None:
            return
        entry_events.setdefault(key, []).append((day_i, found[0], found[1], found[2]))

    for di, d in enumerate(days):
        info = d["info"]
        side, o, bars = info["side"], info["o930"], info["rth_search"]
        wh, wl = info["W_hi"], info["W_lo"]
        add_entry("at_open_wstop", di, find_at_open(side, o, bars, True, wl, wh))
        for dip in DIP:
            add_entry(f"reclaim_dip{int(dip)}", di, find_reclaim(side, o, bars, dip))
        for imp in IMPULSE:
            for pb in PB:
                add_entry(f"imp{int(imp)}_pb{int(pb)}", di, find_impulse_pb(side, o, bars, imp, pb))
        for conf in (5.0, 10.0, 15.0):
            add_entry(f"break{int(conf)}", di, find_open_break(side, o, bars, conf))
        if di % 200 == 0:
            print(f"entries… {di}/{len(days)}", flush=True)

    print(f"entry kinds: {len(entry_events)}", flush=True)

    # Risk/exit combos
    risk_combos = []
    # structural stop + fixed target
    for tgt in FIXED_TGTS:
        risk_combos.append(("structural", np.nan, "fixed", tgt, np.nan))
    # structural stop + RR
    for rr in RR:
        risk_combos.append(("structural", np.nan, "rr", np.nan, rr))
    # fixed stop + fixed target
    for sp in FIXED_STOPS:
        for tgt in FIXED_TGTS:
            risk_combos.append(("fixed", sp, "fixed", tgt, np.nan))
        for rr in RR:
            risk_combos.append(("fixed", sp, "rr", np.nan, rr))

    rows = []
    n_combo = 0
    for entry_key, events in entry_events.items():
        for stop_mode, stop_pts, tgt_mode, tgt_pts, rr in risk_combos:
            for hold_h in HOLD_HS:
                n_combo += 1
                # accumulate by split
                buckets: dict[str, list] = {"Discovery": [], "Validation": [], "OOS": []}
                kinds: dict[str, list] = {"Discovery": [], "Validation": [], "OOS": []}
                stops: dict[str, list] = {"Discovery": [], "Validation": [], "OOS": []}
                n_elig = {"Discovery": 0, "Validation": 0, "OOS": 0}
                # eligible days for this entry's rev is embedded in days list; count unique by split among events' days
                seen_day = set()
                for di, ent_i, entry, struct_stop in events:
                    d = days[di]
                    split = d["split"]
                    key = (d["session_date"], d["rev"], entry_key)
                    if key not in seen_day:
                        seen_day.add(key)
                        n_elig[split] = n_elig.get(split, 0) + 1
                    st = apply_stop_target(
                        d["info"]["side"], entry, struct_stop, stop_mode, stop_pts, tgt_mode, tgt_pts, rr
                    )
                    if st is None:
                        continue
                    stop, target, stop_dist = st
                    # for at_open with fixed stop, struct may be set; apply_stop_target overwrites with fixed
                    out = sim(d["info"], ent_i, entry, stop, target, hold_h)
                    if out is None:
                        continue
                    buckets[split].append(out["pnl"])
                    kinds[split].append(out["kind"])
                    stops[split].append(out["stop_dist"])

                for split in ("Discovery", "Validation", "OOS"):
                    x = np.asarray(buckets[split], dtype=np.float64)
                    if len(x) == 0:
                        rows.append(
                            {
                                "entry": entry_key,
                                "stop_mode": stop_mode,
                                "stop_pts": stop_pts,
                                "tgt_mode": tgt_mode,
                                "tgt_pts": tgt_pts,
                                "rr": rr,
                                "hold_h": hold_h,
                                "split": split,
                                "n": 0,
                                "n_elig": n_elig.get(split, 0),
                                "trig_rate": np.nan,
                                "win": np.nan,
                                "E_net": np.nan,
                                "E_R": np.nan,
                                "target_hit": np.nan,
                                "stop_hit": np.nan,
                                "time_exit": np.nan,
                                "median_stop": np.nan,
                            }
                        )
                        continue
                    k = np.asarray(kinds[split])
                    sd = np.asarray(stops[split], dtype=np.float64)
                    rows.append(
                        {
                            "entry": entry_key,
                            "stop_mode": stop_mode,
                            "stop_pts": stop_pts,
                            "tgt_mode": tgt_mode,
                            "tgt_pts": tgt_pts,
                            "rr": rr,
                            "hold_h": hold_h,
                            "split": split,
                            "n": int(len(x)),
                            "n_elig": n_elig.get(split, 0),
                            "trig_rate": float(len(x) / n_elig[split]) if n_elig.get(split, 0) else np.nan,
                            "win": float(np.mean(x > 0)),
                            "E_net": float(np.mean(x)),
                            "E_R": float(np.mean(x / sd)),
                            "target_hit": float(np.mean(k == "target")),
                            "stop_hit": float(np.mean((k == "stop") | (k == "stop_samebar"))),
                            "time_exit": float(np.mean(k == "time")),
                            "median_stop": float(np.median(sd)),
                        }
                    )
                if n_combo % 50 == 0:
                    print(f"risk combos done ~{n_combo} last={entry_key}", flush=True)

    grid = pd.DataFrame(rows)
    grid.to_csv(ART / "phase_e_grid.csv", index=False)
    print(f"grid rows: {len(grid)}", flush=True)

    # survivors
    idx_cols = ["entry", "stop_mode", "stop_pts", "tgt_mode", "tgt_pts", "rr", "hold_h"]
    piv = grid.pivot_table(index=idx_cols, columns="split", values="E_net", aggfunc="first")
    cnt = grid.pivot_table(index=idx_cols, columns="split", values="n", aggfunc="first")
    survivors = []
    for idx in piv.index:
        e_v = piv.loc[idx].get("Validation", np.nan)
        e_o = piv.loc[idx].get("OOS", np.nan)
        e_d = piv.loc[idx].get("Discovery", np.nan)
        n_v = cnt.loc[idx].get("Validation", 0) or 0
        n_o = cnt.loc[idx].get("OOS", 0) or 0
        if np.isfinite(e_v) and np.isfinite(e_o) and e_v > 0 and e_o > 0 and n_v >= 30 and n_o >= 25:
            survivors.append(
                {
                    "entry": idx[0],
                    "stop_mode": idx[1],
                    "stop_pts": idx[2],
                    "tgt_mode": idx[3],
                    "tgt_pts": idx[4],
                    "rr": idx[5],
                    "hold_h": idx[6],
                    "E_Discovery": float(e_d) if np.isfinite(e_d) else None,
                    "E_Validation": float(e_v),
                    "E_OOS": float(e_o),
                    "n_Validation": int(n_v),
                    "n_OOS": int(n_o),
                }
            )
    surv = pd.DataFrame(survivors)
    if len(surv):
        surv = surv.sort_values(["E_OOS", "E_Validation"], ascending=False)
    surv.to_csv(ART / "phase_e_survivors.csv", index=False)

    # summaries by entry family / stop / rr
    def family(e: str) -> str:
        if e.startswith("reclaim"):
            return "reclaim"
        if e.startswith("imp"):
            return "impulse_pb"
        if e.startswith("break"):
            return "break"
        if e.startswith("at_open"):
            return "at_open"
        return e

    g2 = grid.copy()
    g2["family"] = g2["entry"].map(family)
    fam = (
        g2[g2["n"] >= 20]
        .groupby(["family", "split"], as_index=False)
        .agg(median_E=("E_net", "median"), mean_E=("E_net", "mean"), n_cells=("E_net", "size"), pct_pos=("E_net", lambda s: float(np.mean(s > 0))))
    )
    fam.to_csv(ART / "phase_e_by_family.csv", index=False)

    risk_sum = (
        g2[g2["n"] >= 20]
        .groupby(["stop_mode", "tgt_mode", "split"], as_index=False)
        .agg(median_E=("E_net", "median"), pct_pos=("E_net", lambda s: float(np.mean(s > 0))), n_cells=("E_net", "size"))
    )
    risk_sum.to_csv(ART / "phase_e_by_risk.csv", index=False)

    hold_sum = (
        g2[g2["n"] >= 20]
        .groupby(["hold_h", "split"], as_index=False)
        .agg(median_E=("E_net", "median"), pct_pos=("E_net", lambda s: float(np.mean(s > 0))))
    )
    hold_sum.to_csv(ART / "phase_e_by_hold.csv", index=False)

    # best Discovery / Val / OOS tables
    best = {}
    for split in ("Discovery", "Validation", "OOS"):
        sub = grid[(grid["split"] == split) & (grid["n"] >= 30)].sort_values("E_net", ascending=False).head(20)
        best[split] = sub
        sub.to_csv(ART / f"phase_e_best_{split}.csv", index=False)

    # cross-split join for top Val cells with OOS
    val = grid[(grid["split"] == "Validation") & (grid["n"] >= 30)].copy()
    oos = grid[(grid["split"] == "OOS") & (grid["n"] >= 25)].copy()
    disc = grid[(grid["split"] == "Discovery") & (grid["n"] >= 30)].copy()
    merged = val.merge(
        oos,
        on=idx_cols,
        suffixes=("_val", "_oos"),
    ).merge(disc, on=idx_cols, suffixes=("", "_disc"))
    # after merge disc columns may be without suffix for E_net etc - fix
    # Actually third merge: disc columns collide. Redo cleanly.
    val2 = val.rename(columns={c: f"{c}_val" for c in val.columns if c not in idx_cols})
    oos2 = oos.rename(columns={c: f"{c}_oos" for c in oos.columns if c not in idx_cols})
    disc2 = disc.rename(columns={c: f"{c}_disc" for c in disc.columns if c not in idx_cols})
    merged = val2.merge(oos2, on=idx_cols).merge(disc2, on=idx_cols)
    merged["min_E_val_oos"] = merged[["E_net_val", "E_net_oos"]].min(axis=1)
    merged = merged.sort_values("min_E_val_oos", ascending=False)
    merged.head(50).to_csv(ART / "phase_e_cross_rank.csv", index=False)

    verdict = {
        "n_grid_rows": int(len(grid)),
        "n_entry_kinds": int(len(entry_events)),
        "n_survivors_val_oos": int(len(surv)),
        "survivors_top": survivors[:25],
        "family_median_E": fam.to_dict(orient="records"),
        "risk_median_E": risk_sum.to_dict(orient="records"),
        "hold_median_E": hold_sum.to_dict(orient="records"),
        "best_cross_min_val_oos": merged.head(15)[
            idx_cols
            + ["E_net_disc", "E_net_val", "E_net_oos", "n_val", "n_oos", "win_val", "win_oos"]
        ].to_dict(orient="records")
        if len(merged)
        else [],
        "class": "B_REVIEW" if len(surv) else "C",
        "label": "PARAM_COMPARE_HAS_SURVIVORS" if len(surv) else "PARAM_COMPARE_NO_SURVIVOR",
    }
    (ART / "phase_e_verdict.json").write_text(json.dumps(verdict, indent=2, default=float), encoding="utf-8")

    md = [
        "# Strategy 29 — Phase E parameter comparison",
        "",
        f"Survivors Val+OOS: **{len(surv)}** / class `{verdict['class']}`",
        "",
        "## By entry family (median E_net, n≥20 cells)",
        "",
        fam.to_markdown(index=False),
        "",
        "## By risk style",
        "",
        risk_sum.to_markdown(index=False),
        "",
        "## By hold",
        "",
        hold_sum.to_markdown(index=False),
        "",
        "## Survivors",
        "",
        surv.head(30).to_markdown(index=False) if len(surv) else "_none_",
        "",
        "## Best by min(Val,OOS) E_net",
        "",
        merged.head(20)[
            idx_cols + ["E_net_disc", "E_net_val", "E_net_oos", "n_val", "n_oos"]
        ].to_markdown(index=False)
        if len(merged)
        else "_none_",
    ]
    (ART / "phase_e_report.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps({k: verdict[k] for k in ("class", "label", "n_survivors_val_oos", "n_grid_rows")}, indent=2))
    print(fam.to_string(index=False))
    print("survivors", len(surv))


if __name__ == "__main__":
    main()
