"""Independent lookahead / timestamp audit for VSA Step 2 events."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from constants import MIN_SEPARATION, ND_CLOSE_FRAC_MAX


def audit_events(events: pd.DataFrame, bars: pd.DataFrame) -> dict:
    checks: dict[str, dict] = {}

    def ok(name: str, passed: bool, detail: str = "") -> None:
        checks[name] = {"pass": bool(passed), "detail": detail}

    if len(events) == 0:
        ok("nonempty", False, "zero events — power/audit note only")
        return {"checks": checks, "n_events": 0, "all_pass": False}

    te = events["t_event"].to_numpy(np.int64)
    tc = events["t_confirmation"].to_numpy(np.int64)
    ok("t_event_lt_t_confirmation", bool(np.all(te < tc)), f"bad={(te >= tc).sum()}")
    ok("confirm_is_event_plus_1", bool(np.all(tc == te + 1)), f"bad={(tc != te + 1).sum()}")

    # Class integrity
    for cls, need_bg, need_nd in (("C", True, True), ("A", False, True), ("B", True, False)):
        sub = events[events["event_class"] == cls]
        if len(sub) == 0:
            ok(f"{cls}_present_or_empty", True, "empty")
            continue
        bg = sub["bg_weak"].to_numpy(bool)
        nd = sub["nd_morph"].to_numpy(bool)
        ok(f"{cls}_bg_flag", bool(np.all(bg == need_bg)), f"n={len(sub)}")
        ok(f"{cls}_nd_flag", bool(np.all(nd == need_nd)), f"n={len(sub)}")
        ok(f"{cls}_confirm_ok", bool(sub["confirm_ok"].all()), f"n={len(sub)}")

    # Mutual exclusivity of classes at same t_event
    if events["t_event"].duplicated().any():
        ok("unique_t_event", False, f"dups={int(events['t_event'].duplicated().sum())}")
    else:
        ok("unique_t_event", True)

    # Separation: sorted t_event diffs >= MIN_SEPARATION (except first)
    order = np.sort(te)
    if len(order) >= 2:
        diffs = np.diff(order)
        ok(
            "min_separation",
            bool(np.all(diffs >= MIN_SEPARATION)),
            f"min_diff={int(diffs.min())}",
        )
    else:
        ok("min_separation", True, "n<2")

    # Same segment event/confirm; confirm is down-bar; event is up-bar
    same_seg = []
    event_up = []
    confirm_down = []
    nd_close_ok = []
    for r in events.itertuples(index=False):
        te_i = int(r.t_event)
        tc_i = int(r.t_confirmation)
        same_seg.append(int(bars["segment_id"].iat[te_i]) == int(bars["segment_id"].iat[tc_i]))
        event_up.append(bool(bars["up_bar"].iat[te_i]))
        confirm_down.append(bool(bars["down_bar"].iat[tc_i]))
        if r.event_class in ("A", "C"):
            cf = float(bars["close_frac"].iat[te_i])
            nd_close_ok.append(np.isfinite(cf) and cf <= ND_CLOSE_FRAC_MAX)
        else:
            nd_close_ok.append(True)
    ok("event_confirm_same_segment", bool(all(same_seg)), f"bad={len(same_seg) - sum(same_seg)}")
    ok("event_is_up_bar", bool(all(event_up)), f"bad={len(event_up) - sum(event_up)}")
    ok("confirm_is_down_bar", bool(all(confirm_down)), f"bad={len(confirm_down) - sum(confirm_down)}")
    ok("ND_close_frac_le_050", bool(all(nd_close_ok)), f"bad={len(nd_close_ok) - sum(nd_close_ok)}")

    # No signed volume / CVD columns; no outcome columns
    banned_sub = ("return_pts", "leave_", "sharpe", "pnl", "mfe", "mae", "cvd", "signed_vol", "delta")
    banned = [c for c in events.columns if any(x in c.lower() for x in banned_sub)]
    ok("no_outcome_or_signed_columns", len(banned) == 0, f"banned={banned}")

    # Index bounds
    nb = len(bars)
    ok(
        "indices_in_range",
        bool(np.all((te >= 0) & (tc >= 0) & (te < nb) & (tc < nb))),
        f"n_bars={nb}",
    )

    # Causal medians: event bar must have finite med_spread/med_vol
    med_ok = []
    for t in te:
        med_ok.append(
            np.isfinite(bars["med_spread"].iat[int(t)]) and np.isfinite(bars["med_vol"].iat[int(t)])
        )
    ok("event_has_causal_medians", bool(all(med_ok)), f"bad={len(med_ok) - sum(med_ok)}")

    # t_sequence_complete == t_confirmation for all emitted events
    ok(
        "sequence_complete_eq_confirm",
        bool(np.all(events["t_sequence_complete"].to_numpy(np.int64) == tc)),
    )

    all_pass = all(v["pass"] for v in checks.values())
    return {"checks": checks, "n_events": int(len(events)), "all_pass": all_pass}


def write_audit(report: dict, path: Path) -> None:
    path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
