"""
NQ Multi-session Structural Opportunity Map (Phase A)

Sessions: Asia / London / NY_AM / NY_PM (frozen clock in common.sessions).
Asks only: can causal intra-session activity states reprice
P(structural residual >= frac * psr within H) vs same session-TOD baseline?

NO entries. NO targets. NO direction. NO threshold mining on forward resolve.
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

_CODE = Path(__file__).resolve().parent
_ROOT = _CODE.parents[2]  # strategies/<dossier>/code -> repo root
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from common.nq_session import art, load_nq, rate_of
from common.sessions import (
    SESSION_DECISION_OFFSETS,
    SESSION_ORDER,
    SESSION_START,
    bars_in_session,
    build_session_facts,
    decision_ny_min,
    state_at_T_session,
)

warnings.filterwarnings("ignore", category=FutureWarning)

OPP_HORIZONS = (10, 15, 20, 30, 45)
STRUCT_FRACS = (0.15, 0.25, 0.35)
PRIMARY_FRAC = 0.25

LOW_STATES = (
    "quiet_wait",
    "vol_expansion_low",
    "weak_dir_move",
    "low_local_vol",
    "slow_move",
)
HIGH_STATES = (
    "vol_expansion_high",
    "strong_dir_move",
    "fast_move",
    "fast_and_expanded",
    "strong_and_persistent",
    "high_local_vol",
)

PAIR_DEFS = (
    ("quiet_wait", "fast_and_expanded"),
    ("quiet_wait", "vol_expansion_high"),
    ("vol_expansion_low", "vol_expansion_high"),
    ("low_local_vol", "high_local_vol"),
    ("weak_dir_move", "strong_dir_move"),
)


def structural_resolved_session(
    sess_full: pd.DataFrame,
    T_ny: int,
    psr: float,
    frac: float,
    horizons: tuple[int, ...],
    session: str,
) -> dict[str, float] | None:
    """Unsigned structural opportunity inside the same session after T."""
    if not np.isfinite(psr) or psr <= 0:
        return None
    if session == "ASIA":
        ord_T = T_ny if T_ny >= SESSION_START else T_ny + 24 * 60
        ord_key = np.where(
            sess_full["ny_min"].to_numpy(np.int64) >= SESSION_START,
            sess_full["ny_min"].to_numpy(np.int64),
            sess_full["ny_min"].to_numpy(np.int64) + 24 * 60,
        )
        after = sess_full.loc[ord_key > ord_T].reset_index(drop=True)
    else:
        after = sess_full[sess_full["ny_min"] > T_ny].reset_index(drop=True)

    need = max(horizons)
    if len(after) < need:
        return None
    entry = float(after.iloc[0]["open"])
    thr = frac * psr
    highs = after["high"].to_numpy(float)
    lows = after["low"].to_numpy(float)
    out: dict[str, float] = {"entry": entry, "thr_pts": thr}
    for H in horizons:
        mfe = float(highs[:H].max() - entry)
        mae = float(entry - lows[:H].min())
        mx = max(mfe, mae)
        out[f"max_exc_{H}"] = mx
        out[f"max_exc_psr_{H}"] = mx / psr
        out[f"resolved_f{frac:g}_{H}"] = 1.0 if mx >= thr else 0.0
        already = abs(float(sess_full.loc[sess_full["ny_min"] == T_ny, "close"].iloc[-1]) - entry)
        # share of eventual H-excursion already present at T close vs entry open approx
        t_hit = np.nan
        run_max = 0.0
        for i in range(H):
            run_max = max(run_max, highs[i] - entry, entry - lows[i])
            if run_max >= thr:
                t_hit = float(i + 1)
                break
        out[f"t_resolve_f{frac:g}_{H}"] = t_hit
        out[f"share_pre_{H}"] = float(min(already / mx, 1.0)) if mx > 0 else np.nan
    return out


def conditions_for(
    sub: pd.DataFrame,
    thresholds: dict[str, dict[str, float]],
) -> dict[str, pd.Series]:
    th = thresholds
    c: dict[str, pd.Series] = {}
    if "rng_psr" in th:
        c["vol_expansion_high"] = sub["rng_psr"] >= th["rng_psr"]["p66"]
        c["vol_expansion_low"] = sub["rng_psr"] <= th["rng_psr"]["p33"]
    if "abs_move_psr" in th:
        c["strong_dir_move"] = (sub["abs_move_psr"] >= th["abs_move_psr"]["p66"]) & (
            sub["dir_sign"] != 0
        )
        c["weak_dir_move"] = sub["abs_move_psr"] <= th["abs_move_psr"]["p33"]
    if "persist_frac" in th:
        c["high_persistence"] = (sub["persist_frac"] >= th["persist_frac"]["p66"]) & (
            sub["dir_sign"] != 0
        )
        c["low_persistence"] = (sub["persist_frac"] <= th["persist_frac"]["p33"]) & (
            sub["dir_sign"] != 0
        )
    if "speed" in th:
        c["fast_move"] = (sub["speed"] >= th["speed"]["p66"]) & (sub["dir_sign"] != 0)
        c["slow_move"] = sub["speed"] <= th["speed"]["p33"]
    if "vol_unit_psr" in th:
        c["high_local_vol"] = sub["vol_unit_psr"] >= th["vol_unit_psr"]["p66"]
        c["low_local_vol"] = sub["vol_unit_psr"] <= th["vol_unit_psr"]["p33"]
    if "strong_dir_move" in c and "high_persistence" in c:
        c["strong_and_persistent"] = c["strong_dir_move"] & c["high_persistence"]
    if "fast_move" in c and "vol_expansion_high" in c:
        c["fast_and_expanded"] = c["fast_move"] & c["vol_expansion_high"]
    if "vol_expansion_low" in c and "weak_dir_move" in c:
        c["quiet_wait"] = c["vol_expansion_low"] & c["weak_dir_move"]
    return c


def pct(x: Any) -> str:
    return f"{100 * x:.1f}%" if isinstance(x, (int, float)) and np.isfinite(x) else "—"


def pp(x: Any) -> str:
    return f"{100 * x:+.1f}pp" if isinstance(x, (int, float)) and np.isfinite(x) else "—"


def main() -> None:
    print("=== NQ Multi-session Opportunity Map (Phase A) ===", flush=True)
    df = load_nq()
    print(f"Bars: {len(df):,}", flush=True)

    print("Building session facts...", flush=True)
    facts = build_session_facts(df)
    facts_path = art("nq_multi_sess_facts.parquet")
    facts.to_parquet(facts_path, index=False)
    print(f"Session facts: {len(facts)} -> {facts_path}", flush=True)

    facts_map = {
        (r["session_date"], r["session"]): r for _, r in facts.iterrows()
    }

    print("Indexing session bars...", flush=True)
    sess_bars: dict[tuple, pd.DataFrame] = {}
    for sd, g in df.groupby("session_date", sort=False):
        for name in SESSION_ORDER:
            key = (sd, name)
            if key not in facts_map:
                continue
            bars = bars_in_session(g, name)
            if len(bars) >= 40:
                sess_bars[key] = bars
    print(f"Session day-slices: {len(sess_bars)}", flush=True)

    rows: list[dict] = []
    n_keys = 0
    for (sd, name), bars in sess_bars.items():
        fr = facts_map[(sd, name)]
        psr = float(fr["psr"])
        if not np.isfinite(psr) or psr <= 0:
            continue
        session_open = float(fr["open"])
        year = int(fr["year"])
        split = str(fr["split"])
        offsets = SESSION_DECISION_OFFSETS[name]
        n_keys += 1
        for off in offsets:
            T = decision_ny_min(name, off)
            if T not in set(bars["ny_min"].astype(int).tolist()):
                continue
            st = state_at_T_session(
                bars,
                session=name,
                T_ny=T,
                session_open=session_open,
                psr=psr,
            )
            if st is None:
                continue
            packed: dict[str, float] = {}
            ok = True
            for frac in STRUCT_FRACS:
                out = structural_resolved_session(
                    bars, T, psr, frac, OPP_HORIZONS, name
                )
                if out is None:
                    ok = False
                    break
                packed.update(out)
            if not ok:
                continue
            # already-moving: abs move from session open at T vs structural thr
            already_moving = float(st["abs_move_psr"] >= PRIMARY_FRAC)
            rows.append(
                {
                    "session_date": str(sd),
                    "session": name,
                    "year": year,
                    "dow": int(fr["dow"]),
                    "split": split,
                    "T_offset": off,
                    "T_ny": T,
                    "already_moving": already_moving,
                    **st,
                    **packed,
                }
            )
        if n_keys % 800 == 0:
            print(f"  processed {n_keys} session-days, panel={len(rows)}", flush=True)

    panel = pd.DataFrame(rows)
    panel_path = art("nq_multi_sess_opp_panel.parquet")
    panel.to_parquet(panel_path, index=False)
    print(f"Panel rows: {len(panel)} -> {panel_path}", flush=True)
    if panel.empty:
        raise SystemExit("Empty panel — check data / session filters")

    # IS terciles per (session, T_offset, feature)
    features = [
        "rng_psr",
        "abs_move_psr",
        "path_psr",
        "speed",
        "persist_frac",
        "vol_unit_psr",
    ]
    thresholds: dict[str, dict[int, dict[str, dict[str, float]]]] = {}
    is_p = panel[panel["split"] == "IS"]
    for sess in SESSION_ORDER:
        thresholds[sess] = {}
        for off in SESSION_DECISION_OFFSETS[sess]:
            thresholds[sess][off] = {}
            sub = is_p[(is_p["session"] == sess) & (is_p["T_offset"] == off)]
            for feat in features:
                s = sub[feat].dropna()
                if len(s) < 80:
                    continue
                thresholds[sess][off][feat] = {
                    "p33": float(s.quantile(0.33)),
                    "p66": float(s.quantile(0.66)),
                }

    thr_path = art("nq_multi_sess_opp_thresholds_IS.json")
    with open(thr_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "state_terciles": {
                    sess: {str(k): v for k, v in offs.items()}
                    for sess, offs in thresholds.items()
                },
                "structural_frac_primary": PRIMARY_FRAC,
                "structural_fracs_sensitivity": list(STRUCT_FRACS),
                "note": "STRUCT_FRAC pre-specified; terciles IS-only per session×offset",
            },
            f,
            indent=2,
        )
    print(f"Thresholds -> {thr_path}", flush=True)

    results: list[dict[str, Any]] = []
    for sess in SESSION_ORDER:
        for off in SESSION_DECISION_OFFSETS[sess]:
            sub = panel[(panel["session"] == sess) & (panel["T_offset"] == off)].copy()
            if len(sub) < 150:
                continue
            th = thresholds.get(sess, {}).get(off, {})
            if not th:
                continue
            conds = conditions_for(sub, th)
            conds = {"UNCONDITIONAL": pd.Series(True, index=sub.index), **conds}
            for cname, mask in conds.items():
                for split in ("IS", "Validation", "OOS", "ALL"):
                    base = sub if split == "ALL" else sub[sub["split"] == split]
                    m = mask.reindex(base.index).fillna(False)
                    cond = base.loc[m.to_numpy()]
                    unc = base
                    if cname != "UNCONDITIONAL" and len(cond) < 40:
                        continue
                    if len(cond) < 20:
                        continue
                    for frac in STRUCT_FRACS:
                        for H in OPP_HORIZONS:
                            col = f"resolved_f{frac:g}_{H}"
                            if col not in cond.columns:
                                continue
                            cr = rate_of(cond[col])
                            ur = rate_of(unc[col])
                            if not cr["n"] or not ur["n"]:
                                continue
                            results.append(
                                {
                                    "session": sess,
                                    "condition": cname,
                                    "regime": (
                                        "LOW"
                                        if cname in LOW_STATES
                                        else (
                                            "HIGH"
                                            if cname in HIGH_STATES
                                            else "OTHER"
                                        )
                                    ),
                                    "T_offset": off,
                                    "horizon": H,
                                    "frac": frac,
                                    "split": split,
                                    "n": int(len(cond)),
                                    "n_unc": int(len(unc)),
                                    "rate": float(len(cond) / max(len(unc), 1)),
                                    "p_resolve": cr["rate"],
                                    "unc_p_resolve": ur["rate"],
                                    "delta": cr["rate"] - ur["rate"],
                                    "mean_already_moving": float(
                                        np.nanmean(cond["already_moving"].to_numpy(float))
                                    ),
                                    "mean_share_pre": float(
                                        np.nanmean(cond[f"share_pre_{H}"].to_numpy(float))
                                    )
                                    if f"share_pre_{H}" in cond.columns
                                    else np.nan,
                                }
                            )

    res_df = pd.DataFrame(results)
    res_path = art("nq_multi_sess_opp_results.csv")
    res_df.to_csv(res_path, index=False)
    print(f"Result rows: {len(res_df)} -> {res_path}", flush=True)

    def slice_metrics(
        sess: str, cname: str, off: int, H: int, frac: float
    ) -> dict[str, Any]:
        out: dict[str, Any] = {
            "session": sess,
            "condition": cname,
            "T_offset": off,
            "horizon": H,
            "frac": frac,
        }
        for split in ("IS", "Validation", "OOS"):
            s = res_df[
                (res_df["session"] == sess)
                & (res_df["condition"] == cname)
                & (res_df["T_offset"] == off)
                & (res_df["horizon"] == H)
                & (res_df["frac"] == frac)
                & (res_df["split"] == split)
            ]
            if len(s) == 0:
                out[f"{split}_n"] = 0
                out[f"{split}_p"] = np.nan
                out[f"{split}_delta"] = np.nan
                continue
            r = s.iloc[0]
            out[f"{split}_n"] = int(r["n"])
            out[f"{split}_p"] = float(r["p_resolve"])
            out[f"{split}_delta"] = float(r["delta"])
            out[f"{split}_already"] = float(r["mean_already_moving"])
            out[f"{split}_share_pre"] = float(r["mean_share_pre"])
        return out

    def year_rates(
        sess: str, cname: str, off: int, H: int, frac: float
    ) -> dict[str, Any]:
        sub = panel[
            (panel["session"] == sess)
            & (panel["T_offset"] == off)
            & (panel["year"].isin([2025, 2026]))
        ].copy()
        out: dict[str, Any] = {
            "y2025": np.nan,
            "y2025_n": 0,
            "y2026": np.nan,
            "y2026_n": 0,
            "y2025_delta": np.nan,
            "y2026_delta": np.nan,
        }
        if len(sub) == 0:
            return out
        th = thresholds.get(sess, {}).get(off, {})
        conds = conditions_for(sub, th) if th else {}
        col = f"resolved_f{frac:g}_{H}"
        unc25 = rate_of(sub.loc[sub["year"] == 2025, col])
        unc26 = rate_of(sub.loc[sub["year"] == 2026, col])
        if cname == "UNCONDITIONAL":
            out["y2025"] = unc25["rate"]
            out["y2025_n"] = unc25["n"]
            out["y2026"] = unc26["rate"]
            out["y2026_n"] = unc26["n"]
            out["y2025_delta"] = 0.0
            out["y2026_delta"] = 0.0
            return out
        if cname not in conds:
            return out
        mask = conds[cname]
        hit = sub.loc[mask.reindex(sub.index).fillna(False).to_numpy()]
        for y, unc in ((2025, unc25), (2026, unc26)):
            hy = hit[hit["year"] == y]
            rr = rate_of(hy[col])
            out[f"y{y}"] = rr["rate"]
            out[f"y{y}_n"] = rr["n"]
            out[f"y{y}_delta"] = (
                rr["rate"] - unc["rate"] if rr["n"] and unc["n"] else np.nan
            )
        return out

    candidates: list[dict[str, Any]] = []
    is_rows = res_df[
        (res_df["split"] == "IS")
        & (res_df["condition"] != "UNCONDITIONAL")
        & (res_df["frac"] == PRIMARY_FRAC)
        & (res_df["regime"].isin(["LOW", "HIGH"]))
    ]
    for _, r in is_rows.iterrows():
        sess = str(r["session"])
        cname = str(r["condition"])
        off, H = int(r["T_offset"]), int(r["horizon"])
        regime = str(r["regime"])
        if int(r["n"]) < 80:
            continue
        met = slice_metrics(sess, cname, off, H, PRIMARY_FRAC)
        yrs = year_rates(sess, cname, off, H, PRIMARY_FRAC)
        is_d, v_d, o_d = met["IS_delta"], met["Validation_delta"], met["OOS_delta"]
        if not all(isinstance(x, (int, float)) and np.isfinite(x) for x in (is_d, v_d, o_d)):
            continue
        if regime == "LOW":
            sign_ok_is = is_d <= -0.05
            sign_ok_vo = v_d < 0 and o_d < 0
            soft_is = is_d <= -0.03
        else:
            sign_ok_is = is_d >= 0.05
            sign_ok_vo = v_d > 0 and o_d > 0
            soft_is = is_d >= 0.03
        y25_d, y26_d = yrs.get("y2025_delta"), yrs.get("y2026_delta")
        y25_n, y26_n = yrs.get("y2025_n", 0), yrs.get("y2026_n", 0)
        year_sign_ok = (
            isinstance(y25_d, (int, float))
            and isinstance(y26_d, (int, float))
            and np.isfinite(y25_d)
            and np.isfinite(y26_d)
            and y25_n >= 20
            and y26_n >= 20
            and (
                (regime == "LOW" and y25_d < 0 and y26_d < 0)
                or (regime == "HIGH" and y25_d > 0 and y26_d > 0)
            )
        )
        year_material = (
            isinstance(y25_d, (int, float))
            and isinstance(y26_d, (int, float))
            and abs(y25_d) >= 0.03
            and abs(y26_d) >= 0.03
        )
        strong = (
            sign_ok_is
            and sign_ok_vo
            and abs(is_d) >= 0.08
            and abs(v_d) >= 0.04
            and abs(o_d) >= 0.04
            and year_sign_ok
            and year_material
            and met["Validation_n"] >= 40
            and met["OOS_n"] >= 30
        )
        soft = (
            soft_is
            and sign_ok_vo
            and year_sign_ok
            and met["Validation_n"] >= 30
            and met["OOS_n"] >= 25
        )
        if strong or soft:
            candidates.append(
                {
                    **met,
                    **yrs,
                    "regime": regime,
                    "tier": "strong" if strong else "soft",
                    "score": abs(is_d),
                }
            )

    candidates.sort(
        key=lambda x: (
            0 if x["tier"] == "strong" else 1,
            x["session"],
            -x["score"],
        )
    )
    cand_df = pd.DataFrame(candidates) if candidates else pd.DataFrame()
    cand_path = art("nq_multi_sess_opp_candidates.csv")
    cand_df.to_csv(cand_path, index=False)

    # Clock stability per (session, condition, H)
    stability: list[dict[str, Any]] = []
    if len(cand_df):
        for (sess, cname, H, regime), g in cand_df.groupby(
            ["session", "condition", "horizon", "regime"]
        ):
            offs = sorted(g["T_offset"].unique().tolist())
            strong_offs = sorted(g.loc[g["tier"] == "strong", "T_offset"].unique().tolist())
            stability.append(
                {
                    "session": sess,
                    "condition": cname,
                    "horizon": int(H),
                    "regime": regime,
                    "n_clocks_soft_or_strong": len(offs),
                    "n_clocks_strong": len(strong_offs),
                    "clocks": offs,
                    "median_IS_delta": float(g["IS_delta"].median()),
                    "median_OOS_delta": float(g["OOS_delta"].median()),
                }
            )
        stability.sort(
            key=lambda x: (-x["n_clocks_strong"], -x["n_clocks_soft_or_strong"], -abs(x["median_IS_delta"]))
        )

    # Discrimination gaps
    discrimination: list[dict[str, Any]] = []
    for sess in SESSION_ORDER:
        for low_c, high_c in PAIR_DEFS:
            for off in SESSION_DECISION_OFFSETS[sess]:
                for H in OPP_HORIZONS:
                    low_m = slice_metrics(sess, low_c, off, H, PRIMARY_FRAC)
                    high_m = slice_metrics(sess, high_c, off, H, PRIMARY_FRAC)
                    if low_m["IS_n"] < 80 or high_m["IS_n"] < 80:
                        continue
                    if low_m["Validation_n"] < 30 or high_m["Validation_n"] < 30:
                        continue
                    if low_m["OOS_n"] < 25 or high_m["OOS_n"] < 25:
                        continue
                    gaps = {}
                    ok = True
                    for split in ("IS", "Validation", "OOS"):
                        lp, hp = low_m[f"{split}_p"], high_m[f"{split}_p"]
                        if not (np.isfinite(lp) and np.isfinite(hp)):
                            ok = False
                            break
                        gaps[f"{split}_gap"] = hp - lp
                    if not ok:
                        continue
                    # year gaps via vol_expansion pair proxy on panel
                    y_ok = True
                    y_gaps = {}
                    for y in (2025, 2026):
                        # reuse year_rates p for high/low absolute resolve
                        yl = year_rates(sess, low_c, off, H, PRIMARY_FRAC)
                        yh = year_rates(sess, high_c, off, H, PRIMARY_FRAC)
                        lp, hp = yl.get(f"y{y}"), yh.get(f"y{y}")
                        ln, hn = yl.get(f"y{y}_n", 0), yh.get(f"y{y}_n", 0)
                        if (
                            not isinstance(lp, (int, float))
                            or not isinstance(hp, (int, float))
                            or not np.isfinite(lp)
                            or not np.isfinite(hp)
                            or ln < 20
                            or hn < 20
                        ):
                            y_ok = False
                            break
                        y_gaps[f"y{y}_gap"] = hp - lp
                    disc_strong = (
                        gaps["IS_gap"] >= 0.08
                        and gaps["Validation_gap"] > 0
                        and gaps["OOS_gap"] > 0
                        and gaps["Validation_gap"] >= 0.04
                        and gaps["OOS_gap"] >= 0.04
                        and y_ok
                        and y_gaps.get("y2025_gap", 0) > 0
                        and y_gaps.get("y2026_gap", 0) > 0
                    )
                    discrimination.append(
                        {
                            "session": sess,
                            "low": low_c,
                            "high": high_c,
                            "T_offset": off,
                            "horizon": H,
                            **gaps,
                            **y_gaps,
                            "tier": "strong" if disc_strong else "soft",
                            "year_ok": y_ok,
                        }
                    )

    disc_df = pd.DataFrame(discrimination) if discrimination else pd.DataFrame()
    strong_disc = (
        disc_df[disc_df["tier"] == "strong"] if len(disc_df) else pd.DataFrame()
    )

    # Promote sessions with multi-clock strong discrimination
    promoted: list[str] = []
    for sess in SESSION_ORDER:
        if len(strong_disc) == 0:
            continue
        g = strong_disc[strong_disc["session"] == sess]
        if len(g) == 0:
            continue
        # multi-clock: >=2 distinct offsets among strong disc cells
        n_clocks = g["T_offset"].nunique()
        if n_clocks >= 2:
            promoted.append(sess)

    # Markdown report
    lines: list[str] = []
    lines.append("# NQ Multi-session Opportunity Map (Phase A)")
    lines.append("")
    lines.append("## Freeze")
    lines.append("")
    lines.append("| Session | Window ET |")
    lines.append("|---------|-----------|")
    lines.append("| ASIA | 18:00–03:00 |")
    lines.append("| LONDON | 03:00–09:30 |")
    lines.append("| NY_AM | 09:30–12:00 |")
    lines.append("| NY_PM | 12:00–16:00 |")
    lines.append("")
    lines.append(f"- Panel rows: **{len(panel):,}**")
    lines.append(f"- Primary STRUCT_FRAC: **{PRIMARY_FRAC}** × psr")
    lines.append(f"- Strong candidates: **{int((cand_df['tier']=='strong').sum()) if len(cand_df) else 0}**")
    lines.append(f"- Soft candidates: **{int((cand_df['tier']=='soft').sum()) if len(cand_df) else 0}**")
    lines.append(f"- Strong discrimination cells: **{len(strong_disc)}**")
    lines.append(f"- Sessions promoted to Phase B: **{', '.join(promoted) if promoted else 'none'}**")
    lines.append("")

    lines.append("## Discrimination (HIGH − LOW), primary frac")
    lines.append("")
    if len(disc_df) == 0:
        lines.append("No discrimination cells met sample floors.")
    else:
        show = disc_df.sort_values(
            ["tier", "IS_gap"], ascending=[True, False]
        ).head(40)
        lines.append(
            "| Session | Pair | T+ | H | IS gap | Val gap | OOS gap | Tier |"
        )
        lines.append("|---------|------|----|---|--------|---------|---------|------|")
        for _, r in show.iterrows():
            lines.append(
                f"| {r['session']} | {r['low']}→{r['high']} | {int(r['T_offset'])} | "
                f"{int(r['horizon'])} | {pp(r['IS_gap'])} | {pp(r['Validation_gap'])} | "
                f"{pp(r['OOS_gap'])} | {r['tier']} |"
            )
    lines.append("")

    lines.append("## Multi-clock stability (candidates)")
    lines.append("")
    if not stability:
        lines.append("No soft/strong candidates.")
    else:
        lines.append("| Session | Condition | H | Regime | Soft/strong clocks | Strong clocks | Med IS Δ | Med OOS Δ |")
        lines.append("|---------|-----------|---|--------|--------------------|---------------|----------|-----------|")
        for s in stability[:40]:
            lines.append(
                f"| {s['session']} | {s['condition']} | {s['horizon']} | {s['regime']} | "
                f"{s['n_clocks_soft_or_strong']} | {s['n_clocks_strong']} | "
                f"{pp(s['median_IS_delta'])} | {pp(s['median_OOS_delta'])} |"
            )
    lines.append("")

    lines.append("## Per-session headline (vol_expansion_high vs quiet_wait @ best IS gap H30)")
    lines.append("")
    lines.append("| Session | Best T+ | IS gap | Val gap | OOS gap | y25 gap | y26 gap |")
    lines.append("|---------|---------|--------|---------|---------|---------|---------|")
    for sess in SESSION_ORDER:
        sub = disc_df[
            (disc_df["session"] == sess)
            & (disc_df["low"] == "quiet_wait")
            & (disc_df["high"] == "vol_expansion_high")
            & (disc_df["horizon"] == 30)
        ] if len(disc_df) else pd.DataFrame()
        if len(sub) == 0:
            lines.append(f"| {sess} | — | — | — | — | — | — |")
            continue
        best = sub.sort_values("IS_gap", ascending=False).iloc[0]
        lines.append(
            f"| {sess} | {int(best['T_offset'])} | {pp(best['IS_gap'])} | "
            f"{pp(best['Validation_gap'])} | {pp(best['OOS_gap'])} | "
            f"{pp(best.get('y2025_gap', np.nan))} | {pp(best.get('y2026_gap', np.nan))} |"
        )
    lines.append("")

    lines.append("## Phase B gate")
    lines.append("")
    if promoted:
        lines.append(
            f"Promote **{', '.join(promoted)}** — multi-clock strong HIGH−LOW discrimination held."
        )
        lines.append("Next: directional continuation/fade and residual economics dossiers (13+).")
    else:
        lines.append(
            "No session met multi-clock strong discrimination with year-stable gaps. "
            "Phase B direction hunt is **blocked** for this pass."
        )
    lines.append("")

    report_md = art("nq_multi_sess_opp_report.md")
    report_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    report_json = {
        "panel_rows": int(len(panel)),
        "n_strong_candidates": int((cand_df["tier"] == "strong").sum()) if len(cand_df) else 0,
        "n_soft_candidates": int((cand_df["tier"] == "soft").sum()) if len(cand_df) else 0,
        "n_strong_discrimination": int(len(strong_disc)),
        "promoted_sessions": promoted,
        "stability_top": stability[:20],
        "discrimination_top": discrimination[:30],
    }
    art("nq_multi_sess_opp_report.json").write_text(
        json.dumps(report_json, indent=2, default=str), encoding="utf-8"
    )
    print(f"Report -> {report_md}", flush=True)
    print(f"Promoted sessions: {promoted or 'none'}", flush=True)


if __name__ == "__main__":
    main()
