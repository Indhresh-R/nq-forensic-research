"""
MBO Replay & Microstructure Sampling Engine
Strategy 44: Hypotheses H01 & H02 (Aggressive Order Flow Delta & MBO Order Dynamics)

Samples every 1.0s between 09:30:00 and 12:00:00 EDT (13:30 to 16:00 UTC):
  - L1 & L5 Bid/Ask Depth: q_b1, q_a1, q_b5, q_a5
  - BBO, Spread, Mid-price
  - OBI_1, OBI_5
  - Aggressive Trade Volume (Buy vs Sell): trade_b_1s, trade_a_1s
  - Row t contains only events with ts_event in (t - 1s, t]. [t, t + 1s) belongs to row t+1.
  - Aggressive Trade Counts: trade_cnt_b_1s, trade_cnt_a_1s
  - Passive Order Fills: fill_b_1s, fill_a_1s
  - Limit Order Adds: add_b_1s, add_a_1s
  - Limit Order Cancels: cancel_b_1s, cancel_a_1s
  - Forward Mid-Price Changes: 1s, 5s, 15s, 60s, 300s
  - Forward Bid/Ask Prices: for execution feasibility testing
"""

import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd
import databento as db
from concurrent.futures import ProcessPoolExecutor, as_completed

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(PROJECT_ROOT))
from common.order_book import LimitOrderBook
from research.mbo.clock import snapshot_bin_index

DATA_DIR = PROJECT_ROOT / "data" / "mbo_full_state_50"
OUTPUT_DIR = PROJECT_ROOT / "strategies" / "44_mbo_orderflow" / "results" / "sampled_features"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

IS_SESSIONS = [
    "2026-07-08", "2026-07-09", "2026-07-10", "2026-07-13", "2026-07-14", "2026-07-15",
    "2026-07-16", "2026-07-17", "2026-07-20", "2026-07-21", "2026-07-22", "2026-07-23",
    "2026-07-24", "2026-07-27", "2026-07-28", "2026-07-29", "2026-07-30", "2026-07-31",
    "2026-08-03", "2026-08-04", "2026-08-05", "2026-08-06", "2026-08-07", "2026-08-10",
    "2026-08-11", "2026-08-12"
]

FLOW_COUNT_COLS = (
    "trade_b_1s", "trade_a_1s", "trade_cnt_b_1s", "trade_cnt_a_1s",
    "fill_b_1s", "fill_a_1s", "add_b_1s", "add_a_1s", "cancel_b_1s", "cancel_a_1s",
)


def process_session_h02(date_str: str, force: bool = False) -> Path:
    """
    Extracts 1-second continuous order flow metrics (trades, fills, adds, cancels)
    and merges with reconstructed L3 order book state for date_str.
    """
    mbo_file = DATA_DIR / f"mbo_{date_str}.dbn.zst"
    if not mbo_file.exists():
        raise FileNotFoundError(f"Missing MBO file: {mbo_file}")

    out_file = OUTPUT_DIR / f"h02_samples_{date_str}.parquet"
    if out_file.exists() and not force:
        return out_file

    h01_file = OUTPUT_DIR / f"h01_samples_{date_str}.parquet"
    if not h01_file.exists():
        # Fallback to creating h01_samples first
        from code.replay_mbo import process_session_h01
        process_session_h01(date_str)

    t0 = time.time()
    df = pd.read_parquet(h01_file).copy()
    n_bins = len(df)
    ny_open_ns = df["ts_ns"].iloc[0]
    ny_close_ns = df["ts_ns"].iloc[-1]
    step_ns = int(1e9)

    # Pre-allocate numpy arrays for 1s bins
    trade_b = np.zeros(n_bins, dtype=np.int32)
    trade_a = np.zeros(n_bins, dtype=np.int32)
    cnt_b = np.zeros(n_bins, dtype=np.int32)
    cnt_a = np.zeros(n_bins, dtype=np.int32)
    fill_b = np.zeros(n_bins, dtype=np.int32)
    fill_a = np.zeros(n_bins, dtype=np.int32)
    add_b = np.zeros(n_bins, dtype=np.int32)
    add_a = np.zeros(n_bins, dtype=np.int32)
    cancel_b = np.zeros(n_bins, dtype=np.int32)
    cancel_a = np.zeros(n_bins, dtype=np.int32)
    flow_max_ts = np.zeros(n_bins, dtype=np.int64)

    data = db.DBNStore.from_file(mbo_file)
    recs = 0

    for record in data:
        if not isinstance(record, db.MBOMsg):
            continue
        ts = record.ts_event
        if ts <= ny_open_ns - step_ns:
            continue
        if ts > ny_close_ns:
            break

        idx = snapshot_bin_index(ts, ny_open_ns, ny_close_ns, step_ns, n_bins)
        if idx is not None:
            action = chr(record.action) if isinstance(record.action, int) else str(record.action)
            side = chr(record.side) if isinstance(record.side, int) else str(record.side)
            size = record.size

            if action == 'T':
                if side == 'B':  # Buyer lifting ask
                    trade_b[idx] += size
                    cnt_b[idx] += 1
                elif side == 'A':  # Seller hitting bid
                    trade_a[idx] += size
                    cnt_a[idx] += 1
            elif action == 'F':
                if side == 'B':
                    fill_b[idx] += size
                elif side == 'A':
                    fill_a[idx] += size
            elif action == 'A':
                if side == 'B':
                    add_b[idx] += size
                elif side == 'A':
                    add_a[idx] += size
            elif action == 'C':
                if side == 'B':
                    cancel_b[idx] += size
                elif side == 'A':
                    cancel_a[idx] += size
            if ts > flow_max_ts[idx]:
                flow_max_ts[idx] = ts

        recs += 1

    df["trade_b_1s"] = trade_b
    df["trade_a_1s"] = trade_a
    df["trade_cnt_b_1s"] = cnt_b
    df["trade_cnt_a_1s"] = cnt_a
    df["fill_b_1s"] = fill_b
    df["fill_a_1s"] = fill_a
    df["add_b_1s"] = add_b
    df["add_a_1s"] = add_a
    df["cancel_b_1s"] = cancel_b
    df["cancel_a_1s"] = cancel_a
    df["flow_max_ts_ns"] = flow_max_ts

    # Execution feasibility forward bid/ask prices
    df["fwd_bid_1s"] = df["bid_px"].shift(-1)
    df["fwd_ask_1s"] = df["ask_px"].shift(-1)
    df["fwd_bid_5s"] = df["bid_px"].shift(-5)
    df["fwd_ask_5s"] = df["ask_px"].shift(-5)
    df["fwd_bid_15s"] = df["bid_px"].shift(-15)
    df["fwd_ask_15s"] = df["ask_px"].shift(-15)
    df["fwd_bid_60s"] = df["bid_px"].shift(-60)
    df["fwd_ask_60s"] = df["ask_px"].shift(-60)
    df["fwd_bid_300s"] = df["bid_px"].shift(-300)
    df["fwd_ask_300s"] = df["ask_px"].shift(-300)

    df.to_parquet(out_file, index=False)
    elapsed = time.time() - t0
    print(f"[{date_str}] Sampled {len(df)} 1s rows ({recs:,} events) in {elapsed:.1f}s -> {out_file.name}", flush=True)
    return out_file


def run_in_sample_batch_h02(max_workers: int = 3, force: bool = False):
    print("==========================================================")
    print("   H02 IN-SAMPLE ORDER FLOW & MBO SAMPLING (26 DATES)     ")
    print("==========================================================")
    print(f"Target Directory: {DATA_DIR}")
    print(f"Sessions:         {len(IS_SESSIONS)}")
    print(f"Workers:          {max_workers}\n")

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_session_h02, d, force): d for d in IS_SESSIONS}
        for future in as_completed(futures):
            date_str = futures[future]
            try:
                out_p = future.result()
            except Exception as e:
                print(f"[{date_str}] ERROR: {e}", flush=True)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--all-is":
            run_in_sample_batch_h02(max_workers=3, force="--rebuild" in sys.argv)
        elif sys.argv[1] == "--rebuild":
            run_in_sample_batch_h02(max_workers=3, force=True)
        else:
            process_session_h02(sys.argv[1], force="--rebuild" in sys.argv)
    else:
        run_in_sample_batch_h02(max_workers=3)
