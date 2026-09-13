"""Year break for Phase E soft survivor: imp20_pb5, stop25, tgt40, hold60."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))

from common.nq_session import SESSION_START, load_nq
from common.paths import ROOT

ART = ROOT / "artifacts" / "29_830_900_hodlod_opposite"
W0, W1 = 8 * 60 + 30, 9 * 60
OPEN = 9 * 60 + 30
SEARCH_END = 11 * 60
RTH_END = 16 * 60
COST = 1.0


def path_exit(side, entry, highs, lows, closes, stop, target):
    for i in range(len(highs)):
        hi, lo = float(highs[i]), float(lows[i])
        if side > 0:
            hs, ht = lo <= stop, hi >= target
        else:
            hs, ht = hi >= stop, lo <= target
        if hs and ht:
            return side * (stop - entry) - COST, "stop_samebar"
        if hs:
            return side * (stop - entry) - COST, "stop"
        if ht:
            return side * (target - entry) - COST, "target"
    return side * (float(closes[-1]) - entry) - COST, "time"


def main() -> None:
    nq = load_nq()
    m = (nq["ny_min"] >= SESSION_START) | (nq["ny_min"] < RTH_END)
    df = nq.loc[m]
    rows = []
    for sess, g0 in df.groupby("session_date", sort=False):
        g = g0.sort_values("ny_min")
        w = g[(g["ny_min"] >= W0) & (g["ny_min"] < W1)]
        pre900 = g[g["ny_min"] < W1]
        pre929 = g[g["ny_min"] < OPEN]
        rth = g[(g["ny_min"] >= OPEN) & (g["ny_min"] < SEARCH_END)].reset_index(drop=True)
        full = g[(g["ny_min"] >= OPEN) & (g["ny_min"] < RTH_END)].reset_index(drop=True)
        if len(w) < 20 or len(pre900) < 30 or len(rth) < 5:
            continue
        wh, wl = float(w["high"].max()), float(w["low"].min())
        sf_hi, sf_lo = float(pre900["high"].max()), float(pre900["low"].min())
        lod = abs(wl - sf_lo) < 1e-8 and abs(wh - sf_hi) >= 1e-8
        hod = abs(wh - sf_hi) < 1e-8 and abs(wl - sf_lo) >= 1e-8
        if lod == hod:
            continue
        side = 1 if lod else -1
        c929 = float(pre929.iloc[-1]["close"])
        o = float(rth.iloc[0]["open"])
        sf_lo929 = float(pre929["low"].min())
        sf_hi929 = float(pre929["high"].max())
        if (side > 0 and o <= sf_lo929) or (side < 0 and o >= sf_hi929):
            continue
        if side > 0 and c929 < wl + 5:
            continue
        if side < 0 and c929 > wh - 5:
            continue
        highs = rth["high"].to_numpy()
        lows = rth["low"].to_numpy()
        closes = rth["close"].to_numpy()
        opens = rth["open"].to_numpy()
        best = o
        seen = False
        pb_ext = None
        found = None
        for i in range(len(rth)):
            if side > 0:
                best = max(best, highs[i])
                if not seen and best >= o + 20:
                    seen = True
                    pb_ext = lows[i]
                if seen:
                    pb_ext = min(pb_ext, lows[i])
                    if best - pb_ext >= 5 and closes[i] >= pb_ext + 1:
                        if i + 1 < len(rth):
                            found = (i + 1, float(opens[i + 1]))
                        break
            else:
                best = min(best, lows[i])
                if not seen and best <= o - 20:
                    seen = True
                    pb_ext = highs[i]
                if seen:
                    pb_ext = max(pb_ext, highs[i])
                    if pb_ext - best >= 5 and closes[i] <= pb_ext - 1:
                        if i + 1 < len(rth):
                            found = (i + 1, float(opens[i + 1]))
                        break
        if not found:
            continue
        ent_i, entry = found
        stop = entry - side * 25
        target = entry + side * 40
        ent_ny = int(rth.iloc[ent_i]["ny_min"])
        pos = full.index[full["ny_min"] == ent_ny]
        if len(pos) == 0:
            continue
        p0 = int(pos[0])
        p1 = min(p0 + 60, len(full))
        path = full.iloc[p0:p1]
        pnl, kind = path_exit(
            side,
            entry,
            path["high"].to_numpy(),
            path["low"].to_numpy(),
            path["close"].to_numpy(),
            stop,
            target,
        )
        rows.append({"year": int(g["year"].iloc[0]), "pnl": pnl, "kind": kind, "win": pnl > 0})

    t = pd.DataFrame(rows)
    yearly = t.groupby("year").agg(n=("pnl", "size"), E=("pnl", "mean"), win=("win", "mean")).reset_index()
    yearly.to_csv(ART / "phase_e_candidate_yearly.csv", index=False)
    print(yearly.to_string(index=False))
    print("overall n", len(t), "E", t["pnl"].mean(), "win", t["win"].mean())
    # OOS years
    oos = t[t["year"].isin([2025, 2026])]
    print("2025", oos[oos.year == 2025]["pnl"].mean() if (oos.year == 2025).any() else None)
    print("2026", oos[oos.year == 2026]["pnl"].mean() if (oos.year == 2026).any() else None)


if __name__ == "__main__":
    main()
