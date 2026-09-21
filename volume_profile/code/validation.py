"""Validation tests for the CME volume-profile dataset.

`--unit` does not read trade files.
`--data` checks profiles and reruns the builder for determinism.
`--events` checks interaction timestamps.
"""

from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_research_dataset import _approach, detect_events, iter_session_trades
from build_session_profiles import (
    VP,
    assign_cme_session,
    build_profiles,
    choose_poc,
    expand_value_area,
    load_config,
    session_bounds,
)

STATUS_PATH = VP / "data" / "validation_status.json"


def _ts(value: str) -> pd.Timestamp:
    return pd.Timestamp(value, tz="UTC")


def test_session_assignment() -> None:
    cases = {
        "2026-03-25 22:30:00": date(2026, 3, 25),  # 18:30 EDT
        "2026-03-26 04:00:00": date(2026, 3, 25),  # midnight EDT
        "2026-03-26 14:00:00": date(2026, 3, 25),  # 10:00 EDT
        "2026-03-26 20:59:59": date(2026, 3, 25),  # 16:59 EDT
        "2026-03-26 21:00:00": date(2026, 3, 25),  # 17:00 EDT still this session
        "2026-03-26 21:59:59": date(2026, 3, 25),  # maintenance, still this session
        "2026-03-26 22:00:00": date(2026, 3, 26),  # 18:00 EDT opens the next session
        "2026-01-15 23:00:00": date(2026, 1, 15),  # 18:00 EST
        "2026-01-16 21:59:00": date(2026, 1, 15),  # 16:59 EST
        "2026-01-16 22:00:00": date(2026, 1, 15),  # 17:00 EST
        "2026-01-16 23:00:00": date(2026, 1, 16),  # 18:00 EST
        "2026-03-07 23:00:00": date(2026, 3, 7),  # 18:00 EST, evening before DST
        "2026-03-08 06:30:00": date(2026, 3, 7),  # 01:30 EST, before the 07:00 UTC spring
        "2026-03-08 07:30:00": date(2026, 3, 7),  # 03:30 EDT after the spring
        "2026-03-08 22:00:00": date(2026, 3, 8),  # 18:00 EDT
        "2026-11-01 05:30:00": date(2026, 10, 31),  # 01:30 EDT, before the fall back
        "2026-11-01 06:30:00": date(2026, 10, 31),  # 01:30 EST after the fall back
        "2026-11-01 23:00:00": date(2026, 11, 1),  # 18:00 EST
    }
    for raw, expected in cases.items():
        got = assign_cme_session(_ts(raw))
        if got != expected:
            raise AssertionError(f"{raw} -> {got}, expected {expected}")


def test_partition_equivalence() -> None:
    left = {100: 10, 101: 50, 102: 5}
    right = {101: 20, 102: 40, 103: 7}
    merged: dict[int, int] = {}
    for part in (left, right):
        for px, vol in part.items():
            merged[px] = merged.get(px, 0) + vol
    together = {100: 10, 101: 70, 102: 45, 103: 7}
    if merged != together:
        raise AssertionError("split volume maps do not sum to the combined map")
    poc = choose_poc(merged)
    val, vah, included = expand_value_area(merged, poc, 0.70)
    poc2 = choose_poc(together)
    val2, vah2, included2 = expand_value_area(together, poc2, 0.70)
    if (poc, val, vah, included) != (poc2, val2, vah2, included2):
        raise AssertionError("split profile does not match the combined profile")
    if not (val <= poc <= vah):
        raise AssertionError("value area does not contain POC")
    if included / sum(merged.values()) < 0.70:
        raise AssertionError("value area below 70 percent")


def test_same_timestamp_ordering() -> None:
    # sequence, not row order, decides what is known before the touch
    if _approach(np.array([10, 8], dtype=np.int64), 12, 1) != "from_below":
        raise AssertionError("approach should use the last print outside tolerance")
    if _approach(np.array([10, 20], dtype=np.int64), 12, 1) != "from_above":
        raise AssertionError("approach from above failed")
    if _approach(np.array([], dtype=np.int64), 12, 1) != "ambiguous":
        raise AssertionError("empty prior must be ambiguous")
    cfg = load_config()
    session = date(2026, 3, 25)
    start, _end = session_bounds(session)
    touch = start + pd.Timedelta(hours=2)
    earlier = touch - pd.Timedelta(seconds=1)
    later = touch + pd.Timedelta(minutes=5)
    same_time_below = touch
    trades = pd.DataFrame(
        {
            "ts_event": [touch, same_time_below, earlier, touch],
            "sequence": [5, 0, 1, 2],
            "price_ticks": [130, 80, 90, 100],
            "size": [1, 1, 1, 1],
        }
    )
    row = pd.Series(
        {
            "session_date": session.isoformat(),
            "prev_session_date": (session - timedelta(days=1)).isoformat(),
            "prev_poc": 25.0,
            "prev_vah": 26.0,
            "prev_val": 24.0,
            "prev_profile_high": 27.0,
            "prev_profile_low": 23.0,
            "is_roll_transition": False,
            "prev_is_roll_transition": False,
            "is_complete": True,
            "prev_is_complete": True,
            "open_price": 22.5,
        }
    )
    # Force the POC tick to 100 so the unsorted same-time row is not used as prior.
    row["prev_poc"] = 100 * float(cfg["tick_size"])
    events = detect_events(trades, row, cfg)
    poc = [e for e in events if e["level_name"] == "poc"][0]
    if poc["approach"] != "from_below":
        raise AssertionError(f"same-timestamp ordering failed: {poc['approach']}")
    if pd.Timestamp(poc["event_ts"]) != touch.tz_convert("UTC"):
        raise AssertionError("event timestamp is not the touching trade")


def run_unit() -> dict:
    test_session_assignment()
    test_partition_equivalence()
    test_same_timestamp_ordering()
    return {
        "session_assignment": "pass",
        "partition_equivalence": "pass",
        "same_event_contamination": "pass",
    }


def _eligible_mask(frame: pd.DataFrame) -> pd.Series:
    return (
        ~frame["is_roll_transition"].astype(bool)
        & ~frame["prev_is_roll_transition"].astype(bool)
        & frame["is_complete"].astype(bool)
        & frame["prev_is_complete"].astype(bool)
    )


def run_data(cfg: dict) -> dict:
    profiles = pd.read_parquet(VP / "data" / "session_profiles.parquet")
    vap = pd.read_parquet(VP / "data" / "session_volume_profile.parquet")
    research = None
    research_path = VP / "data" / "session_research.parquet"
    results = {}

    sums = vap.groupby("session_date")["volume"].sum()
    joined = profiles.set_index("session_date")["total_volume"]
    if not sums.index.equals(joined.index) or not np.array_equal(sums.to_numpy(), joined.to_numpy()):
        # index order may differ
        aligned = joined.reindex(sums.index)
        if not np.array_equal(sums.to_numpy(), aligned.to_numpy()):
            raise AssertionError("volume at price does not sum to total_volume")
    results["volume_conservation"] = "pass"

    poc_vol = vap.merge(profiles[["session_date", "poc_ticks", "poc_volume"]], on="session_date", how="left")
    at_poc = poc_vol[poc_vol["price_ticks"] == poc_vol["poc_ticks"]]
    if not np.array_equal(at_poc["volume"].to_numpy(), at_poc["poc_volume"].to_numpy()):
        raise AssertionError("poc_volume is not the volume at the POC tick")
    max_vol = vap.groupby("session_date")["volume"].max()
    if not np.array_equal(profiles.set_index("session_date")["poc_volume"].reindex(max_vol.index).to_numpy(), max_vol.to_numpy()):
        raise AssertionError("POC is not the maximum volume price")
    results["poc_correctness"] = "pass"

    va_ok = (
        (profiles["value_area_volume"] / profiles["total_volume"] >= float(cfg["value_area_pct"]) - 1e-12)
        & (profiles["val_ticks"] <= profiles["poc_ticks"])
        & (profiles["poc_ticks"] <= profiles["vah_ticks"])
    )
    if not bool(va_ok.all()):
        raise AssertionError("value area failed the 70 percent or containment check")
    results["value_area_correctness"] = "pass"

    tick = float(cfg["tick_size"])
    prices = vap["price"].to_numpy(dtype=np.float64)
    ticks = vap["price_ticks"].to_numpy(dtype=np.int64)
    if np.max(np.abs(prices - ticks * tick)) > 1e-9:
        raise AssertionError("profile prices are not on the NQ tick")
    results["tick_alignment"] = "pass"

    if research_path.exists():
        research = pd.read_parquet(research_path)
        if not (research["prev_session_date"] < research["session_date"]).all():
            raise AssertionError("prev_session_date is not before session_date")
        prev = profiles[["session_date", "poc", "vah", "val"]].rename(
            columns={"session_date": "prev_session_date", "poc": "poc_check", "vah": "vah_check", "val": "val_check"}
        )
        merged = research.merge(prev, on="prev_session_date", how="left")
        if merged[["poc_check", "vah_check", "val_check"]].isna().any().any():
            raise AssertionError("previous profile fields did not match a completed session")
        if not np.allclose(merged["prev_poc"], merged["poc_check"]):
            raise AssertionError("prev_poc does not match the previous session")
        if not np.allclose(merged["prev_vah"], merged["vah_check"]) or not np.allclose(merged["prev_val"], merged["val_check"]):
            raise AssertionError("prev VAH/VAL does not match the previous session")
        results["no_lookahead"] = "pass"
    else:
        results["no_lookahead"] = "pending_research_dataset"

    first = profiles.copy()
    build_profiles(cfg)
    second = pd.read_parquet(VP / "data" / "session_profiles.parquet")
    vap2 = pd.read_parquet(VP / "data" / "session_volume_profile.parquet")
    pd.testing.assert_frame_equal(first.reset_index(drop=True), second.reset_index(drop=True), check_exact=False, rtol=0, atol=0)
    pd.testing.assert_frame_equal(
        vap.sort_values(["session_date", "price_ticks"]).reset_index(drop=True),
        vap2.sort_values(["session_date", "price_ticks"]).reset_index(drop=True),
        check_exact=False,
        rtol=0,
        atol=0,
    )
    results["determinism"] = "pass"
    return results


def run_events(cfg: dict) -> dict:
    events = pd.read_parquet(VP / "data" / "interaction_events.parquet")
    research = pd.read_parquet(VP / "data" / "session_research.parquet")
    if not (research["prev_session_date"] < research["session_date"]).all():
        raise AssertionError("lookahead check failed on research rows")
    bad = 0
    for session, part in events.groupby("session_date"):
        start, end = session_bounds(date.fromisoformat(str(session)[:10]))
        ts = pd.to_datetime(part["event_ts"], utc=True)
        if ((ts < start) | (ts >= end)).any():
            bad += int(((ts < start) | (ts >= end)).sum())
    if bad:
        raise AssertionError(f"{bad} events fall outside the CME session window")
    sample_dates = sorted({str(v)[:10] for v in events["session_date"].unique()})[:2]
    wanted = {}
    for _, row in research.iterrows():
        wanted[date.fromisoformat(str(row["session_date"])[:10])] = row
    rebuilt = []
    targets = {date.fromisoformat(v) for v in sample_dates}
    for session, trades in iter_session_trades(cfg):
        if session not in targets:
            continue
        rebuilt.extend(detect_events(trades, wanted[session], cfg))
        targets.remove(session)
        if not targets:
            break
    rebuilt_frame = pd.DataFrame(rebuilt)
    left = events[events["session_date"].isin(sample_dates)].sort_values(["session_date", "level_name"]).reset_index(drop=True)
    right = rebuilt_frame.sort_values(["session_date", "level_name"]).reset_index(drop=True)
    if len(left) != len(right):
        raise AssertionError("rebuilt event count does not match")
    if not left["approach"].equals(right["approach"]):
        raise AssertionError("rebuilt approach does not match stored events")
    return {"event_timestamp_integrity": "pass", "no_lookahead": "pass"}


def write_status(update: dict) -> dict:
    current = {}
    if STATUS_PATH.exists():
        current = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    current.pop("failed_test", None)
    current.update(update)
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATUS_PATH.write_text(json.dumps(current, indent=2), encoding="utf-8")
    return current


def write_dataset_report(cfg: dict, status: dict) -> None:
    audit = pd.read_csv(VP / "data" / "input_audit.csv")
    profiles = pd.read_parquet(VP / "data" / "session_profiles.parquet")
    files = audit[audit["filename"].astype(str).str.startswith("trades_")]
    failed = files[files["status"] != "ok"]
    rolls = profiles[profiles["is_roll_transition"].astype(bool)]
    lines = [
        "# Dataset report",
        "",
        "## Input",
        "",
        f"- Files expected: {cfg['expected_file_count']}",
        f"- Files in audit: {len(files)}",
        f"- Failed files: {len(failed)}",
        f"- File dates: {files['file_date'].min()} through {files['file_date'].max()}",
        f"- Total trades: {int(files['row_count'].sum())}",
        f"- Total volume: {int(files['total_volume'].sum())}",
        f"- Timestamp coverage: {files['min_ts_event'].min()} to {files['max_ts_event'].max()}",
        "",
        "## CME session construction",
        "",
        "- Timezone: America/New_York, via the standard zone database. EST/EDT offsets are not hardcoded.",
        "- If New York time is at or after 18:00, session_date is that New York calendar date.",
        "- Otherwise session_date is the previous New York calendar date.",
        "- The session window used for events is [18:00, next 18:00). The economic close is 17:00. The maintenance break is the empty interval before 18:00.",
        f"- Sessions created: {len(profiles)}",
        f"- Session dates: {profiles['session_date'].min()} through {profiles['session_date'].max()}",
        f"- Complete sessions (first trade within {cfg['completeness_slack_minutes']} minutes of 18:00 and last trade within {cfg['completeness_slack_minutes']} minutes of 17:00): {int(profiles['is_complete'].sum())}",
        "",
        "## Profile construction",
        "",
        f"- Tick size: {cfg['tick_size']} index points. Price ticks = round(price / tick_size). Databento fixed-point prices are divided by {cfg['price_scale']} when they are still scaled.",
        "- POC: traded price with the most volume. Equal volume resolves to the lower price.",
        f"- Value area: {cfg['value_area_pct']:.0%} of total session volume, expanded from the POC across traded prices only.",
        "- Tie-break: if the next higher and next lower traded prices have equal volume, expand to the lower price.",
        "- Profiles use trade prints. Bars are not used.",
        "",
        "## Roll handling",
        "",
        "- Primary detector: `instrument_id` changes from the previous session, or more than one instrument_id prints inside the session.",
        f"- Fallback, also predeclared: absolute gap between the previous session's last trade and this session's first trade of at least {cfg['roll_gap_points']} points.",
        "- The first session is not a roll unless it contains two instrument ids. There is no prior contract in this file set to compare against.",
        f"- Sessions flagged: {len(rolls)}",
        "- Flagged dates: " + (", ".join(rolls["session_date"].astype(str).tolist()) if len(rolls) else "none"),
        f"- Of which instrument-id changes: {int(profiles['roll_id_change'].sum())}",
        f"- Of which price-gap flags: {int(profiles['roll_gap'].sum())}",
        "- Flagged sessions stay in the profile tables. A mechanism row is excluded when the session or its previous session is flagged, because the prices are not comparable.",
        "",
        "## Validation",
        "",
    ]
    for name in (
        "session_assignment",
        "no_lookahead",
        "volume_conservation",
        "poc_correctness",
        "value_area_correctness",
        "tick_alignment",
        "determinism",
        "partition_equivalence",
        "event_timestamp_integrity",
        "same_event_contamination",
    ):
        lines.append(f"- {name}: {status.get(name, 'not_run')}")
    lines.extend(
        [
            "",
            "## Ordering limitation",
            "",
            "Trades are ordered by `ts_event`, then Databento `sequence`. That is the finest order this schema supports. Approach direction does not use a later sequence at the same timestamp.",
            "",
        ]
    )
    report = VP / "reports" / "DATASET_REPORT.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    cfg = load_config()
    mode = "--unit"
    for arg in sys.argv[1:]:
        if arg.startswith("--"):
            mode = arg
    try:
        if mode == "--unit":
            status = write_status(run_unit())
        elif mode == "--data":
            status = write_status(run_data(cfg))
        elif mode == "--events":
            status = write_status(run_events(cfg))
        else:
            raise SystemExit(f"unknown mode {mode}")
    except Exception as exc:
        status = write_status({"failed_test": f"{exc.__class__.__name__}: {exc}"})
        if (VP / "data" / "session_profiles.parquet").exists() and (VP / "data" / "input_audit.csv").exists():
            write_dataset_report(cfg, status)
        raise
    if mode != "--unit" and (VP / "data" / "session_profiles.parquet").exists():
        write_dataset_report(cfg, status)
    print(json.dumps(status, indent=2), flush=True)


if __name__ == "__main__":
    main()
