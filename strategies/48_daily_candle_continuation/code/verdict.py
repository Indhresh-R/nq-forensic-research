"""Mechanical verdict. The clauses are frozen and are not revised after the run."""
from __future__ import annotations

import math

import pandas as pd

from definitions import REQUIRED_SPLITS


def _lift(metrics: pd.DataFrame, model: str, slice_name: str) -> float:
    chosen = metrics.loc[(metrics["model"] == model) & (metrics["slice"] == slice_name), "lift"]
    if chosen.empty:
        return math.nan
    return float(chosen.iloc[0])


def _hit(table: pd.DataFrame, model: str, slice_name: str, block: str | None = None) -> float:
    mask = (table["model"] == model) & (table["slice"] == slice_name)
    if block is not None:
        mask = mask & (table["block"] == block)
    chosen = table.loc[mask, "hit_rate"]
    if chosen.empty:
        return math.nan
    return float(chosen.iloc[0])


def _n(table: pd.DataFrame, model: str, slice_name: str, block: str | None = None) -> int:
    mask = (table["model"] == model) & (table["slice"] == slice_name)
    if block is not None:
        mask = mask & (table["block"] == block)
    chosen = table.loc[mask, "n"]
    if chosen.empty:
        return 0
    return int(chosen.iloc[0])


def _positive_on_splits(metrics: pd.DataFrame, model: str) -> tuple[bool, list[str]]:
    failures: list[str] = []
    for slice_name in REQUIRED_SPLITS:
        value = _lift(metrics, model, slice_name)
        if math.isnan(value) or value <= 0.0:
            failures.append(f"{model} lift on {slice_name} is {value:.4f}" if not math.isnan(value) else f"{model} lift on {slice_name} is missing")
    return (len(failures) == 0), failures


def judge(metrics: pd.DataFrame, agreement: pd.DataFrame) -> dict[str, object]:
    """Return the frozen pass/fail clauses. This does not search for a better cut."""
    clauses: list[str] = []
    test1_ok, test1_fail = _positive_on_splits(metrics, "test1_pooled")
    test2_ok, test2_fail = _positive_on_splits(metrics, "test2_pooled")
    bear1_ok, bear1_fail = _positive_on_splits(metrics, "test1_bear")
    bear2_ok, bear2_fail = _positive_on_splits(metrics, "test2_down")
    clauses.extend(test1_fail)
    clauses.extend(test2_fail)
    clauses.extend(bear1_fail)
    clauses.extend(bear2_fail)

    continuation_real = test1_ok and test2_ok and bear1_ok and bear2_ok
    disagree_n = _n(agreement, "test1", "All", "disagree")
    test1_disagree = _hit(agreement, "test1", "All", "disagree")
    test2_disagree = _hit(agreement, "test2", "All", "disagree")
    if disagree_n == 0:
        flip_line = "There are no disagreement days, so the flip never diverges from Test 1."
        flip_adds = False
    elif math.isnan(test2_disagree) or math.isnan(test1_disagree) or test2_disagree <= test1_disagree:
        flip_line = (
            f"The flip adds nothing. On disagreement days (n={disagree_n}), "
            f"Test 2 hit rate {test2_disagree:.4f} does not beat Test 1 hit rate {test1_disagree:.4f}."
        )
        flip_adds = False
    else:
        flip_line = (
            f"On disagreement days (n={disagree_n}), Test 2 hit rate {test2_disagree:.4f} "
            f"beats Test 1 hit rate {test1_disagree:.4f}."
        )
        flip_adds = True

    test2_up = _hit(metrics, "test2_up", "All")
    always = _hit(metrics, "always_long", "All")
    if math.isnan(test2_up) or math.isnan(always) or test2_up <= always:
        long_line = (
            f"Always Long matches or beats the bullish state. "
            f"Test 2 up hit rate {test2_up:.4f}, Always Long hit rate {always:.4f}."
        )
        long_beats = True
    else:
        long_line = (
            f"The bullish state hit rate {test2_up:.4f} is above Always Long {always:.4f} on All."
        )
        long_beats = False

    if continuation_real:
        verdict = "REAL"
        lead = (
            "REAL on the frozen continuation clauses: Test 1 and Test 2 pooled lifts, "
            "and both bear-forecast lifts, are positive on IS, Validation, and OOS."
        )
    else:
        verdict = "NOT REAL"
        lead = "NOT REAL. The frozen continuation clauses fail."

    return {
        "verdict": verdict,
        "lead": lead,
        "failures": clauses,
        "flip_line": flip_line,
        "flip_adds": flip_adds,
        "long_line": long_line,
        "long_beats_bullish_state": long_beats,
        "continuation_real": continuation_real,
    }
