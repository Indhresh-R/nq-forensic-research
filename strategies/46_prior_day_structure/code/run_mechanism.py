"""Run the previous-day structure mechanism study. No strategy is produced."""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

CODE_DIR = Path(__file__).resolve().parent
ROOT = CODE_DIR.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(CODE_DIR))

from analysis import (  # noqa: E402
    baseline_table,
    distribution_row,
    duration_distribution,
    excursion_table,
    forward_table,
    sequence_frequency,
    structure_table,
    wick_associations,
    year_table,
)
from daily_candles import candle_fields, load_sessions  # noqa: E402
from definitions import RESULTS_DIR, body_fraction_bucket  # noqa: E402
from panel import build_panel  # noqa: E402
from plots import (  # noqa: E402
    plot_bull_bear,
    plot_forward_vs_penetration,
    plot_median_by_bucket,
    plot_mfe_mae,
    plot_penetration_histograms,
    plot_separation_duration,
    plot_year_stability,
)
from report import write_report  # noqa: E402
from safety import run_safety_checks  # noqa: E402
from test_mechanism import run_definition_tests  # noqa: E402
from verdict import decide  # noqa: E402


def _write(frame, name: str) -> None:
    frame.to_csv(RESULTS_DIR / name, index=False)


def main() -> None:
    run_definition_tests()
    print("loading frozen NQ sessions", flush=True)
    sessions, audit = load_sessions()
    print(
        f"sessions={audit['n_sessions']} complete={audit['n_complete']} incomplete={audit['n_incomplete']}",
        flush=True,
    )
    panel, pair_counts = build_panel(sessions)
    print(f"eligible pairs={pair_counts['eligible_pairs']} retracement={pair_counts['retracement']}", flush=True)
    safety_lines = run_safety_checks(panel, sessions)
    print("safety checks passed", flush=True)

    qualified = panel[panel["qualified"]].copy()
    forward_points = forward_table(qualified, "retracement_bucket", "fwd_ret_")
    forward_range = forward_table(qualified, "retracement_bucket", "fwd_ret_rng_")
    bull = qualified[qualified["direction"] == "bullish"]
    bear = qualified[qualified["direction"] == "bearish"]
    bull_points = forward_table(bull, "retracement_bucket", "fwd_ret_")
    bear_points = forward_table(bear, "retracement_bucket", "fwd_ret_")
    bull_range = forward_table(bull, "retracement_bucket", "fwd_ret_rng_")
    bear_range = forward_table(bear, "retracement_bucket", "fwd_ret_rng_")
    excursions = excursion_table(qualified, "retracement_bucket")
    max_range = forward_table(qualified, "max_penetration_bucket", "fwd_ret_rng_")
    baseline = baseline_table(panel)
    structure = structure_table(panel)
    wick_stats = wick_associations(panel)
    yearly = year_table(panel)
    verdict_payload = decide(panel)
    frequency = sequence_frequency(panel)
    durations = duration_distribution(panel)
    split_range = {
        split: forward_table(qualified[qualified["split"] == split], "retracement_bucket", "fwd_ret_rng_")
        for split in ("IS", "Validation", "OOS")
    }

    candle_rows = []
    for session in sessions:
        if not session.complete:
            continue
        fields = candle_fields(session)
        fields["body_bucket"] = body_fraction_bucket(float(fields["body_fraction"]))
        fields["year"] = session.year
        candle_rows.append(fields)
    candle_frame = pd.DataFrame(candle_rows)
    incomplete_reasons = dict(Counter(session.incomplete_reason for session in sessions if not session.complete))

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(RESULTS_DIR / "session_panel.parquet", index=False)
    _write(forward_points, "forward_points_by_retracement.csv")
    _write(forward_range, "forward_range_by_retracement.csv")
    _write(bull_points, "forward_points_bullish.csv")
    _write(bear_points, "forward_points_bearish.csv")
    _write(bull_range, "forward_range_bullish.csv")
    _write(bear_range, "forward_range_bearish.csv")
    _write(excursions, "mfe_mae_by_retracement.csv")
    _write(max_range, "forward_range_by_max_penetration_NONCAUSAL.csv")
    _write(baseline, "baseline_from_open.csv")
    _write(structure, "candle_structure.csv")
    _write(yearly, "year_by_year.csv")
    _write(frequency, "sequence_frequency.csv")
    _write(durations, "separation_duration.csv")
    for split, table in split_range.items():
        _write(table, f"forward_range_{split}.csv")
    for stale in (
        "forward_points_by_first_touch.csv",
        "forward_range_by_first_touch.csv",
        "mfe_mae_by_first_touch.csv",
    ):
        stale_path = RESULTS_DIR / stale
        if stale_path.exists():
            stale_path.unlink()
    (RESULTS_DIR / "audit_status.json").write_text(
        json.dumps(
            {
                "audit": audit,
                "pair_counts": pair_counts,
                "incomplete_reasons": incomplete_reasons,
                "verdict": verdict_payload["verdict"],
                "spearman_30m": verdict_payload["spearman_30m"],
                "spearman_60m": verdict_payload["spearman_60m"],
                "wick_associations": wick_stats,
                "range_distribution_eligible_previous_day": distribution_row(panel["previous_range"]),
                "label": "Pre-cost mechanism analysis — no executable strategy.",
            },
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )

    plot_penetration_histograms(panel)
    plot_separation_duration(panel)
    plot_forward_vs_penetration(panel)
    plot_median_by_bucket(forward_range)
    plot_mfe_mae(excursions)
    plot_bull_bear(panel)
    plot_year_stability(yearly)

    # Safety must already have passed. Writing the report is interpretation.
    report_path = write_report(
        panel=panel,
        audit=audit,
        pair_counts=pair_counts,
        incomplete_reasons=incomplete_reasons,
        safety_lines=safety_lines,
        verdict_payload=verdict_payload,
        candle_frame=candle_frame,
        forward_points=forward_points,
        forward_range=forward_range,
        bull_points=bull_points,
        bear_points=bear_points,
        bull_range=bull_range,
        bear_range=bear_range,
        excursions=excursions,
        max_range=max_range,
        baseline=baseline,
        structure=structure,
        wick_stats=wick_stats,
        yearly=yearly,
        frequency=frequency,
        durations=durations,
        split_range=split_range,
    )
    print(verdict_payload["verdict"], flush=True)
    print(f"report={report_path}", flush=True)


if __name__ == "__main__":
    main()
