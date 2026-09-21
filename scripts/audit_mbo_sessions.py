"""
MBO 50-Session Data Quality Audit Script
Validates all 50 full-state MBO files before strategy development.

Audits per session:
  - Date
  - Snapshot present (action == 'R', F_SNAPSHOT)?
  - Snapshot complete (F_LAST received)?
  - Snapshot initial resting order count
  - Incremental events processed (00:00:00 UTC up to 09:30:00 EDT)
  - Pre-open trades executed
  - 09:30 EDT Best Bid, Best Ask, and Inside Spread
  - Active resting orders at 09:30 EDT
  - Orphan Cancels & Modifies (must be 0 under official semantics)
  - Crossed book events (bid >= ask during pre-open)
  - Audit Status (PASS / FLAG)
"""

import sys
import time
from pathlib import Path
import pandas as pd
import databento as db

# Add project root to path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent))
from common.order_book import LimitOrderBook

DATA_DIR = Path("d:/NQ-2/data/mbo_full_state_50")
REPORT_DIR = Path("d:/NQ-2/reports")
REPORT_DIR.mkdir(parents=True, exist_ok=True)

mbo_sessions = [
    "2026-07-08", "2026-07-09", "2026-07-10", "2026-07-13", "2026-07-14", "2026-07-15",
    "2026-07-16", "2026-07-17", "2026-07-20", "2026-07-21", "2026-07-22",
    "2026-07-23", "2026-07-24", "2026-07-27", "2026-07-28", "2026-07-29",
    "2026-07-30", "2026-07-31", "2026-08-03", "2026-08-04", "2026-08-05",
    "2026-08-06", "2026-08-07", "2026-08-10", "2026-08-11", "2026-08-12",
    "2026-08-13", "2026-08-14", "2026-08-17", "2026-08-18", "2026-08-19",
    "2026-08-20", "2026-08-21", "2026-08-24", "2026-08-25", "2026-08-26",
    "2026-08-27", "2026-08-28", "2026-08-31", "2026-09-01", "2026-09-02",
    "2026-09-03", "2026-09-04", "2026-09-08", "2026-09-09", "2026-09-10",
    "2026-09-11", "2026-09-14", "2026-09-15", "2026-09-16"
]


def audit_session(file_path: Path, date_str: str) -> dict:
    if not file_path.exists():
        return {"date": date_str, "status": "MISSING_FILE"}

    file_size_mb = file_path.stat().st_size / (1024**2)
    if file_size_mb < 50:
        return {"date": date_str, "file_size_mb": round(file_size_mb, 1), "status": "FILE_TOO_SMALL"}

    lob = LimitOrderBook()
    # 09:30:00 EDT = 13:30:00 UTC
    ny_open_ns = pd.Timestamp(f"{date_str}T13:30:00Z").value

    data = db.DBNStore.from_file(file_path)
    crossed_count = 0
    check_crossed_interval = 50_000

    for record in data:
        if not isinstance(record, db.MBOMsg):
            continue

        flags = record.flags
        if bool(flags & db.RecordFlags.F_SNAPSHOT):
            lob.apply_record(record, is_snapshot=True, is_last_snapshot=bool(flags & db.RecordFlags.F_LAST))
            continue

        if record.ts_event >= ny_open_ns:
            break

        lob.apply_record(record, is_snapshot=False)

        if lob.events_processed % check_crossed_interval == 0:
            if len(lob.bids) > 0 and len(lob.asks) > 0:
                if lob.bids.peekitem(-1)[0] >= lob.asks.peekitem(0)[0]:
                    crossed_count += 1

    best_bid, best_ask, spread = lob.get_bbo()

    status = "PASS"
    flags_list = []
    if not lob.snapshot_complete:
        status = "FLAG"
        flags_list.append("INCOMPLETE_SNAPSHOT")
    if lob.orphan_cancels > 0:
        status = "FLAG"
        flags_list.append(f"ORPHAN_CANCELS({lob.orphan_cancels})")
    if lob.orphan_modifies > 0:
        status = "FLAG"
        flags_list.append(f"ORPHAN_MODIFIES({lob.orphan_modifies})")
    if spread <= 0 or spread > 2.5:
        status = "FLAG"
        flags_list.append(f"ABNORMAL_SPREAD({spread:.2f})")

    return {
        "date": date_str,
        "file_size_mb": round(file_size_mb, 1),
        "snapshot_present": lob.snapshot_orders > 0,
        "snapshot_complete": lob.snapshot_complete,
        "snapshot_orders": lob.snapshot_orders,
        "events_to_0930": lob.events_processed,
        "trades_to_0930": lob.trades_count,
        "bbo_bid": round(best_bid[0] / 1e9, 2) if best_bid[0] else 0.0,
        "bbo_ask": round(best_ask[0] / 1e9, 2) if best_ask[0] else 0.0,
        "spread_pts": round(spread, 2),
        "active_orders_0930": len(lob.orders),
        "orphan_cancels": lob.orphan_cancels,
        "orphan_modifies": lob.orphan_modifies,
        "crossed_checks_flagged": crossed_count,
        "status": status,
        "notes": "; ".join(flags_list) if flags_list else "CLEAN"
    }


def audit_session_wrapper(date_str: str) -> dict:
    file_path = DATA_DIR / f"mbo_{date_str}.dbn.zst"
    t0 = time.time()
    res = audit_session(file_path, date_str)
    elapsed = time.time() - t0
    res["elapsed_s"] = round(elapsed, 1)
    print(f"[{res['date']}] Status: {res.get('status')} | Spread: {res.get('spread_pts', 0)} pts | Active: {res.get('active_orders_0930', 0)} | Orphans: {res.get('orphan_cancels', 0)} ({elapsed:.1f}s)", flush=True)
    return res


def main():
    print("==========================================================")
    print("        MBO 50-SESSION DATA QUALITY AUDIT SUITE           ")
    print("==========================================================")
    print(f"Target Directory: {DATA_DIR}")
    print(f"Total Sessions:   {len(mbo_sessions)}")
    print(f"Parallel Workers: 3\n")

    results = []
    t_start = time.time()

    from concurrent.futures import ProcessPoolExecutor, as_completed
    with ProcessPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(audit_session_wrapper, date_str): date_str for date_str in mbo_sessions}
        for future in as_completed(futures):
            try:
                res = future.result()
                results.append(res)
            except Exception as e:
                date_str = futures[future]
                print(f"[{date_str}] CRITICAL ERROR: {e}")
                results.append({"date": date_str, "status": "ERROR", "notes": str(e)})

    # Sort results chronologically
    results.sort(key=lambda x: x.get("date", ""))
    df = pd.DataFrame(results)

    # Save outputs
    csv_path = REPORT_DIR / "mbo_50_data_quality_audit.csv"
    md_path = REPORT_DIR / "mbo_50_data_quality_audit.md"

    df.to_csv(csv_path, index=False)

    passed_count = (df["status"] == "PASS").sum()
    total_count = len(df)
    total_elapsed_min = (time.time() - t_start) / 60

    with open(md_path, "w") as f:
        f.write("# 50-Session MBO Data Quality Audit Report\n\n")
        f.write(f"- **Total Sessions Audited:** {total_count}\n")
        f.write(f"- **Passed (100% Integrity):** {passed_count}/{total_count}\n")
        f.write(f"- **Elapsed Audit Time:** {total_elapsed_min:.1f} minutes\n\n")
        f.write("## Session Breakdown\n\n")
        f.write(df.to_markdown(index=False))
        f.write("\n")

    print("\n==========================================================")
    print(f"AUDIT COMPLETE: {passed_count}/{total_count} sessions PASSED in {total_elapsed_min:.1f} min.")
    print(f"Reports saved to:\n  {csv_path}\n  {md_path}")
    print("==========================================================")


if __name__ == "__main__":
    main()
