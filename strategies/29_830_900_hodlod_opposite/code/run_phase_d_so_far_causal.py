"""
Strategy 29 Phase D — corrected causal: day-so-far extreme in 08:30-09:00,
reversal before open, skip if 09:30 still at extreme, impulse/pullback entries.
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
PRE_END = OPEN  # ny_min < 09:30
SEARCH_END = 10 * 60 + 30
RTH_END = 16 * 60
COST = 1.0
HOLD_H = 30

REV_PTS = (5.0, 10.0)
IMPULSE = (10.0, 15.0, 20.0)
PB = (5.0, 10.0)
DIP = (5.0, 10.0)
TARGETS = (20.0, 25.0, 30.0)


def split_of(year: int) -> str:
    if year in IS_YEARS:
        return "Discovery"
    if year in VAL_YEARS:
        return "Validation"
    if year in OOS_YEARS:
        return "OOS"
    return "OTHER"


def path_exit(side: float, entry: float, highs, lows, closes, stop: float, target: float):
    if not np.isfinite(entry) or side == 0:
        return float("nan"), "invalid"
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
        return float("nan"), "invalid"
    return side * (last - entry) - COST, "time"


def classify_day(g: pd.DataFrame) -> dict | None:
    """Return eligibility fields or None if insufficient data."""
    g = g.sort_values("ny_min")
    w = g[(g["ny_min"] >= W0) & (g["ny_min"] < W1)]
    pre900 = g[g["ny_min"] < W1]
    pre929 = g[g["ny_min"] < PRE_END]
    rth_search = g[(g["ny_min"] >= OPEN) & (g["ny_min"] < SEARCH_END)]
    if len(w) < 20 or len(pre900) < 30 or len(pre929) < 30 or len(rth_search) < 5:
        return None

    wh, wl = float(w["high"].max()), float(w["low"].min())
    sf_hi = float(pre900["high"].max())
    sf_lo = float(pre900["low"].min())
    lod = abs(wl - sf_lo) < 1e-8 and abs(wh - sf_hi) >= 1e-8
    hod = abs(wh - sf_hi) < 1e-8 and abs(wl - sf_lo) >= 1e-8
    if lod == hod:  # both or neither
        return {
            "eligible_label": False,
            "label": "BOTH" if (abs(wl - sf_lo) < 1e-8 and abs(wh - sf_hi) < 1e-8) else "NEITHER",
        }

    label = "LOD_SO_FAR" if lod else "HOD_SO_FAR"
    side = 1 if lod else -1
    bar929 = pre929[pre929["ny_min"] == OPEN - 1]
    if len(bar929) == 0:
        # nearest last bar before open
        bar929 = pre929.iloc[[-1]]
    c929 = float(bar929.iloc[0]["close"])
    sf_hi_929 = float(pre929["high"].max())
    sf_lo_929 = float(pre929["low"].min())

    o930 = float(rth_search.iloc[0]["open"])
    # skip if still at extreme at open
    skip_at_ext = (side > 0 and o930 <= sf_lo_929 + 1e-8) or (side < 0 and o930 >= sf_hi_929 - 1e-8)

    return {
        "eligible_label": True,
        "label": label,
        "side": side,
        "W_hi": wh,
        "W_lo": wl,
        "close_0929": c929,
        "so_far_hi_0929": sf_hi_929,
        "so_far_lo_0929": sf_lo_929,
        "o930": o930,
        "skip_at_ext": skip_at_ext,
        "rth_search": rth_search.reset_index(drop=True),
        "rth_full": g[(g["ny_min"] >= OPEN) & (g["ny_min"] < RTH_END)].sort_values("ny_min").reset_index(drop=True),
    }


def reversed_ok(info: dict, rev_pts: float) -> bool:
    if info["side"] > 0:
        return info["close_0929"] >= info["W_lo"] + rev_pts
    return info["close_0929"] <= info["W_hi"] - rev_pts


def entry_impulse_pb(side: int, o: float, bars: pd.DataFrame, impulse_pts: float, pb_pts: float):
    highs = bars["high"].to_numpy(np.float64)
    lows = bars["low"].to_numpy(np.float64)
    closes = bars["close"].to_numpy(np.float64)
    opens = bars["open"].to_numpy(np.float64)
    n = len(bars)
    # stage 1: impulse
    imp_i = None
    for i in range(n):
        if side > 0 and highs[i] >= o + impulse_pts:
            imp_i = i
            break
        if side < 0 and lows[i] <= o - impulse_pts:
            imp_i = i
            break
    if imp_i is None:
        return None
    # stage 2: pullback extreme after impulse
    pb_ext = None
    pb_i = None
    for j in range(imp_i, n):
        if side > 0:
            # pullback down
            if lows[j] <= highs[imp_i] - pb_pts:  # or from running max?
                # use distance from post-impulse peak
                pass
        # simpler: from O+impulse level, pull back pb_pts from the best favorable ext so far
    # clearer state machine:
    best_fav = o
    seen_impulse = False
    pb_extreme = None
    for i in range(n):
        if side > 0:
            best_fav = max(best_fav, highs[i])
            if not seen_impulse and best_fav >= o + impulse_pts:
                seen_impulse = True
                pb_extreme = lows[i]
            if seen_impulse:
                pb_extreme = min(pb_extreme, lows[i])
                # pullback deep enough from best_fav
                if best_fav - pb_extreme >= pb_pts:
                    # resume: close back up through pb_extreme + 1 toward best
                    if closes[i] >= pb_extreme + 1.0:
                        ent = i + 1
                        if ent >= n:
                            return None
                        return ent, float(opens[ent]), float(pb_extreme - 1.0)
        else:
            best_fav = min(best_fav, lows[i])
            if not seen_impulse and best_fav <= o - impulse_pts:
                seen_impulse = True
                pb_extreme = highs[i]
            if seen_impulse:
                pb_extreme = max(pb_extreme, highs[i])
                if pb_extreme - best_fav >= pb_pts:
                    if closes[i] <= pb_extreme - 1.0:
                        ent = i + 1
                        if ent >= n:
                            return None
                        return ent, float(opens[ent]), float(pb_extreme + 1.0)
    return None


def entry_reclaim(side: int, o: float, bars: pd.DataFrame, dip_pts: float):
    highs = bars["high"].to_numpy(np.float64)
    lows = bars["low"].to_numpy(np.float64)
    closes = bars["close"].to_numpy(np.float64)
    opens = bars["open"].to_numpy(np.float64)
    n = len(bars)
    dip_ext = None
    for i in range(n):
        if side > 0:
            # adverse dip down then reclaim O
            if dip_ext is None and lows[i] <= o - dip_pts:
                dip_ext = lows[i]
            if dip_ext is not None:
                dip_ext = min(dip_ext, lows[i])
                if closes[i] >= o:
                    ent = i + 1
                    if ent >= n:
                        return None
                    return ent, float(opens[ent]), float(dip_ext - 1.0)
        else:
            if dip_ext is None and highs[i] >= o + dip_pts:
                dip_ext = highs[i]
            if dip_ext is not None:
                dip_ext = max(dip_ext, highs[i])
                if closes[i] <= o:
                    ent = i + 1
                    if ent >= n:
                        return None
                    return ent, float(opens[ent]), float(dip_ext + 1.0)
    return None


def simulate_from_entry(info: dict, ent_i: int, entry: float, stop: float, side: int, target_pts: float):
    rth = info["rth_search"]
    full = info["rth_full"]
    ent_ny = int(rth.iloc[ent_i]["ny_min"])
    pos = full.index[full["ny_min"] == ent_ny]
    if len(pos) == 0:
        return None
    p0 = int(pos[0])
    p1 = min(p0 + HOLD_H, len(full))
    if p1 <= p0:
        return None
    path = full.iloc[p0:p1]
    tgt = entry + side * target_pts
    pnl, kind = path_exit(
        float(side),
        entry,
        path["high"].to_numpy(),
        path["low"].to_numpy(),
        path["close"].to_numpy(),
        stop,
        tgt,
    )
    if not np.isfinite(pnl):
        return None
    stop_dist = abs(entry - stop)
    return {
        "pnl": pnl,
        "kind": kind,
        "stop_dist": stop_dist,
        "R": pnl / stop_dist if stop_dist > 1e-8 else np.nan,
    }


def main() -> None:
    ART.mkdir(parents=True, exist_ok=True)
    nq = load_nq()
    m = (nq["ny_min"] >= SESSION_START) | (nq["ny_min"] < RTH_END)
    df = nq.loc[m].copy()

    day_meta = []
    trade_rows = []

    for sess, g0 in df.groupby("session_date", sort=False):
        year = int(g0["year"].iloc[0])
        split = split_of(year)
        info = classify_day(g0)
        if info is None:
            continue
        if not info["eligible_label"]:
            day_meta.append({"session_date": str(sess), "split": split, "label": info["label"], "setup_ok": False})
            continue

        for rev in REV_PTS:
            rev_ok = reversed_ok(info, rev)
            setup_ok = rev_ok and (not info["skip_at_ext"])
            day_meta.append(
                {
                    "session_date": str(sess),
                    "split": split,
                    "year": year,
                    "label": info["label"],
                    "side": info["side"],
                    "rev": rev,
                    "rev_ok": rev_ok,
                    "skip_at_ext": info["skip_at_ext"],
                    "setup_ok": setup_ok,
                }
            )
            if not setup_ok:
                continue

            side = int(info["side"])
            o = float(info["o930"])
            bars = info["rth_search"]

            # impulse_pb grid
            for imp in IMPULSE:
                for pb in PB:
                    found = entry_impulse_pb(side, o, bars, imp, pb)
                    for tgt in TARGETS:
                        base = {
                            "session_date": str(sess),
                            "split": split,
                            "year": year,
                            "label": info["label"],
                            "entry_style": "impulse_pb",
                            "rev": rev,
                            "impulse": imp,
                            "pb": pb,
                            "dip": np.nan,
                            "target": tgt,
                            "side": side,
                        }
                        if found is None:
                            trade_rows.append({**base, "triggered": False})
                        else:
                            ent_i, entry, stop = found
                            sim = simulate_from_entry(info, ent_i, entry, stop, side, tgt)
                            if sim is None:
                                trade_rows.append({**base, "triggered": False})
                            else:
                                trade_rows.append(
                                    {
                                        **base,
                                        "triggered": True,
                                        "pnl": sim["pnl"],
                                        "kind": sim["kind"],
                                        "stop_dist": sim["stop_dist"],
                                        "R": sim["R"],
                                    }
                                )

            # reclaim grid
            for dip in DIP:
                found = entry_reclaim(side, o, bars, dip)
                for tgt in TARGETS:
                    base = {
                        "session_date": str(sess),
                        "split": split,
                        "year": year,
                        "label": info["label"],
                        "entry_style": "reclaim_O",
                        "rev": rev,
                        "impulse": np.nan,
                        "pb": np.nan,
                        "dip": dip,
                        "target": tgt,
                        "side": side,
                    }
                    if found is None:
                        trade_rows.append({**base, "triggered": False})
                    else:
                        ent_i, entry, stop = found
                        sim = simulate_from_entry(info, ent_i, entry, stop, side, tgt)
                        if sim is None:
                            trade_rows.append({**base, "triggered": False})
                        else:
                            trade_rows.append(
                                {
                                    **base,
                                    "triggered": True,
                                    "pnl": sim["pnl"],
                                    "kind": sim["kind"],
                                    "stop_dist": sim["stop_dist"],
                                    "R": sim["R"],
                                }
                            )

    meta = pd.DataFrame(day_meta)
    trades = pd.DataFrame(trade_rows)
    meta.to_csv(ART / "phase_d_day_meta.csv", index=False)
    trades.to_parquet(ART / "phase_d_trades.parquet", index=False)

    # setup frequency
    freq_rows = []
    for (rev, split), g in meta.groupby(["rev", "split"]):
        # one row per session per rev — take unique sessions
        u = g.drop_duplicates("session_date")
        # need label-eligible base rate from days with eligible_label
        freq_rows.append(
            {
                "rev": rev,
                "split": split,
                "n_labeled_days": int(u["session_date"].nunique()),
                "pct_setup_ok": float(u["setup_ok"].mean()) if len(u) else np.nan,
                "pct_rev_ok": float(u["rev_ok"].mean()) if len(u) else np.nan,
                "pct_skip_at_ext": float(u["skip_at_ext"].mean()) if len(u) else np.nan,
            }
        )
    # better: among days with LOD/HOD so far label
    labeled = meta[meta["label"].isin(["LOD_SO_FAR", "HOD_SO_FAR"])]
    freq = (
        labeled.groupby(["rev", "split"], as_index=False)
        .agg(
            n=("session_date", "nunique"),
            pct_setup_ok=("setup_ok", "mean"),
            pct_rev_ok=("rev_ok", "mean"),
            pct_skip_at_ext=("skip_at_ext", "mean"),
            pct_lod=("label", lambda s: float(np.mean(s == "LOD_SO_FAR"))),
        )
    )
    freq.to_csv(ART / "phase_d_setup_freq.csv", index=False)

    # how often W is day-so-far xor extreme (unique days, ignore rev dup)
    base_lab = meta.drop_duplicates("session_date")
    # meta only has labeled days in eligible path... also NEITHER/BOTH
    all_lab = meta.groupby("session_date").first().reset_index()
    label_rate = all_lab.groupby("split")["label"].value_counts(normalize=True).unstack(fill_value=0)
    label_rate.to_csv(ART / "phase_d_label_rates.csv")

    trig = trades[trades["triggered"] == True]  # noqa: E712
    rows = []
    keys = ["entry_style", "rev", "impulse", "pb", "dip", "target", "split"]
    for kvals, g in trig.groupby(keys, dropna=False):
        x = g["pnl"].to_numpy(np.float64)
        r = g["R"].to_numpy(np.float64)
        rows.append(
            {
                "entry_style": kvals[0],
                "rev": kvals[1],
                "impulse": kvals[2],
                "pb": kvals[3],
                "dip": kvals[4],
                "target": kvals[5],
                "split": kvals[6],
                "n": int(len(x)),
                "win": float(np.mean(x > 0)),
                "E_net": float(np.mean(x)),
                "E_R": float(np.nanmean(r)),
                "target_hit": float(np.mean(g["kind"] == "target")),
                "stop_hit": float(np.mean(g["kind"].isin(["stop", "stop_samebar"]))),
                "time_exit": float(np.mean(g["kind"] == "time")),
                "median_stop_dist": float(np.median(g["stop_dist"])),
            }
        )
    grid = pd.DataFrame(rows)

    # trigger rates from full trades
    rates = (
        trades.groupby(keys, dropna=False)
        .agg(n_days=("session_date", "nunique"), n_trig=("triggered", "sum"))
        .reset_index()
    )
    rates["trig_rate"] = rates["n_trig"] / rates["n_days"].replace(0, np.nan)
    grid = grid.merge(rates, on=keys, how="left")
    grid.to_csv(ART / "phase_d_grid.csv", index=False)

    survivors = []
    if len(grid):
        idx_cols = ["entry_style", "rev", "impulse", "pb", "dip", "target"]
        piv = grid.pivot_table(index=idx_cols, columns="split", values="E_net", aggfunc="first")
        cnt = grid.pivot_table(index=idx_cols, columns="split", values="n", aggfunc="first")
        for idx in piv.index:
            e_v = piv.loc[idx].get("Validation", np.nan)
            e_o = piv.loc[idx].get("OOS", np.nan)
            e_d = piv.loc[idx].get("Discovery", np.nan)
            n_v = cnt.loc[idx].get("Validation", 0) or 0
            n_o = cnt.loc[idx].get("OOS", 0) or 0
            if np.isfinite(e_v) and np.isfinite(e_o) and e_v > 0 and e_o > 0 and n_v >= 30 and n_o >= 30:
                survivors.append(
                    {
                        "entry_style": idx[0],
                        "rev": idx[1],
                        "impulse": idx[2],
                        "pb": idx[3],
                        "dip": idx[4],
                        "target": idx[5],
                        "E_Discovery": e_d,
                        "E_Validation": e_v,
                        "E_OOS": e_o,
                        "n_Validation": int(n_v),
                        "n_OOS": int(n_o),
                    }
                )
    surv = pd.DataFrame(survivors)
    surv.to_csv(ART / "phase_d_survivors.csv", index=False)

    # Discovery rank for reporting
    disc = grid[grid["split"] == "Discovery"].sort_values("E_net", ascending=False).head(15)
    oos_best = grid[grid["split"] == "OOS"].sort_values("E_net", ascending=False).head(15)

    # headline: reclaim dip10 rev10 tgt25 and impulse 15/5 rev10 tgt25
    def cell(style, rev, tgt, impulse=np.nan, pb=np.nan, dip=np.nan):
        m = (grid["entry_style"] == style) & (grid["rev"] == rev) & (grid["target"] == tgt)
        if style == "impulse_pb":
            m &= (grid["impulse"] == impulse) & (grid["pb"] == pb)
        else:
            m &= grid["dip"] == dip
        return grid.loc[m, ["split", "n", "trig_rate", "win", "E_net", "E_R", "target_hit", "stop_hit"]]

    h1 = cell("reclaim_O", 10.0, 25.0, dip=10.0)
    h2 = cell("impulse_pb", 10.0, 25.0, impulse=15.0, pb=5.0)

    if len(surv) == 0:
        klass, label = "C", "NO_CAUSAL_EDGE"
    else:
        strong = surv[surv["E_Discovery"].fillna(-1) > 0]
        klass, label = ("B", "CAUSAL_CANDIDATE") if len(strong) else ("B", "VAL_OOS_SOFT")

    verdict = {
        "class": klass,
        "label": label,
        "n_survivors": int(len(surv)),
        "survivors": survivors[:30],
        "headline_reclaim_rev10_dip10_tgt25": h1.to_dict(orient="records"),
        "headline_impulse_rev10_imp15_pb5_tgt25": h2.to_dict(orient="records"),
        "note": "Corrected: day-so-far extreme in W, reverse before open, skip if 09:30 still at extreme",
    }
    (ART / "phase_d_verdict.json").write_text(json.dumps(verdict, indent=2, default=float), encoding="utf-8")

    md = [
        "# Strategy 29 — Phase D (corrected causal)",
        "",
        f"**Verdict: `{klass}` — {label}**",
        f"Survivors (Val+OOS E_net>0, n≥30): **{len(surv)}**",
        "",
        "## Setup frequency (labeled LOD/HOD so-far days)",
        "",
        freq.to_markdown(index=False),
        "",
        "## Label mix",
        "",
        label_rate.to_markdown(),
        "",
        "## Headline reclaim_O rev=10 dip=10 tgt=25",
        "",
        h1.to_markdown(index=False) if len(h1) else "_none_",
        "",
        "## Headline impulse_pb rev=10 imp=15 pb=5 tgt=25",
        "",
        h2.to_markdown(index=False) if len(h2) else "_none_",
        "",
        "## Survivors",
        "",
        surv.to_markdown(index=False) if len(surv) else "_none_",
        "",
        "## Best Discovery cells",
        "",
        disc.to_markdown(index=False),
        "",
        "## Best OOS cells (descriptive)",
        "",
        oos_best.to_markdown(index=False),
    ]
    (ART / "phase_d_report.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps(verdict, indent=2, default=float))
    print(freq.to_string(index=False))


if __name__ == "__main__":
    main()
