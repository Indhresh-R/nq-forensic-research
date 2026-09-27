"""
Strategy 50 Step 2 extractor: bars → pivots → TRs → terminal → confirm → A/B/C.

No forward returns. No outcome columns.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from bars import build_15m, causal_atr20, from_ticks, mark_segments
from constants import (
    ACCEPT_CONSEC_CLOSES,
    CONTROL_A_LOOKBACK,
    LATE_MIN_BARS,
    MAX_EXCURSION_HEIGHT_FRAC,
    MIN_VIOL_HEIGHT_FRAC,
    MIN_VIOL_TICKS,
    PIVOT_L,
    R_MAX,
    SWING_TOL_ATR,
    TICK,
    TR_HEIGHT_MIN_ATR,
    TR_MIN_DEV_BARS,
    TR_REVISIT_FRAC,
    W_CONFIRM,
)


def _min_viol_ticks(height_ticks: int) -> int:
    return max(MIN_VIOL_TICKS, int(np.ceil(MIN_VIOL_HEIGHT_FRAC * max(height_ticks, 1))))


@dataclass
class TR:
    tr_id: int
    t_eligible: int
    tr_low_ticks: int
    tr_high_ticks: int
    invalidate_i: int | None = None
    cooldown_until: int = -1

    def live_at(self, i: int) -> bool:
        if i < self.t_eligible:
            return False
        if self.invalidate_i is not None and i >= self.invalidate_i:
            return False
        return True


@dataclass
class TermState:
    kind: str  # spring | upthrust
    tr: TR
    t_viol: int
    E: int
    stage: str = "recover"  # recover | confirm
    t_return: int | None = None
    V_exc: float | None = None
    extreme_after_return: int | None = None  # rally high (spring) / pullback low (upthrust)


def detect_pivots(
    low_t: np.ndarray, high_t: np.ndarray, seg: np.ndarray
) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    n = len(low_t)
    L = PIVOT_L
    lows: list[tuple[int, int]] = []
    highs: list[tuple[int, int]] = []
    for i in range(L, n - L):
        if not np.all(seg[i - L : i + L + 1] == seg[i]):
            continue
        w_lo = low_t[i - L : i + L + 1]
        if low_t[i] == w_lo.min() and int(np.sum(w_lo == low_t[i])) == 1:
            lows.append((i, i + L))
        w_hi = high_t[i - L : i + L + 1]
        if high_t[i] == w_hi.max() and int(np.sum(w_hi == high_t[i])) == 1:
            highs.append((i, i + L))
    return lows, highs


def try_build_tr(
    confirm_i: int,
    swing_lows: list[tuple[int, int]],
    swing_highs: list[tuple[int, int]],
    low_t: np.ndarray,
    high_t: np.ndarray,
    atr_at: np.ndarray,
    seg: np.ndarray,
    tr_id: int,
) -> TR | None:
    atr = atr_at[confirm_i]
    if not np.isfinite(atr) or atr <= 0:
        return None
    atr_ticks = atr / TICK
    tol = SWING_TOL_ATR * atr_ticks

    recent_lows = swing_lows[-80:]
    recent_highs = swing_highs[-80:]
    lows = [(p, c) for p, c in recent_lows if seg[p] == seg[confirm_i]]
    highs = [(p, c) for p, c in recent_highs if seg[p] == seg[confirm_i]]
    lows = lows[-40:]
    highs = highs[-40:]
    if len(lows) < 2 or len(highs) < 2:
        return None

    sl2_p, _ = lows[-1]
    sl1_p = None
    for p, _c in reversed(lows[:-1]):
        if abs(int(low_t[p]) - int(low_t[sl2_p])) <= tol + 1e-9:
            sl1_p = p
            break
    if sl1_p is None:
        return None

    lo_i, hi_span = min(sl1_p, sl2_p), max(sl1_p, sl2_p)
    cand_h = [(p, c) for p, c in highs if p >= lo_i and c <= confirm_i]
    if len(cand_h) < 2:
        return None
    sh2_p, _ = cand_h[-1]
    sh1_p = None
    for p, _c in reversed(cand_h[:-1]):
        if abs(int(high_t[p]) - int(high_t[sh2_p])) <= tol + 1e-9:
            sh1_p = p
            break
    if sh1_p is None:
        return None

    if not (max(sh1_p, sh2_p) > sl1_p and max(sl1_p, sl2_p) > sh1_p):
        return None

    pivots = [sl1_p, sl2_p, sh1_p, sh2_p]
    confirms = []
    low_map = {p: c for p, c in lows}
    high_map = {p: c for p, c in highs}
    for p in (sl1_p, sl2_p):
        confirms.append(low_map[p])
    for p in (sh1_p, sh2_p):
        confirms.append(high_map[p])
    t_elig = max(confirms)
    if t_elig != confirm_i:
        return None
    if seg[min(pivots)] != seg[t_elig]:
        return None

    tr_low = int(min(low_t[sl1_p], low_t[sl2_p]))
    tr_high = int(max(high_t[sh1_p], high_t[sh2_p]))
    height = tr_high - tr_low
    if height <= 0 or height < TR_HEIGHT_MIN_ATR * atr_ticks:
        return None
    if t_elig - min(pivots) < TR_MIN_DEV_BARS:
        return None

    pivot_set = set(pivots)
    band_low = tr_low + int(np.floor(TR_REVISIT_FRAC * height))
    band_high = tr_high - int(np.floor(TR_REVISIT_FRAC * height))
    near_low = near_high = False
    for j in range(min(pivots), t_elig + 1):
        if j in pivot_set:
            continue
        if low_t[j] <= band_low:
            near_low = True
        if high_t[j] >= band_high:
            near_high = True
    if not (near_low and near_high):
        return None

    return TR(tr_id=tr_id, t_eligible=t_elig, tr_low_ticks=tr_low, tr_high_ticks=tr_high)


def _row(
    bars: pd.DataFrame,
    *,
    event_class: str,
    kind: str,
    tr_id: int,
    tr_low_ticks: int,
    tr_high_ticks: int,
    t_eligible: int,
    t_viol: int,
    t_return: int,
    t_confirm: int | None,
    confirm_ok: bool,
    fail_reason: str,
    E: int,
    V_exc: float | None = None,
    V_test: float | None = None,
    test_pivot: int | None = None,
) -> dict:
    split_i = t_confirm if (t_confirm is not None and confirm_ok) else t_return
    return {
        "event_class": event_class,
        "kind": kind,
        "tr_id": tr_id,
        "tr_low": from_ticks(tr_low_ticks),
        "tr_high": from_ticks(tr_high_ticks),
        "tr_low_ticks": tr_low_ticks,
        "tr_high_ticks": tr_high_ticks,
        "t_eligible": t_eligible,
        "t_viol": t_viol,
        "t_return": t_return,
        "t_terminal_event": t_return,
        "t_confirm": t_confirm if confirm_ok else None,
        "t_sequence_complete": t_confirm if confirm_ok else None,
        "confirm_ok": bool(confirm_ok),
        "fail_reason": fail_reason,
        "E_extreme": from_ticks(E),
        "E_ticks": E,
        "V_excursion": V_exc,
        "V_test": V_test,
        "test_pivot": test_pivot,
        "ts_viol": str(bars["end"].iat[t_viol]),
        "ts_return": str(bars["end"].iat[t_return]),
        "ts_confirm": str(bars["end"].iat[t_confirm]) if (t_confirm is not None and confirm_ok) else "",
        "session_date": bars["session_date"].iat[split_i],
        "year": int(bars["year"].iat[split_i]),
        "segment_id": int(bars["segment_id"].iat[t_return]),
    }


def extract_events(df_1m: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    bars = build_15m(df_1m)
    bars = mark_segments(bars)
    atr_at, atr_prior = causal_atr20(bars)
    bars["atr_at"] = atr_at
    bars["atr_prior"] = atr_prior

    low_t = bars["low_ticks"].to_numpy(np.int64)
    high_t = bars["high_ticks"].to_numpy(np.int64)
    close_t = bars["close_ticks"].to_numpy(np.int64)
    vol = bars["volume"].to_numpy(np.float64)
    seg = bars["segment_id"].to_numpy(np.int64)
    n = len(bars)

    swing_lows, swing_highs = detect_pivots(low_t, high_t, seg)
    # Index by confirm bar for O(1) updates; keep causal running lists per segment.
    low_confirm: dict[int, list[int]] = {}
    high_confirm: dict[int, list[int]] = {}
    for p, c in swing_lows:
        low_confirm.setdefault(c, []).append(p)
    for p, c in swing_highs:
        high_confirm.setdefault(c, []).append(p)

    # Running confirmed swings available at time i (append-only).
    lows_so_far: list[tuple[int, int]] = []
    highs_so_far: list[tuple[int, int]] = []

    trs: list[TR] = []
    next_id = 1
    events: list[dict] = []
    term: TermState | None = None

    # Descriptive funnel counters only — do not affect event grammar.
    funnel = {
        "eligible_trs": 0,
        "terminal_violations": 0,
        "terminal_violations_spring": 0,
        "terminal_violations_upthrust": 0,
        "recover_abort_timeout": 0,
        "recover_abort_excursion": 0,
        "recover_abort_acceptance": 0,
        "recover_abort_segment_break": 0,
        "returns_into_tr": 0,
        "returns_spring": 0,
        "returns_upthrust": 0,
        "candidate_tests": 0,
        "confirm_success_C": 0,
        "confirm_fail_test_quality": 0,
        "confirm_fail_window_expire": 0,
        "confirm_fail_adverse_close": 0,
        "confirm_abort_segment_break": 0,
    }

    # Control A levels in ticks
    support20 = np.full(n, -1, dtype=np.int64)
    resist20 = np.full(n, -1, dtype=np.int64)
    for i in range(CONTROL_A_LOOKBACK, n):
        if np.all(seg[i - CONTROL_A_LOOKBACK : i] == seg[i]):
            support20[i] = int(low_t[i - CONTROL_A_LOOKBACK : i].min())
            resist20[i] = int(high_t[i - CONTROL_A_LOOKBACK : i].max())

    open_a: dict | None = None

    for i in range(n):
        # --- segment break ---
        if bool(bars["segment_break"].iat[i]):
            if term is not None and term.stage == "recover":
                funnel["recover_abort_segment_break"] += 1
            elif term is not None and term.stage == "confirm":
                funnel["confirm_abort_segment_break"] = funnel.get("confirm_abort_segment_break", 0) + 1
            term = None
            open_a = None
            for tr in trs:
                if tr.invalidate_i is None and tr.t_eligible <= i:
                    tr.invalidate_i = i

        # --- TR acceptance invalidation ---
        for tr in trs:
            if not tr.live_at(i):
                continue
            if i + 1 < ACCEPT_CONSEC_CLOSES:
                continue
            w = close_t[i - ACCEPT_CONSEC_CLOSES + 1 : i + 1]
            protected_spring = term is not None and term.tr.tr_id == tr.tr_id and term.kind == "spring" and term.stage == "recover"
            protected_ut = term is not None and term.tr.tr_id == tr.tr_id and term.kind == "upthrust" and term.stage == "recover"
            if np.all(w < tr.tr_low_ticks) and not protected_spring:
                tr.invalidate_i = i
            if np.all(w > tr.tr_high_ticks) and not protected_ut:
                tr.invalidate_i = i

        # --- new TR on pivot confirm ---
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
                next_id += 1
                funnel["eligible_trs"] += 1

        # --- advance terminal recover / confirm ---
        if term is not None:
            tr = term.tr
            height = tr.tr_high_ticks - tr.tr_low_ticks
            if term.stage == "recover":
                age = i - term.t_viol
                if age >= R_MAX:
                    funnel["recover_abort_timeout"] += 1
                    term = None
                elif term.kind == "spring":
                    term.E = min(term.E, int(low_t[i]))
                    if term.E < tr.tr_low_ticks - int(MAX_EXCURSION_HEIGHT_FRAC * height):
                        funnel["recover_abort_excursion"] += 1
                        term = None
                    elif close_t[i] >= tr.tr_low_ticks:
                        term.t_return = i
                        term.V_exc = float(np.mean(vol[term.t_viol : i + 1]))
                        term.extreme_after_return = int(high_t[i])
                        term.stage = "confirm"
                        funnel["returns_into_tr"] += 1
                        funnel["returns_spring"] += 1
                    elif age + 1 >= ACCEPT_CONSEC_CLOSES and np.all(
                        close_t[i - ACCEPT_CONSEC_CLOSES + 1 : i + 1] < tr.tr_low_ticks
                    ):
                        funnel["recover_abort_acceptance"] += 1
                        term = None
                else:
                    term.E = max(term.E, int(high_t[i]))
                    if term.E > tr.tr_high_ticks + int(MAX_EXCURSION_HEIGHT_FRAC * height):
                        funnel["recover_abort_excursion"] += 1
                        term = None
                    elif close_t[i] <= tr.tr_high_ticks:
                        term.t_return = i
                        term.V_exc = float(np.mean(vol[term.t_viol : i + 1]))
                        term.extreme_after_return = int(low_t[i])
                        term.stage = "confirm"
                        funnel["returns_into_tr"] += 1
                        funnel["returns_upthrust"] += 1
                    elif age + 1 >= ACCEPT_CONSEC_CLOSES and np.all(
                        close_t[i - ACCEPT_CONSEC_CLOSES + 1 : i + 1] > tr.tr_high_ticks
                    ):
                        funnel["recover_abort_acceptance"] += 1
                        term = None

            if term is not None and term.stage == "confirm":
                assert term.t_return is not None
                t0 = term.t_return
                if i > t0:
                    if i - t0 > W_CONFIRM:
                        funnel["confirm_fail_window_expire"] += 1
                        events.append(
                            _row(
                                bars,
                                event_class="B",
                                kind=term.kind,
                                tr_id=tr.tr_id,
                                tr_low_ticks=tr.tr_low_ticks,
                                tr_high_ticks=tr.tr_high_ticks,
                                t_eligible=tr.t_eligible,
                                t_viol=term.t_viol,
                                t_return=t0,
                                t_confirm=None,
                                confirm_ok=False,
                                fail_reason="window_expire",
                                E=term.E,
                                V_exc=term.V_exc,
                            )
                        )
                        tr.cooldown_until = t0 + W_CONFIRM
                        term = None
                    elif term.kind == "spring" and close_t[i] < tr.tr_low_ticks:
                        funnel["confirm_fail_adverse_close"] += 1
                        events.append(
                            _row(
                                bars,
                                event_class="B",
                                kind=term.kind,
                                tr_id=tr.tr_id,
                                tr_low_ticks=tr.tr_low_ticks,
                                tr_high_ticks=tr.tr_high_ticks,
                                t_eligible=tr.t_eligible,
                                t_viol=term.t_viol,
                                t_return=t0,
                                t_confirm=None,
                                confirm_ok=False,
                                fail_reason="close_below_tr",
                                E=term.E,
                                V_exc=term.V_exc,
                            )
                        )
                        tr.cooldown_until = i
                        term = None
                    elif term.kind == "upthrust" and close_t[i] > tr.tr_high_ticks:
                        funnel["confirm_fail_adverse_close"] += 1
                        events.append(
                            _row(
                                bars,
                                event_class="B",
                                kind=term.kind,
                                tr_id=tr.tr_id,
                                tr_low_ticks=tr.tr_low_ticks,
                                tr_high_ticks=tr.tr_high_ticks,
                                t_eligible=tr.t_eligible,
                                t_viol=term.t_viol,
                                t_return=t0,
                                t_confirm=None,
                                confirm_ok=False,
                                fail_reason="close_above_tr",
                                E=term.E,
                                V_exc=term.V_exc,
                            )
                        )
                        tr.cooldown_until = i
                        term = None
                    else:
                        # update post-return extreme
                        if term.kind == "spring":
                            if high_t[i] > term.extreme_after_return:
                                term.extreme_after_return = int(high_t[i])
                            if i in low_confirm:
                                mid = (tr.tr_low_ticks + tr.tr_high_ticks) // 2
                                done = False
                                for p in low_confirm[i]:
                                    if low_t[p] > mid:
                                        continue
                                    # volume on pullback into test
                                    rh = term.extreme_after_return
                                    rh_bar = t0
                                    for j in range(t0, p + 1):
                                        if high_t[j] >= rh:
                                            rh = int(high_t[j])
                                            rh_bar = j
                                    start_pb = rh_bar + 1
                                    if start_pb <= p:
                                        pb = vol[start_pb : p + 1]
                                    else:
                                        pb = vol[max(p - 2, t0 + 1) : p + 1]
                                    v_test = float(np.mean(pb)) if len(pb) else float(vol[p])
                                    ok_hl = int(low_t[p]) > term.E
                                    ok_vol = v_test < float(term.V_exc)
                                    funnel["candidate_tests"] += 1
                                    if ok_hl and ok_vol:
                                        funnel["confirm_success_C"] += 1
                                        events.append(
                                            _row(
                                                bars,
                                                event_class="C",
                                                kind="spring",
                                                tr_id=tr.tr_id,
                                                tr_low_ticks=tr.tr_low_ticks,
                                                tr_high_ticks=tr.tr_high_ticks,
                                                t_eligible=tr.t_eligible,
                                                t_viol=term.t_viol,
                                                t_return=t0,
                                                t_confirm=i,
                                                confirm_ok=True,
                                                fail_reason="",
                                                E=term.E,
                                                V_exc=term.V_exc,
                                                V_test=v_test,
                                                test_pivot=p,
                                            )
                                        )
                                        tr.cooldown_until = max(i, t0 + W_CONFIRM)
                                        term = None
                                        done = True
                                        break
                                    funnel["confirm_fail_test_quality"] += 1
                                    events.append(
                                        _row(
                                            bars,
                                            event_class="B",
                                            kind="spring",
                                            tr_id=tr.tr_id,
                                            tr_low_ticks=tr.tr_low_ticks,
                                            tr_high_ticks=tr.tr_high_ticks,
                                            t_eligible=tr.t_eligible,
                                            t_viol=term.t_viol,
                                            t_return=t0,
                                            t_confirm=i,
                                            confirm_ok=False,
                                            fail_reason="test_fail_hl_or_vol",
                                            E=term.E,
                                            V_exc=term.V_exc,
                                            V_test=v_test,
                                            test_pivot=p,
                                        )
                                    )
                                    tr.cooldown_until = max(i, t0 + W_CONFIRM)
                                    term = None
                                    done = True
                                    break
                                if done:
                                    pass
                        else:  # upthrust confirm
                            if low_t[i] < term.extreme_after_return:
                                term.extreme_after_return = int(low_t[i])
                            if i in high_confirm:
                                mid = (tr.tr_low_ticks + tr.tr_high_ticks) // 2
                                for p in high_confirm[i]:
                                    if high_t[p] < mid:
                                        continue
                                    rl = term.extreme_after_return
                                    rl_bar = t0
                                    for j in range(t0, p + 1):
                                        if low_t[j] <= rl:
                                            rl = int(low_t[j])
                                            rl_bar = j
                                    start_pb = rl_bar + 1
                                    if start_pb <= p:
                                        pb = vol[start_pb : p + 1]
                                    else:
                                        pb = vol[max(p - 2, t0 + 1) : p + 1]
                                    v_test = float(np.mean(pb)) if len(pb) else float(vol[p])
                                    ok_lh = int(high_t[p]) < term.E
                                    ok_vol = v_test < float(term.V_exc)
                                    funnel["candidate_tests"] += 1
                                    if ok_lh and ok_vol:
                                        funnel["confirm_success_C"] += 1
                                        events.append(
                                            _row(
                                                bars,
                                                event_class="C",
                                                kind="upthrust",
                                                tr_id=tr.tr_id,
                                                tr_low_ticks=tr.tr_low_ticks,
                                                tr_high_ticks=tr.tr_high_ticks,
                                                t_eligible=tr.t_eligible,
                                                t_viol=term.t_viol,
                                                t_return=t0,
                                                t_confirm=i,
                                                confirm_ok=True,
                                                fail_reason="",
                                                E=term.E,
                                                V_exc=term.V_exc,
                                                V_test=v_test,
                                                test_pivot=p,
                                            )
                                        )
                                    else:
                                        funnel["confirm_fail_test_quality"] += 1
                                        events.append(
                                            _row(
                                                bars,
                                                event_class="B",
                                                kind="upthrust",
                                                tr_id=tr.tr_id,
                                                tr_low_ticks=tr.tr_low_ticks,
                                                tr_high_ticks=tr.tr_high_ticks,
                                                t_eligible=tr.t_eligible,
                                                t_viol=term.t_viol,
                                                t_return=t0,
                                                t_confirm=i,
                                                confirm_ok=False,
                                                fail_reason="test_fail_lh_or_vol",
                                                E=term.E,
                                                V_exc=term.V_exc,
                                                V_test=v_test,
                                                test_pivot=p,
                                            )
                                        )
                                    tr.cooldown_until = max(i, t0 + W_CONFIRM)
                                    term = None
                                    break

        # --- start new TR terminal ---
        if term is None:
            live = [tr for tr in trs if tr.live_at(i) and i - tr.t_eligible >= LATE_MIN_BARS and i > tr.cooldown_until]
            live.sort(key=lambda t: t.t_eligible)
            for tr in live:
                height = tr.tr_high_ticks - tr.tr_low_ticks
                need = _min_viol_ticks(height)
                if int(low_t[i]) < tr.tr_low_ticks and (tr.tr_low_ticks - int(low_t[i])) >= need:
                    term = TermState(kind="spring", tr=tr, t_viol=i, E=int(low_t[i]))
                    funnel["terminal_violations"] += 1
                    funnel["terminal_violations_spring"] += 1
                    break
                if int(high_t[i]) > tr.tr_high_ticks and (int(high_t[i]) - tr.tr_high_ticks) >= need:
                    term = TermState(kind="upthrust", tr=tr, t_viol=i, E=int(high_t[i]))
                    funnel["terminal_violations"] += 1
                    funnel["terminal_violations_upthrust"] += 1
                    break

        # --- Control A ---
        if open_a is not None:
            age = i - open_a["t_viol"]
            if bool(bars["segment_break"].iat[i]) or age >= R_MAX:
                open_a = None
            elif open_a["kind"] == "spring":
                open_a["E"] = min(open_a["E"], int(low_t[i]))
                if close_t[i] >= open_a["level"]:
                    events.append(
                        _row(
                            bars,
                            event_class="A",
                            kind="spring",
                            tr_id=-1,
                            tr_low_ticks=open_a["level"],
                            tr_high_ticks=open_a["resist"],
                            t_eligible=-1,
                            t_viol=open_a["t_viol"],
                            t_return=i,
                            t_confirm=None,
                            confirm_ok=False,
                            fail_reason="control_a",
                            E=open_a["E"],
                        )
                    )
                    open_a = None
            else:
                open_a["E"] = max(open_a["E"], int(high_t[i]))
                if close_t[i] <= open_a["level"]:
                    events.append(
                        _row(
                            bars,
                            event_class="A",
                            kind="upthrust",
                            tr_id=-1,
                            tr_low_ticks=open_a["support"],
                            tr_high_ticks=open_a["level"],
                            t_eligible=-1,
                            t_viol=open_a["t_viol"],
                            t_return=i,
                            t_confirm=None,
                            confirm_ok=False,
                            fail_reason="control_a",
                            E=open_a["E"],
                        )
                    )
                    open_a = None

        if open_a is None and support20[i] >= 0:
            live_lows = {tr.tr_low_ticks for tr in trs if tr.live_at(i)}
            live_highs = {tr.tr_high_ticks for tr in trs if tr.live_at(i)}
            s20, r20 = int(support20[i]), int(resist20[i])
            need = _min_viol_ticks(max(1, r20 - s20))
            if int(low_t[i]) < s20 and (s20 - int(low_t[i])) >= need and s20 not in live_lows:
                open_a = {"kind": "spring", "t_viol": i, "level": s20, "resist": r20, "support": s20, "E": int(low_t[i])}
            elif int(high_t[i]) > r20 and (int(high_t[i]) - r20) >= need and r20 not in live_highs:
                open_a = {"kind": "upthrust", "t_viol": i, "level": r20, "resist": r20, "support": s20, "E": int(high_t[i])}

    ev = pd.DataFrame(events)
    if len(ev):
        ev = ev.sort_values(["t_terminal_event", "event_class", "kind"]).reset_index(drop=True)

    meta = {
        "n_1m": int(len(df_1m)),
        "n_15m": int(n),
        "n_segments": int(bars["segment_id"].nunique()),
        "n_swing_lows": len(swing_lows),
        "n_swing_highs": len(swing_highs),
        "n_trs": len(trs),
        "n_events": int(len(ev)),
        "n_A": int((ev["event_class"] == "A").sum()) if len(ev) else 0,
        "n_B": int((ev["event_class"] == "B").sum()) if len(ev) else 0,
        "n_C": int((ev["event_class"] == "C").sum()) if len(ev) else 0,
    }
    # attach TR table lightly
    tr_rows = [
        {
            "tr_id": t.tr_id,
            "t_eligible": t.t_eligible,
            "tr_low": from_ticks(t.tr_low_ticks),
            "tr_high": from_ticks(t.tr_high_ticks),
            "invalidate_i": t.invalidate_i,
            "ts_eligible": str(bars["end"].iat[t.t_eligible]),
        }
        for t in trs
    ]
    meta["trs"] = tr_rows
    meta["funnel"] = funnel
    return ev, bars, meta
