"""
Step 2 runner: extract frozen A/B/C event dataset + audit.

No forward returns. No leave-range outcomes.
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

    print("Extracting events (no outcomes)…")
    events, bars, meta = extract_events(df)

    if len(events):
        events["split"] = events["year"].map(lambda y: split_of(int(y)))
    else:
        events["split"] = pd.Series(dtype=str)

    events_path = OUT / "events.parquet"
    bars_path = OUT / "bars_15m.parquet"
    meta_path = OUT / "extract_meta.json"
    counts_path = OUT / "event_counts.csv"
    audit_path = OUT / "audit_report.json"

    # Drop bulky trs list from meta file side; save separately
    trs = meta.pop("trs", [])
    events.to_parquet(events_path, index=False)
    # bars: keep audit columns; drop nothing essential
    bars.to_parquet(bars_path, index=False)
    pd.DataFrame(trs).to_parquet(OUT / "trading_ranges.parquet", index=False)

    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    if "funnel" in meta:
        (OUT / "funnel.json").write_text(json.dumps(meta["funnel"], indent=2), encoding="utf-8")

    if len(events):
        counts = (
            events.groupby(["split", "event_class", "kind"], as_index=False)
            .size()
            .rename(columns={"size": "n"})
        )
    else:
        counts = pd.DataFrame(columns=["split", "event_class", "kind", "n"])
    counts.to_csv(counts_path, index=False)

    print("Auditing…")
    report = audit_events(events, bars)
    report["meta"] = meta
    write_audit(report, audit_path)

    print(json.dumps({"meta": meta, "audit_all_pass": report["all_pass"]}, indent=2))
    print(counts.to_string(index=False) if len(counts) else "(no events)")
    print(f"Wrote {events_path}")
    print(f"Audit pass={report['all_pass']} -> {audit_path}")

    if not report["all_pass"]:
        failed = {k: v for k, v in report["checks"].items() if not v["pass"]}
        print("FAILED CHECKS:", json.dumps(failed, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
