"""Independent lookahead / timestamp audit for Step 2 event dataset."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from constants import PIVOT_L, R_MAX, W_CONFIRM


def audit_events(events: pd.DataFrame, bars: pd.DataFrame) -> dict:
    """
    Re-check frozen invariants without recomputing the full detector.

    Returns a dict of pass/fail checks. Does not compute forward returns.
    """
    checks: dict[str, dict] = {}

    def ok(name: str, passed: bool, detail: str = "") -> None:
        checks[name] = {"pass": bool(passed), "detail": detail}

    if len(events) == 0:
        ok("nonempty", False, "zero events — power/audit note only")
        return {"checks": checks, "n_events": 0}

    # Timestamps: t_viol <= t_return; for C, t_return < t_confirm
    t_viol = events["t_viol"].to_numpy(np.int64)
    t_ret = events["t_return"].to_numpy(np.int64)
    ok("t_viol_le_t_return", bool(np.all(t_viol <= t_ret)), f"violations={(t_viol > t_ret).sum()}")

    c = events[events["event_class"] == "C"]
    if len(c):
        tc = c["t_confirm"].to_numpy(np.float64)
        tr = c["t_return"].to_numpy(np.float64)
        ok(
            "C_t_return_lt_t_confirm",
            bool(np.all(np.isfinite(tc) & (tr < tc))),
            f"n_C={len(c)} bad={int((~(np.isfinite(tc) & (tr < tc))).sum())}",
        )
        ok(
            "C_confirm_within_W",
            bool(np.all((tc - tr) <= W_CONFIRM)),
            f"max_lag={float(np.nanmax(tc - tr)) if len(c) else 'na'}",
        )
    else:
        ok("C_t_return_lt_t_confirm", True, "no C events")
        ok("C_confirm_within_W", True, "no C events")

    # Recovery window
    ok(
        "return_within_R_max",
        bool(np.all((t_ret - t_viol) < R_MAX)),
        f"max={(t_ret - t_viol).max()}",
    )

    # Class integrity
    ok(
        "A_has_no_confirm",
        bool(events.loc[events["event_class"] == "A", "t_sequence_complete"].isna().all())
        if (events["event_class"] == "A").any()
        else True,
    )
    ok(
        "C_has_sequence_complete",
        bool(events.loc[events["event_class"] == "C", "t_sequence_complete"].notna().all())
        if (events["event_class"] == "C").any()
        else True,
    )
    ok(
        "C_confirm_ok_true",
        bool(events.loc[events["event_class"] == "C", "confirm_ok"].all())
        if (events["event_class"] == "C").any()
        else True,
    )

    # Tick integrity: tr_low < tr_high for B/C; A may use support/resist
    bc = events[events["event_class"].isin(["B", "C"])]
    if len(bc):
        ok(
            "BC_tr_low_lt_tr_high",
            bool(np.all(bc["tr_low_ticks"].to_numpy() < bc["tr_high_ticks"].to_numpy())),
        )
        # Extreme beyond boundary
        springs = bc[bc["kind"] == "spring"]
        if len(springs):
            ok(
                "spring_E_below_tr_low",
                bool(np.all(springs["E_ticks"].to_numpy() < springs["tr_low_ticks"].to_numpy())),
            )
        else:
            ok("spring_E_below_tr_low", True, "no springs")
        ups = bc[bc["kind"] == "upthrust"]
        if len(ups):
            ok(
                "upthrust_E_above_tr_high",
                bool(np.all(ups["E_ticks"].to_numpy() > ups["tr_high_ticks"].to_numpy())),
            )
        else:
            ok("upthrust_E_above_tr_high", True, "no upthrusts")
    else:
        ok("BC_tr_low_lt_tr_high", True, "no B/C")

    # Segment consistency: viol and return same segment
    if "segment_id" in events.columns:
        # recompute from bars
        same = []
        for r in events.itertuples(index=False):
            same.append(int(bars["segment_id"].iat[int(r.t_viol)]) == int(bars["segment_id"].iat[int(r.t_return)]))
        ok("viol_return_same_segment", bool(all(same)), f"bad={len(same) - sum(same)}")

    # No outcome columns present
    banned = [c for c in events.columns if any(x in c.lower() for x in ("return_pts", "leave_", "sharpe", "pnl", "mfe", "mae"))]
    ok("no_outcome_columns", len(banned) == 0, f"banned={banned}")

    # Index bounds
    n = len(bars)
    ok(
        "indices_in_range",
        bool(
            np.all(t_viol >= 0)
            and np.all(t_ret < n)
            and np.all(t_viol < n)
        ),
    )

    # C: test pivot confirm uses L — test_pivot + L == t_confirm roughly
    if len(c) and "test_pivot" in c.columns:
        tp = c["test_pivot"].to_numpy(np.float64)
        tc = c["t_confirm"].to_numpy(np.float64)
        ok(
            "C_test_pivot_plus_L_eq_confirm",
            bool(np.all(np.isfinite(tp) & (tp + PIVOT_L == tc))),
            f"mismatches={int((~(np.isfinite(tp) & (tp + PIVOT_L == tc))).sum())}",
        )

    # Year/split sanity
    years = events["year"].to_numpy(np.int64)
    ok("years_in_sample_span", bool(years.min() >= 2010 and years.max() <= 2026), f"min={years.min()} max={years.max()}")

    all_pass = all(v["pass"] for v in checks.values())
    return {"all_pass": all_pass, "checks": checks, "n_events": int(len(events))}


def write_audit(report: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
