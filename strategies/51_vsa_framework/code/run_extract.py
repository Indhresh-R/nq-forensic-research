"""
Step 2 runner: extract frozen A/B/C event dataset + audit.

No forward returns. No DOWN_CLOSE / FAIL_CLEAR_ND outcomes.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
CODE = Path(__file__).resolve().parent
OUT = Path(__file__).resolve().parents[1] / "results"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(CODE))

from common.nq_session import load_nq
from common.splits import split_of

from audit import audit_events, write_audit
from extract import extract_events


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print("Loading NQ 1m…")
    df = load_nq().sort_values("ts").reset_index(drop=True)
    print(f"1m rows={len(df):,}")

    print("Extracting VSA events (no outcomes)…")
    events, bars, meta = extract_events(df)
    failed = meta.pop("_failed_df", pd.DataFrame())

    if len(events):
        events["split"] = events["year"].map(lambda y: split_of(int(y)))
    else:
        events["split"] = pd.Series(dtype=str)

    events_path = OUT / "events.parquet"
    bars_path = OUT / "bars_15m.parquet"
    meta_path = OUT / "extract_meta.json"
    counts_path = OUT / "event_counts.csv"
    audit_path = OUT / "audit_report.json"
    funnel_path = OUT / "funnel.json"
    failed_path = OUT / "failed_confirmations.parquet"

    events.to_parquet(events_path, index=False)
    bars.to_parquet(bars_path, index=False)
    if len(failed):
        failed.to_parquet(failed_path, index=False)

    funnel = meta.get("funnel", {})
    funnel_path.write_text(json.dumps(funnel, indent=2), encoding="utf-8")
    meta_path.write_text(json.dumps(meta, indent=2, default=str), encoding="utf-8")

    if len(events):
        counts = (
            events.groupby(["split", "event_class"], as_index=False)
            .size()
            .rename(columns={"size": "n"})
        )
    else:
        counts = pd.DataFrame(columns=["split", "event_class", "n"])
    counts.to_csv(counts_path, index=False)

    print("Auditing…")
    report = audit_events(events, bars)
    # strip non-serializable if any
    report_out = {
        "checks": report["checks"],
        "n_events": report["n_events"],
        "all_pass": report["all_pass"],
        "meta_summary": {
            "n_1m": meta.get("n_1m"),
            "n_15m": meta.get("n_15m"),
            "n_segments": meta.get("n_segments"),
            "class_counts": meta.get("class_counts"),
            "n_failed_confirm_attempts": meta.get("n_failed_confirm_attempts"),
        },
    }
    write_audit(report_out, audit_path)

    print(json.dumps({"meta": {k: meta[k] for k in meta if k != "_failed_df"}, "audit_all_pass": report["all_pass"]}, indent=2, default=str))
    print(counts.to_string(index=False) if len(counts) else "(no events)")
    print(f"Wrote {events_path}")
    print(f"Audit pass={report['all_pass']} -> {audit_path}")

    if not report["all_pass"]:
        failed_checks = {k: v for k, v in report["checks"].items() if not v["pass"]}
        print("FAILED CHECKS:", json.dumps(failed_checks, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
