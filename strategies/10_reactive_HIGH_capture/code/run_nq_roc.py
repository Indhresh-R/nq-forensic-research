"""
Reactive Opportunity Capture (ROC) — NOT another directional family

Frozen HIGH untouched. No levels/VWAP/options/macro/ES/volume/dead features.

Core question:
  Conditional on HIGH, after a sufficiently large CAUSAL displacement occurs,
  is entering in the direction of that displacement economically better than
  entering at HIGH activation before the move is revealed?

Arms:
  BLIND  — at next open after first HIGH (T0), enter using session direction
           sign(close_T0 - open_930) if nonzero (premature / pre-reveal)
  REACTIVE — from T0, wait until price first reaches ±DISP from close_T0;
           enter next bar in that revealed direction (within WAIT_MAX)

Frozen (do not sweep):
  DISP = 0.15 * ONR
  WAIT_MAX = 30 minutes
  First HIGH only in 09:35–11:00 (scarcity / ~1/day style)
  PRIMARY ARM = vol_expansion_high (IS p66 rng_onr) — NEVER retuned

Compare paired paths: same HIGH activations; IS→Val→OOS→2025/2026.
"""
from __future__ import annotations

import sys
from pathlib import Path

_CODE = Path(__file__).resolve().parent
_ROOT = _CODE.parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_CODE) not in sys.path:
    sys.path.insert(0, str(_CODE))


import json
import warnings
from typing import Any

import numpy as np
import pandas as pd

from common.nq_session import art, ART, NY_OPEN, build_day_context, load_nq, state_at_T

warnings.filterwarnings("ignore", category=FutureWarning)

ARM_OFFSETS = tuple(range(5, 91, 5))  # 09:35–11:00
FWD_HORIZONS = (10, 15, 30, 45, 60)
DISP_ONR = 0.15  # frozen displacement as fraction of ONR
WAIT_MAX = 30  # minutes after T0 to observe displacement
STRUCT_FRAC = 0.25  # frozen structural R (from opportunity gate; not retuned)
IS_Y = set(range(2010, 2022))
VAL_Y = {2022, 2023, 2024}
OOS_Y = {2025, 2026}

THRESH = json.loads((art("ny_open_opp_timing_thresholds_IS.json")).read_text(encoding="utf-8"))
STATE_TH = THRESH["state_terciles"]


def split_of(y: int) -> str:
    if y in IS_Y:
        return "IS"
    if y in VAL_Y:
        return "Validation"
    if y in OOS_Y:
        return "OOS"
    return "OTHER"


def th_get(feat: str, off: int) -> dict[str, float]:
    d = STATE_TH[feat]
    return d.get(str(off)) or d.get(off) or {}


def is_high(rng_onr: float, off: int) -> bool:
    t = th_get("rng_onr", off)
    if not t:
        return False
    return float(rng_onr) >= float(t["p66"])


def first_touch_dir(
    highs: np.ndarray,
    lows: np.ndarray,
    ref: float,
    thr: float,
) -> tuple[int, int] | None:
    """
    Scan bars; return (bar_index, direction) of first ±thr touch.
    Same-bar both → skip (ambiguous).
    """
    for i in range(len(highs)):
        up = highs[i] >= ref + thr
        dn = lows[i] <= ref - thr
        if up and dn:
            return None  # ambiguous bar — treat as no clean reveal this bar; continue? 
            # For cleanliness: abort trigger on ambiguity at first dual-touch bar
            # Better: skip this bar and continue — but dual touch means both hit.
            # Abort entire wait as unclean:
            return None
        if up:
            return i, 1
        if dn:
            return i, -1
    return None


def first_touch_dir_continue(
    highs: np.ndarray,
    lows: np.ndarray,
    ref: float,
    thr: float,
) -> tuple[int, int] | None:
    """First unambiguous single-side touch; skip bars that hit both."""
    for i in range(len(highs)):
        up = highs[i] >= ref + thr
        dn = lows[i] <= ref - thr
        if up and dn:
            continue
        if up:
            return i, 1
        if dn:
            return i, -1
    return None


def signed_path(
    o: np.ndarray,
    h: np.ndarray,
    l: np.ndarray,
    c: np.ndarray,
    entry_i: int,
    direction: int,
    H: int,
    onr: float,
) -> dict[str, float]:
    end_i = entry_i + H - 1
    nan = {k: np.nan for k in ("fwd", "fwd_onr", "mfe", "mae", "mfe_gt_mae", "hit_struct", "hit1R")}
    if entry_i >= len(c) or end_i >= len(c) or direction == 0:
        return nan
    entry = float(o[entry_i])
    hh = h[entry_i : end_i + 1]
    ll = l[entry_i : end_i + 1]
    fwd = float(c[end_i] - entry) * direction
    if direction > 0:
        mfe = float(hh.max() - entry)
        mae = float(entry - ll.min())
    else:
        mfe = float(entry - ll.min())
        mae = float(hh.max() - entry)

    def hit_first(thr: float) -> float:
        t_fav = t_adv = None
        for i in range(len(hh)):
            if direction > 0:
                fav = hh[i] >= entry + thr
                adv = ll[i] <= entry - thr
            else:
                fav = ll[i] <= entry - thr
                adv = hh[i] >= entry + thr
            if fav and adv:
                return np.nan
            if fav and t_fav is None:
                t_fav = i
            if adv and t_adv is None:
                t_adv = i
            if t_fav is not None and t_adv is not None:
                break
        if t_fav is not None and (t_adv is None or t_fav < t_adv):
            return 1.0
        if t_adv is not None and (t_fav is None or t_adv < t_fav):
            return 0.0
        return np.nan

    return {
        "fwd": fwd,
        "fwd_onr": fwd / onr if onr > 0 else np.nan,
        "mfe": mfe,
        "mae": mae,
        "mfe_gt_mae": 1.0 if mfe > mae else 0.0,
        "hit_struct": hit_first(STRUCT_FRAC * onr),
        "hit1R": hit_first(DISP_ONR * onr),
    }


def main() -> None:
    print("=== Reactive Opportunity Capture (frozen HIGH, no prediction) ===", flush=True)
    print(
        f"FROZEN: DISP={DISP_ONR}*ONR; WAIT_MAX={WAIT_MAX}m; first HIGH only; "
        f"STRUCT={STRUCT_FRAC}*ONR; ARM=vol_expansion_high",
        flush=True,
    )

    df = load_nq()
    print("Building day context...", flush=True)
    ctx_df = build_day_context(df)
    ctx_map = {r["session_date"]: r for _, r in ctx_df.iterrows()}

    rows: list[dict] = []
    n_days = 0
    n_high = 0
    n_reactive = 0
    n_blind = 0

    for sd, g in df.groupby("session_date", sort=True):
        ctx = ctx_map.get(sd)
        if ctx is None:
            continue
        onr = float(ctx["onr"])
        if onr <= 0:
            continue
        rth = g[(g["ny_min"] >= NY_OPEN) & (g["ny_min"] < 16 * 60)].reset_index(drop=True)
        if len(rth) < 120:
            continue
        n_days += 1
        year = int(rth.iloc[0]["year"])
        split = split_of(year)
        o930 = float(ctx["open_930"])

        o = rth["open"].to_numpy(float)
        h = rth["high"].to_numpy(float)
        l = rth["low"].to_numpy(float)
        c = rth["close"].to_numpy(float)
        ny = rth["ny_min"].to_numpy(int)
        idx = {int(m): i for i, m in enumerate(ny)}

        # First HIGH in ARM window
        T0 = None
        T0_off = None
        for off in ARM_OFFSETS:
            T = NY_OPEN + off
            if T not in idx:
                continue
            j = idx[T]
            rth_to_T = rth[rth["ny_min"] <= T]
            st = state_at_T(rth_to_T, ctx, T)
            if st is None:
                continue
            if is_high(float(st["rng_onr"]), off):
                T0 = T
                T0_off = off
                j0 = j
                break
        if T0 is None:
            continue
        n_high += 1

        disp = DISP_ONR * onr
        ref = float(c[j0])
        blind_dir = 0
        if abs(ref - o930) >= 0.25:
            blind_dir = 1 if ref > o930 else -1

        # Blind entry: next bar after T0
        after0 = np.where(ny > T0)[0]
        if len(after0) < max(FWD_HORIZONS) + 2:
            continue
        blind_entry_i = int(after0[0])

        # Reactive: scan up to WAIT_MAX bars after T0 for displacement
        scan_end = min(j0 + WAIT_MAX, len(c) - max(FWD_HORIZONS) - 2)
        if scan_end <= j0:
            continue
        touch = first_touch_dir_continue(h[j0 + 1 : scan_end + 1], l[j0 + 1 : scan_end + 1], ref, disp)
        reactive_ok = touch is not None
        if reactive_ok:
            ti, rdir = touch
            # ti is offset within scan array starting at j0+1
            trigger_i = j0 + 1 + ti
            # enter next bar after trigger bar
            reactive_entry_i = trigger_i + 1
            if reactive_entry_i + max(FWD_HORIZONS) >= len(c):
                reactive_ok = False
            else:
                n_reactive += 1
                wait_min = int(ny[trigger_i] - T0)
        else:
            rdir = 0
            reactive_entry_i = -1
            wait_min = np.nan

        if blind_dir != 0:
            n_blind += 1

        row: dict[str, Any] = {
            "session_date": str(sd),
            "year": year,
            "split": split,
            "T0_offset": int(T0_off),
            "T0_ny": int(T0),
            "onr": onr,
            "disp": disp,
            "blind_dir": blind_dir,
            "reactive_ok": int(reactive_ok),
            "reactive_dir": int(rdir) if reactive_ok else 0,
            "wait_min": wait_min,
            "same_dir": int(reactive_ok and blind_dir != 0 and rdir == blind_dir),
            "flip_dir": int(reactive_ok and blind_dir != 0 and rdir == -blind_dir),
        }

        for label, entry_i, direction, active in (
            ("blind", blind_entry_i, blind_dir, blind_dir != 0),
            ("reactive", reactive_entry_i, rdir if reactive_ok else 0, reactive_ok),
        ):
            for H in FWD_HORIZONS:
                if not active:
                    for k in ("fwd", "fwd_onr", "mfe", "mae", "mfe_gt_mae", "hit_struct", "hit1R"):
                        row[f"{label}_{k}_{H}"] = np.nan
                    continue
                pm = signed_path(o, h, l, c, entry_i, direction, H, onr)
                for k, v in pm.items():
                    row[f"{label}_{k}_{H}"] = v

        rows.append(row)
        if n_days % 500 == 0:
            print(f"  days={n_days} high={n_high} reactive={n_reactive}", flush=True)

    panel = pd.DataFrame(rows)
    panel.to_parquet(art("nq_roc_panel.parquet"), index=False)
    print(
        f"Panel days={len(panel)} high_first={n_high} blind={n_blind} reactive={n_reactive} "
        f"trigger_rate={n_reactive/max(n_high,1):.2%}",
        flush=True,
    )

    # Scoring
    results: list[dict] = []

    def summarize(s: pd.DataFrame, prefix: str, H: int) -> dict[str, float]:
        fwd = s[f"{prefix}_fwd_{H}"].to_numpy(float)
        fwd = fwd[np.isfinite(fwd)]
        if len(fwd) == 0:
            return {"n": 0}
        fonr = s[f"{prefix}_fwd_onr_{H}"].to_numpy(float)
        fonr = fonr[np.isfinite(fonr)]
        mfe_gt = s[f"{prefix}_mfe_gt_mae_{H}"].to_numpy(float)
        hit_s = s[f"{prefix}_hit_struct_{H}"].to_numpy(float)
        hit1 = s[f"{prefix}_hit1R_{H}"].to_numpy(float)
        return {
            "n": int(len(fwd)),
            "win": float(np.mean(fwd > 0)),
            "mean": float(np.mean(fwd)),
            "mean_onr": float(np.mean(fonr)) if len(fonr) else np.nan,
            "median_onr": float(np.median(fonr)) if len(fonr) else np.nan,
            "mfe_gt_mae": float(np.nanmean(mfe_gt)),
            "p_struct": float(np.nanmean(hit_s)),
            "p_hit1R": float(np.nanmean(hit1)),
        }

    for split in ("IS", "Validation", "OOS"):
        base = panel[panel["split"] == split]
        for H in FWD_HORIZONS:
            # Blind on all days with blind_dir
            b = summarize(base[base["blind_dir"] != 0], "blind", H)
            # Reactive on days that triggered
            r = summarize(base[base["reactive_ok"] == 1], "reactive", H)
            # Paired: both available
            both = base[(base["blind_dir"] != 0) & (base["reactive_ok"] == 1)]
            bp = summarize(both, "blind", H)
            rp = summarize(both, "reactive", H)
            # Lift reactive - blind on paired
            lift_win = rp["win"] - bp["win"] if rp.get("n", 0) and bp.get("n", 0) else np.nan
            lift_onr = rp["mean_onr"] - bp["mean_onr"] if rp.get("n", 0) and bp.get("n", 0) else np.nan
            lift_struct = (
                rp["p_struct"] - bp["p_struct"]
                if rp.get("n", 0) and bp.get("n", 0)
                else np.nan
            )

            results.append(
                {
                    "split": split,
                    "horizon": H,
                    "sample": "blind_all",
                    **{f"b_{k}": v for k, v in b.items()},
                }
            )
            results.append(
                {
                    "split": split,
                    "horizon": H,
                    "sample": "reactive_trig",
                    **{f"r_{k}": v for k, v in r.items()},
                }
            )
            results.append(
                {
                    "split": split,
                    "horizon": H,
                    "sample": "paired",
                    "n_paired": int(len(both)),
                    "blind_win": bp.get("win", np.nan),
                    "blind_mean_onr": bp.get("mean_onr", np.nan),
                    "blind_mfe_gt_mae": bp.get("mfe_gt_mae", np.nan),
                    "blind_p_struct": bp.get("p_struct", np.nan),
                    "blind_p_hit1R": bp.get("p_hit1R", np.nan),
                    "react_win": rp.get("win", np.nan),
                    "react_mean_onr": rp.get("mean_onr", np.nan),
                    "react_mfe_gt_mae": rp.get("mfe_gt_mae", np.nan),
                    "react_p_struct": rp.get("p_struct", np.nan),
                    "react_p_hit1R": rp.get("p_hit1R", np.nan),
                    "lift_win": lift_win,
                    "lift_mean_onr": lift_onr,
                    "lift_struct": lift_struct,
                    "trigger_rate": float(base["reactive_ok"].mean()) if len(base) else np.nan,
                    "med_wait": float(base.loc[base["reactive_ok"] == 1, "wait_min"].median())
                    if (base["reactive_ok"] == 1).any()
                    else np.nan,
                    "frac_same_dir": float(both["same_dir"].mean()) if len(both) else np.nan,
                    "frac_flip": float(both["flip_dir"].mean()) if len(both) else np.nan,
                }
            )

    res_df = pd.DataFrame(results)
    res_df.to_csv(art("nq_roc_results.csv"), index=False)

    paired = res_df[res_df["sample"] == "paired"].copy()

    def year_paired(H: int) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for y in (2025, 2026):
            s = panel[(panel["year"] == y) & (panel["blind_dir"] != 0) & (panel["reactive_ok"] == 1)]
            bp = summarize(s, "blind", H)
            rp = summarize(s, "reactive", H)
            out[f"y{y}_n"] = int(len(s))
            out[f"y{y}_b_win"] = bp.get("win", np.nan)
            out[f"y{y}_r_win"] = rp.get("win", np.nan)
            out[f"y{y}_lift_win"] = (
                rp["win"] - bp["win"] if bp.get("n", 0) and rp.get("n", 0) else np.nan
            )
            out[f"y{y}_lift_onr"] = (
                rp["mean_onr"] - bp["mean_onr"] if bp.get("n", 0) and rp.get("n", 0) else np.nan
            )
        return out

    # Promotion: reactive beats blind on paired sample across IS/Val/OOS, multi-horizon, years
    survivors = []
    for H in FWD_HORIZONS:
        cells = {}
        for split in ("IS", "Validation", "OOS"):
            row = paired[(paired["horizon"] == H) & (paired["split"] == split)]
            if len(row) == 0:
                cells = None
                break
            cells[split] = row.iloc[0]
        if cells is None:
            continue
        is_r, v_r, o_r = cells["IS"], cells["Validation"], cells["OOS"]
        if int(is_r["n_paired"]) < 80 or int(v_r["n_paired"]) < 40 or int(o_r["n_paired"]) < 30:
            continue
        yrs = year_paired(H)

        # Reactive must be economically meaningful itself
        react_ok = (
            float(is_r["react_win"]) >= 0.52
            and float(v_r["react_win"]) >= 0.50
            and float(o_r["react_win"]) >= 0.50
            and float(is_r["react_mean_onr"]) > 0
            and float(v_r["react_mean_onr"]) > 0
            and float(o_r["react_mean_onr"]) > 0
        )
        # And beat blind on win OR mean_onr stably
        beat_blind = (
            float(is_r["lift_win"]) >= 0.02
            and float(v_r["lift_win"]) > 0
            and float(o_r["lift_win"]) > 0
            and float(is_r["lift_mean_onr"]) > 0
            and float(v_r["lift_mean_onr"]) > 0
            and float(o_r["lift_mean_onr"]) > 0
        )
        # Path support
        path_ok = (
            float(is_r["react_mfe_gt_mae"]) >= 0.52
            and float(is_r["react_p_struct"]) >= float(is_r["blind_p_struct"])
        )
        y25n, y26n = yrs.get("y2025_n", 0), yrs.get("y2026_n", 0)
        year_ok = (
            y25n >= 20
            and np.isfinite(yrs.get("y2025_lift_win", np.nan))
            and yrs["y2025_lift_win"] > 0
            and yrs.get("y2025_r_win", 0) >= 0.50
        )
        if y26n >= 15:
            year_ok = (
                year_ok
                and np.isfinite(yrs.get("y2026_lift_win", np.nan))
                and yrs["y2026_lift_win"] > -0.02
                and yrs.get("y2026_r_win", 0) >= 0.48
            )

        strong = react_ok and beat_blind and path_ok and year_ok and float(is_r["lift_win"]) >= 0.03
        soft = react_ok and beat_blind and year_ok and (
            float(is_r["lift_win"]) >= 0.015 or float(is_r["lift_mean_onr"]) > 0.01
        )
        if strong or soft:
            survivors.append(
                {
                    "horizon": H,
                    "tier": "strong" if strong else "soft",
                    "IS_n": int(is_r["n_paired"]),
                    "IS_r_win": float(is_r["react_win"]),
                    "IS_b_win": float(is_r["blind_win"]),
                    "IS_lift_win": float(is_r["lift_win"]),
                    "IS_lift_onr": float(is_r["lift_mean_onr"]),
                    "IS_lift_struct": float(is_r["lift_struct"])
                    if np.isfinite(is_r["lift_struct"])
                    else None,
                    "Val_r_win": float(v_r["react_win"]),
                    "Val_lift_win": float(v_r["lift_win"]),
                    "OOS_r_win": float(o_r["react_win"]),
                    "OOS_lift_win": float(o_r["lift_win"]),
                    **yrs,
                }
            )

    strong_n = sum(1 for s in survivors if s["tier"] == "strong")
    soft_n = sum(1 for s in survivors if s["tier"] == "soft")
    multi_h = sum(1 for s in survivors if s["tier"] == "strong")

    if multi_h >= 3:
        verdict = "A"
        verdict_text = (
            "Reactive entry after causal displacement inside HIGH stably beats "
            "blind entry at HIGH activation (multi-horizon)."
        )
        kill = False
    elif strong_n > 0 or soft_n > 0:
        verdict = "B"
        verdict_text = (
            "Weak/inconsistent reactive-vs-blind leftovers; not multi-horizon strong. "
            "Do not promote to strategy yet."
        )
        kill = False  # B is soft interest — not kill whole category like dead families
        # User said if no then question the goal. For B we keep category soft.
    else:
        verdict = "C"
        verdict_text = (
            "Waiting for displacement inside HIGH does NOT improve the conditional path "
            "vs entering at HIGH activation. Reactive opportunity capture fails."
        )
        kill = True

    # IS paired summary table
    is_paired = paired[paired["split"] == "IS"]
    summary = []
    for _, r in is_paired.iterrows():
        summary.append(
            {
                "horizon": int(r["horizon"]),
                "n": int(r["n_paired"]),
                "blind_win": float(r["blind_win"]),
                "react_win": float(r["react_win"]),
                "lift_win": float(r["lift_win"]),
                "blind_mean_onr": float(r["blind_mean_onr"]),
                "react_mean_onr": float(r["react_mean_onr"]),
                "lift_mean_onr": float(r["lift_mean_onr"]),
                "lift_struct": float(r["lift_struct"]) if np.isfinite(r["lift_struct"]) else np.nan,
                "trigger_rate": float(r["trigger_rate"]),
                "med_wait": float(r["med_wait"]) if np.isfinite(r["med_wait"]) else np.nan,
                "frac_flip": float(r["frac_flip"]) if np.isfinite(r["frac_flip"]) else np.nan,
            }
        )

    meta = {
        "stage": "reactive_opportunity_capture",
        "category": "reactive_opportunity_capture",
        "verdict": verdict,
        "kill_category": kill,
        "verdict_text": verdict_text,
        "frozen": {
            "arm": "vol_expansion_high",
            "disp_onr": DISP_ONR,
            "wait_max": WAIT_MAX,
            "struct_frac": STRUCT_FRAC,
            "first_high_only": True,
            "window": "09:35-11:00",
        },
        "n_strong": strong_n,
        "n_soft": soft_n,
        "n_horizons_strong": multi_h,
        "IS_paired_summary": summary,
        "survivors": survivors,
        "trigger_rate_all": float(panel["reactive_ok"].mean()),
        "n_first_high_days": int(len(panel)),
        "implication_if_C": (
            "Question whether a mechanical 1-2/day NQ strategy is extractable "
            "from this dataset at these horizons. HIGH remains valid opportunity timing."
        ),
    }
    with open(art("nq_roc_report.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, default=str)

    def pct(x: Any) -> str:
        return f"{100 * x:.1f}%" if isinstance(x, (int, float)) and np.isfinite(x) else "—"

    def pp(x: Any) -> str:
        return f"{100 * x:+.1f}pp" if isinstance(x, (int, float)) and np.isfinite(x) else "—"

    md = []
    md.append("# Reactive Opportunity Capture — Minimal Report")
    md.append("")
    md.append(f"**Classification: `{verdict}`** — {verdict_text}")
    md.append("")
    md.append(
        "Not a predictive directional family. Frozen HIGH only. "
        f"DISP=`{DISP_ONR}·ONR`, WAIT_MAX=`{WAIT_MAX}m`, first HIGH in 09:35–11:00."
    )
    md.append("")
    md.append(
        f"First-HIGH days: {len(panel)} · Trigger rate: {pct(panel['reactive_ok'].mean())} · "
        f"Strong horizons: {strong_n} · Soft: {soft_n}"
    )
    md.append("")
    md.append("## IS paired: Blind @ HIGH vs Reactive after displacement")
    md.append("")
    md.append("| H | n | Blind win | React win | Δwin | Blind ONR | React ONR | ΔONR | Δstruct | wait | flip |")
    md.append("|---|---|-----------|-----------|------|-----------|-----------|------|---------|------|------|")
    for s in summary:
        md.append(
            f"| {s['horizon']} | {s['n']} | {pct(s['blind_win'])} | {pct(s['react_win'])} | "
            f"{pp(s['lift_win'])} | {s['blind_mean_onr']:+.3f} | {s['react_mean_onr']:+.3f} | "
            f"{s['lift_mean_onr']:+.3f} | {pp(s['lift_struct'])} | "
            f"{s['med_wait']:.0f}m | {pct(s['frac_flip'])} |"
        )
    md.append("")
    md.append("## Val / OOS paired lift (win)")
    md.append("")
    md.append("| H | IS Δwin | Val Δwin | OOS Δwin | Val react | OOS react |")
    md.append("|---|---------|----------|----------|-----------|-----------|")
    for H in FWD_HORIZONS:
        cells = []
        ok = True
        for split in ("IS", "Validation", "OOS"):
            row = paired[(paired["horizon"] == H) & (paired["split"] == split)]
            if len(row) == 0:
                ok = False
                break
            cells.append(row.iloc[0])
        if not ok:
            continue
        md.append(
            f"| {H} | {pp(cells[0]['lift_win'])} | {pp(cells[1]['lift_win'])} | "
            f"{pp(cells[2]['lift_win'])} | {pct(cells[1]['react_win'])} | {pct(cells[2]['react_win'])} |"
        )
    md.append("")
    md.append("## Survivors")
    md.append("")
    if not survivors:
        md.append("None.")
    else:
        md.append("| Tier | H | IS n | React | Blind | Δwin | ΔONR | Val Δ | OOS Δ | 2025 Δ | 2026 Δ |")
        md.append("|------|---|------|-------|-------|------|------|-------|-------|--------|--------|")
        for s in survivors:
            md.append(
                f"| {s['tier']} | {s['horizon']} | {s['IS_n']} | {pct(s['IS_r_win'])} | "
                f"{pct(s['IS_b_win'])} | {pp(s['IS_lift_win'])} | {s['IS_lift_onr']:+.3f} | "
                f"{pp(s['Val_lift_win'])} | {pp(s['OOS_lift_win'])} | "
                f"{pp(s.get('y2025_lift_win'))} | {pp(s.get('y2026_lift_win'))} |"
            )
    md.append("")
    md.append(f"## Final: **{verdict}**")
    md.append("")
    if verdict == "A":
        md.append(
            "Reactive displacement entry inside HIGH is a candidate engine. "
            "Next: execution realism / 1–2/day economics — still no dead-feature rescue."
        )
    elif verdict == "B":
        md.append(
            "Soft signal only. Do not build a strategy. Optionally inspect one soft cell; "
            "do not add filters."
        )
    else:
        md.append(
            "**Reactive opportunity capture fails.** Combined with killed predictive families, "
            "seriously question whether a mechanical 1–2 trade/day NQ directional strategy "
            "is extractable from this dataset at these horizons."
        )
        md.append("")
        md.append("Still valid: frozen HIGH as **opportunity/activity timing**.")
    md.append("")
    (art("nq_roc_report.md")).write_text("\n".join(md), encoding="utf-8")

    # Pivot doc
    pivot = art("research_pivot_reactive_opportunity.md")
    pivot.write_text(
        "\n".join(
            [
                "# Research Pivot — Reactive Opportunity Capture",
                "",
                "**Date:** 2026-09-05",
                "**Status:** ACTIVE after terminal kill of predictive directional families",
                "",
                "## Stopped",
                "",
                "No more predictive directional families (OHLC, options, macro, …).",
                "",
                "## New objective",
                "",
                "Can we monetize HIGH opportunity **without predicting direction beforehand**?",
                "",
                "```text",
                "HIGH / ARM",
                "    ↓",
                "wait for observable displacement",
                "    ↓",
                "direction revealed",
                "    ↓",
                "reactive entry",
                "```",
                "",
                f"## ROC result: **{verdict}** (kill_category={kill})",
                "",
                verdict_text,
                "",
                "Frozen HIGH remains opportunity timing only.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(f"VERDICT: {verdict} kill_category={kill}", flush=True)
    print(f"strong/soft horizons: {strong_n}/{soft_n}", flush=True)


if __name__ == "__main__":
    main()
