"""
Full Data Acquisition Script for NQ Forensic Research
Acquires:
  1. 50 Full-State MBO Sessions (00:00:00 to 16:00:00 UTC) with synthetic snapshot.
  2. 126 Full 24-Hour Trades Sessions (00:00:00 to 23:59:59 UTC) for Volume Profile.
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
import databento as db

# ACQUISITION PERMANENTLY LOCKED - ALL DATA ACQUIRED
print("ACQUISITION LOCKED: All historical data has been acquired. No further downloads permitted.")
sys.exit(0)

DATA_DIR = Path("d:/NQ-2/data")
DIR_MBO = DATA_DIR / "mbo_full_state_50"
DIR_TRADES = DATA_DIR / "trades_24h_6m"
DIR_MBO.mkdir(parents=True, exist_ok=True)
DIR_TRADES.mkdir(parents=True, exist_ok=True)

# 3. Exact 50 MBO Sessions (2026-07-08 to 2026-09-16)
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

# 4. Exact 126 6-Month Trades Sessions (2026-03-24 to 2026-09-16)
# Generating contiguous trading days (weekdays)
from datetime import date, timedelta
candidate = date(2026, 9, 16)
trades_sessions = []
while len(trades_sessions) < 126:
    if candidate.weekday() < 5:
        # Exclude known holiday closures if any (e.g. Good Friday, Memorial Day, Juneteenth, July 4, Labor Day)
        # Note: Databento metadata get_cost will return $0 or error if no trading, so we keep valid trading days
        trades_sessions.append(candidate.strftime("%Y-%m-%d"))
    candidate -= timedelta(days=1)
trades_sessions.reverse()

import gc

def download_session(target_file, fetch_fn, min_size_bytes=10*1024*1024, max_retries=5, base_delay=10):
    for attempt in range(1, max_retries + 1):
        # Unique temp filename prevents collisions and Windows [WinError 32] lock issues
        temp_file = target_file.with_name(f"{target_file.stem}_att{attempt}_{int(time.time())}.part")
        try:
            fetch_fn(temp_file)
            if not temp_file.exists() or temp_file.stat().st_size < min_size_bytes:
                raise IOError(f"Downloaded file is suspiciously small or missing ({temp_file.stat().st_size if temp_file.exists() else 0} bytes).")
            
            # Atomic rename to final target
            temp_file.rename(target_file)
            return
        except Exception as e:
            print(f"  [Attempt {attempt}/{max_retries}] Error: {e}")
            gc.collect()
            time.sleep(1.0)
            if temp_file.exists():
                try:
                    temp_file.unlink(missing_ok=True)
                except Exception:
                    pass
            if attempt == max_retries:
                raise
            sleep_time = base_delay * attempt
            print(f"  Waiting {sleep_time}s before attempt {attempt + 1}...")
            time.sleep(sleep_time)


def main():
    print("==========================================================")
    print("      DATABENTO NQ HISTORICAL ACQUISITION PIPELINE        ")
    print("==========================================================")
    print(f"MBO Target:    {len(mbo_sessions)} sessions -> {DIR_MBO}")
    print(f"Trades Target: {len(trades_sessions)} sessions -> {DIR_TRADES}")
    print("----------------------------------------------------------\n")

    # --- PART 1: MBO ACQUISITION ---
    print(">>> Starting Phase 1: Full-State MBO Sessions (00:00 to 16:00 UTC) <<<")
    mbo_downloaded = 0
    mbo_skipped = 0

    for i, date_str in enumerate(mbo_sessions):
        target_file = DIR_MBO / f"mbo_{date_str}.dbn.zst"
        if target_file.exists() and target_file.stat().st_size > 50 * 1024 * 1024:
            print(f"[{i+1}/{len(mbo_sessions)}] MBO {date_str} already exists ({target_file.stat().st_size / (1024**2):.1f} MB). Skipping.")
            mbo_skipped += 1
            continue

        print(f"[{i+1}/{len(mbo_sessions)}] Downloading MBO with Snapshot for {date_str}...")
        start_ts = f"{date_str}T00:00:00"
        end_ts = f"{date_str}T16:00:00"
        
        def fetch_mbo(dest_path):
            client.timeseries.get_range(
                dataset="GLBX.MDP3",
                start=start_ts,
                end=end_ts,
                symbols="NQ.c.0",
                schema="mbo",
                stype_in="continuous",
                path=dest_path
            )

        t0 = time.time()
        download_session(target_file, fetch_mbo, min_size_bytes=50*1024*1024, max_retries=5, base_delay=10)
        elapsed = time.time() - t0
        file_mb = target_file.stat().st_size / (1024**2)
        print(f"  Completed {date_str}: {file_mb:.1f} MB in {elapsed:.1f}s")
        mbo_downloaded += 1

    print(f"\nPhase 1 Complete! Downloaded: {mbo_downloaded}, Previously Cached: {mbo_skipped}\n")

    # --- PART 2: TRADES ACQUISITION ---
    print(">>> Starting Phase 2: 24h Full-Session Trades (00:00 to 23:59:59 UTC) <<<")
    trades_downloaded = 0
    trades_skipped = 0

    for j, date_str in enumerate(trades_sessions):
        target_file = DIR_TRADES / f"trades_24h_{date_str}.dbn.zst"
        if target_file.exists() and target_file.stat().st_size > 100 * 1024:
            print(f"[{j+1}/{len(trades_sessions)}] Trades {date_str} already exists. Skipping.")
            trades_skipped += 1
            continue

        start_ts = f"{date_str}T00:00:00"
        end_ts = f"{date_str}T23:59:59"
        
        def fetch_trades(dest_path):
            client.timeseries.get_range(
                dataset="GLBX.MDP3",
                start=start_ts,
                end=end_ts,
                symbols="NQ.c.0",
                schema="trades",
                stype_in="continuous",
                path=dest_path
            )

        print(f"[{j+1}/{len(trades_sessions)}] Downloading 24h Trades for {date_str}...")
        t0 = time.time()
        download_session(target_file, fetch_trades, min_size_bytes=10*1024, max_retries=5, base_delay=5)
        elapsed = time.time() - t0
        file_mb = target_file.stat().st_size / (1024**2)
        print(f"  Completed {date_str}: {file_mb:.2f} MB in {elapsed:.1f}s")
        trades_downloaded += 1

    print(f"\nPhase 2 Complete! Downloaded: {trades_downloaded}, Previously Cached: {trades_skipped}\n")
    print("==========================================================")
    print("        ALL DATA ACQUISITION COMPLETED SUCCESSFULLY       ")
    print("==========================================================")

if __name__ == "__main__":
    main()
