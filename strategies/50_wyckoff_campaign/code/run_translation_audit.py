"""
Step 4 — Wyckoff translation audit (no outcomes, no change to frozen Step 3 events).

For each frozen-grammar terminal-violation *start*, record recovery-path counterfactuals
to separate the 6-bar window from the 1×TR-height excursion cap.

Does NOT rewrite Step 3 results. Does NOT compute leave-range outcomes.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
CODE = Path(__file__).resolve().parent
OUT = Path(__file__).resolve().parents[1] / "results"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(CODE))

from bars import causal_atr20, mark_segments
from constants import (
    ACCEPT_CONSEC_CLOSES,
    LATE_MIN_BARS,
    MAX_EXCURSION_HEIGHT_FRAC,
    MIN_VIOL_HEIGHT_FRAC,
    MIN_VIOL_TICKS,
    R_MAX,
)
from extract import TR, detect_pivots, try_build_tr


def _min_viol_ticks(height_ticks: int) -> int:
    return max(MIN_VIOL_TICKS, int(np.ceil(MIN_VIOL_HEIGHT_FRAC * max(height_ticks, 1))))


def _path_facts(
    *,
    t_viol: int,
    kind: str,
    tr_low: int,
    tr_high: int,
    low_t: np.ndarray,
    high_t: np.ndarray,
    close_t: np.ndarray,
    seg: np.ndarray,
    n: int,
) -> dict:
    height = max(1, tr_high - tr_low)

    def returned_at(j: int) -> bool:
        if kind == "spring":
            return bool(close_t[j] >= tr_low)
        return bool(close_t[j] <= tr_high)

    def exc_frac_through(j_end: int) -> float:
        if kind == "spring":
            e = int(low_t[t_viol : j_end + 1].min())
            return float((tr_low - e) / height)
        e = int(high_t[t_viol : j_end + 1].max())
        return float((e - tr_high) / height)

    out: dict = {}
    for W in (6, 12, 24, 48):
        # Strict: abort if excursion exceeds cap before return (window-extended frozen rule)
        first_ret = None
        max_exc = 0.0
        seg_break = False
        for age in range(0, W):
            j = t_viol + age
            if j >= n:
                break
            if age > 0 and int(seg[j]) != int(seg[t_viol]):
                seg_break = True
                break
            max_exc = max(max_exc, exc_frac_through(j))
            if max_exc > MAX_EXCURSION_HEIGHT_FRAC:
                break
            if returned_at(j):
                first_ret = age
                break
        out[f"return_within_{W}_exc_capped"] = first_ret is not None
        out[f"return_age_{W}_exc_capped"] = int(first_ret) if first_ret is not None else -1
        out[f"max_exc_frac_within_{W}"] = float(max_exc)
        out[f"seg_break_within_{W}"] = bool(seg_break)

        # Ignore excursion cap: first close back inside within W
        first_ret_ign = None
        max_exc_ign = 0.0
        for age in range(0, W):
            j = t_viol + age
            if j >= n or (age > 0 and int(seg[j]) != int(seg[t_viol])):
                break
            max_exc_ign = max(max_exc_ign, exc_frac_through(j))
            if returned_at(j):
                first_ret_ign = age
                break
        out[f"return_ignoring_exc_within_{W}"] = first_ret_ign is not None
        out[f"return_ignoring_exc_age_{W}"] = int(first_ret_ign) if first_ret_ign is not None else -1
        out[f"max_exc_even_if_returned_{W}"] = float(max_exc_ign)

    # Frozen recovery: return within R_MAX without ever exceeding excursion cap
    frozen_ok = False
    frozen_age = -1
    max_exc = 0.0
    for age in range(0, R_MAX):
        j = t_viol + age
        if j >= n or (age > 0 and int(seg[j]) != int(seg[t_viol])):
            break
        max_exc = max(max_exc, exc_frac_through(j))
        if max_exc > MAX_EXCURSION_HEIGHT_FRAC:
            break
        if returned_at(j):
            frozen_ok = True
            frozen_age = age
            break
    out["frozen_return"] = bool(frozen_ok)
    out["frozen_return_age"] = int(frozen_age)
    out["frozen_max_exc_frac"] = float(max_exc)
    return out


def collect_violation_paths(bars: pd.DataFrame) -> pd.DataFrame:
    if "atr_at" not in bars.columns:
        atr_at, atr_prior = causal_atr20(bars)
        bars = bars.copy()
        bars["atr_at"] = atr_at
        bars["atr_prior"] = atr_prior

    low_t = bars["low_ticks"].to_numpy(np.int64)
    high_t = bars["high_ticks"].to_numpy(np.int64)
    close_t = bars["close_ticks"].to_numpy(np.int64)
    seg = bars["segment_id"].to_numpy(np.int64)
    atr_at = bars["atr_at"].to_numpy(np.float64)
    n = len(bars)

    swing_lows, swing_highs = detect_pivots(low_t, high_t, seg)
    low_confirm: dict[int, list[int]] = {}
    high_confirm: dict[int, list[int]] = {}
    for p, c in swing_lows:
        low_confirm.setdefault(c, []).append(p)
    for p, c in swing_highs:
        high_confirm.setdefault(c, []).append(p)

    lows_so_far: list[tuple[int, int]] = []
    highs_so_far: list[tuple[int, int]] = []
    trs: list[TR] = []
    next_id = 1
    cooldown: dict[int, int] = {}
    busy_until = -1  # global one-open-term separation like extract
    rows: list[dict] = []

    def live(tr: TR, i: int) -> bool:
        if i < tr.t_eligible:
            return False
        if tr.invalidate_i is not None and i >= tr.invalidate_i:
            return False
        return True

    for i in range(n):
        if bool(bars["segment_break"].iat[i]):
            for tr in trs:
                if tr.invalidate_i is None and tr.t_eligible <= i:
                    tr.invalidate_i = i

        for tr in trs:
            if not live(tr, i) or i + 1 < ACCEPT_CONSEC_CLOSES:
                continue
            w = close_t[i - ACCEPT_CONSEC_CLOSES + 1 : i + 1]
            if np.all(w < tr.tr_low_ticks) or np.all(w > tr.tr_high_ticks):
                # simplified: invalidate (protection during recover omitted — violation starts
                # only when not busy; matches count approximately)
                if busy_until < i:
                    tr.invalidate_i = i

        if i in low_confirm:
            for p in low_confirm[i]:
                lows_so_far.append((p, i))
        if i in high_confirm:
            for p in high_confirm[i]:
                highs_so_far.append((p, i))
        if i in low_confirm or i in high_confirm:
            cand = try_build_tr(i, lows_so_far, highs_so_far, low_t, high_t, atr_at, seg, next_id)
            if cand is not None:
                for tr in trs:
                    if tr.invalidate_i is None and tr.t_eligible < cand.t_eligible:
                        tr.invalidate_i = i
                trs.append(cand)
                cooldown[cand.tr_id] = -1
                next_id += 1

        if i <= busy_until:
            continue

        live_trs = [
            tr
            for tr in trs
            if live(tr, i) and i - tr.t_eligible >= LATE_MIN_BARS and i > cooldown.get(tr.tr_id, -1)
        ]
        live_trs.sort(key=lambda t: t.t_eligible)
        for tr in live_trs:
            height = tr.tr_high_ticks - tr.tr_low_ticks
            need = _min_viol_ticks(height)
            kind = None
            if int(low_t[i]) < tr.tr_low_ticks and (tr.tr_low_ticks - int(low_t[i])) >= need:
                kind = "spring"
            elif int(high_t[i]) > tr.tr_high_ticks and (int(high_t[i]) - tr.tr_high_ticks) >= need:
                kind = "upthrust"
            if kind is None:
                continue
            facts = _path_facts(
                t_viol=i,
                kind=kind,
                tr_low=tr.tr_low_ticks,
                tr_high=tr.tr_high_ticks,
                low_t=low_t,
                high_t=high_t,
                close_t=close_t,
                seg=seg,
                n=n,
            )
            rows.append(
                {
                    "tr_id": tr.tr_id,
                    "kind": kind,
                    "t_viol": i,
                    "tr_height_ticks": height,
                    **facts,
                }
            )
            # Match extract: occupy only until frozen recovery resolves (return / exc / gap),
            # not a blind full R_MAX lock — otherwise we under-count subsequent violations.
            if facts["frozen_return"]:
                busy_until = i + max(facts["frozen_return_age"], 0)
            else:
                # aborted inside window: free on next bar (extract clears term immediately)
                busy_until = i
            cooldown[tr.tr_id] = busy_until
            break

    return pd.DataFrame(rows)


def summarize(paths: pd.DataFrame, funnel: dict) -> dict:
    n = len(paths)
    s: dict = {
        "n_violations_recorded": int(n),
        "funnel_terminal_violations": funnel.get("terminal_violations"),
        "note": "Violation starts follow frozen TR/late/min-violation grammar; recovery counterfactuals vary only recovery constraints.",
    }
    if n == 0:
        return s

    s["frozen_return"] = int(paths["frozen_return"].sum())
    for W in (6, 12, 24, 48):
        s[f"return_within_{W}_exc_capped"] = int(paths[f"return_within_{W}_exc_capped"].sum())
        s[f"return_ignoring_exc_within_{W}"] = int(paths[f"return_ignoring_exc_within_{W}"].sum())

    ign6 = paths[paths["return_ignoring_exc_within_6"]]
    s["killed_by_exc_cap_only_at_6"] = int(
        ((paths["return_ignoring_exc_within_6"]) & (~paths["return_within_6_exc_capped"])).sum()
    )
    s["no_return_even_ignoring_exc_6"] = int((~paths["return_ignoring_exc_within_6"]).sum())
    s["extra_returns_from_extending_6_to_12_ignore_exc"] = int(
        paths["return_ignoring_exc_within_12"].sum() - paths["return_ignoring_exc_within_6"].sum()
    )
    s["extra_returns_from_extending_12_to_24_ignore_exc"] = int(
        paths["return_ignoring_exc_within_24"].sum() - paths["return_ignoring_exc_within_12"].sum()
    )
    s["funnel_recover_abort_timeout"] = funnel.get("recover_abort_timeout")
    s["interpretation_timeout"] = (
        "Funnel recover_abort_timeout=0: under the joint frozen rules, pure 6-bar timeout "
        "almost never fires; inside-window failures are excursion/acceptance/gap."
    )

    if len(ign6):
        s["among_return_ign6"] = {
            "n": int(len(ign6)),
            "max_exc_le_1": int((ign6["max_exc_even_if_returned_6"] <= 1.0).sum()),
            "max_exc_gt_1": int((ign6["max_exc_even_if_returned_6"] > 1.0).sum()),
            "max_exc_median": float(ign6["max_exc_even_if_returned_6"].median()),
            "max_exc_p75": float(ign6["max_exc_even_if_returned_6"].quantile(0.75)),
            "max_exc_p90": float(ign6["max_exc_even_if_returned_6"].quantile(0.9)),
        }

    s["prevalence_ladder_recovery_only"] = {
        "P0_frozen_return_Rmax6_exc1x": s["frozen_return"],
        "P0b_return_within_6_exc_capped": s["return_within_6_exc_capped"],
        "P1_return_within_6_ignore_exc_cap": s["return_ignoring_exc_within_6"],
        "P2_return_within_12_ignore_exc_cap": s["return_ignoring_exc_within_12"],
        "P3_return_within_24_ignore_exc_cap": s["return_ignoring_exc_within_24"],
        "P4_return_within_48_ignore_exc_cap": s["return_ignoring_exc_within_48"],
        "P5_step2_candidate_tests_confirm_attempt": funnel.get("candidate_tests"),
        "P6_step2_class_C_full_sequence": funnel.get("confirm_success_C"),
    }
    return s


def main() -> None:
    bars = pd.read_parquet(OUT / "bars_15m.parquet")
    if "segment_id" not in bars.columns:
        bars = mark_segments(bars)
    funnel = json.loads((OUT / "funnel.json").read_text(encoding="utf-8"))
    print(f"bars={len(bars)} collecting violation paths…", flush=True)
    paths = collect_violation_paths(bars)
    paths.to_parquet(OUT / "translation_violation_paths.parquet", index=False)
    summary = summarize(paths, funnel)
    (OUT / "translation_audit_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
