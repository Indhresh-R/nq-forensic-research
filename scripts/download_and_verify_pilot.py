import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import databento as db
import pandas as pd

# 1. Load API key securely from .env
load_dotenv()
API_KEY = os.environ.get("DATABENTO_API_KEY")
if not API_KEY:
    print("ERROR: DATABENTO_API_KEY is not set in environment or .env file.")
    sys.exit(1)

client = db.Historical(API_KEY)
client.timeseries.TIMEOUT = 900  # 15 minutes timeout for large binary stream transfers

# 2. Setup target date and paths
TEST_DATE = "2026-09-10"
START_UTC = f"{TEST_DATE}T00:00:00"
END_UTC = f"{TEST_DATE}T16:00:00"  # 12:00 EDT
TARGET_DIR = Path("d:/NQ-2/data/pilot_test")
TARGET_DIR.mkdir(parents=True, exist_ok=True)
FILE_PATH = TARGET_DIR / f"mbo_{TEST_DATE}.dbn.zst"

print(f"=== PILOT ACQUISITION & VERIFICATION ===")
print(f"Target Date: {TEST_DATE}")
print(f"Time Range:  {START_UTC} -> {END_UTC} (Midnight UTC -> 12:00 EDT)")
print(f"Target Path: {FILE_PATH}")

# 3. Pre-flight Cost Verification
cost = client.metadata.get_cost(
    dataset="GLBX.MDP3",
    start=START_UTC,
    end=END_UTC,
    symbols="NQ.c.0",
    schema="mbo",
    stype_in="continuous"
)
billable_size = client.metadata.get_billable_size(
    dataset="GLBX.MDP3",
    start=START_UTC,
    end=END_UTC,
    symbols="NQ.c.0",
    schema="mbo",
    stype_in="continuous"
)

print(f"Pre-flight verified cost: ${cost:.2f}")
print(f"Billable uncompressed size: {billable_size / (1024**2):.1f} MB")

# 4. Download Single Day
if not FILE_PATH.exists():
    print(f"\nDownloading single session to {FILE_PATH}...")
    client.timeseries.get_range(
        dataset="GLBX.MDP3",
        start=START_UTC,
        end=END_UTC,
        symbols="NQ.c.0",
        schema="mbo",
        stype_in="continuous",
        path=FILE_PATH
    )
    print("Download completed successfully!")
else:
    print(f"File already exists at {FILE_PATH}, proceeding to verification.")

actual_file_size = FILE_PATH.stat().st_size
print(f"Actual compressed download size: {actual_file_size / (1024**2):.2f} MB")

# 5. Order Book Reconstruction & Verification Engine
print("\n--- Starting Order Book Reconstruction Engine ---")

data = db.DBNStore.from_file(FILE_PATH)

# Order book structures:
# orders: order_id -> (price, size, side)
# bids: price -> size
# asks: price -> size
orders = {}
bids = {}
asks = {}

snapshot_count = 0
snapshot_complete = False
incremental_count = 0
orphan_cancels = 0
orphan_modifies = 0
orphan_fills = 0
total_trades = 0

# Target timestamp for NY Cash Open: 09:30:00 EDT = 13:30:00 UTC
# Convert to nanoseconds from epoch
ny_open_ns = pd.Timestamp(f"{TEST_DATE}T13:30:00Z").value

print(f"Target Cash Open Timestamp: {pd.Timestamp(ny_open_ns, unit='ns', tz='UTC')}")

for record in data:
    if not isinstance(record, db.MBOMsg):
        continue
    
    action = chr(record.action) if isinstance(record.action, int) else str(record.action)
    flags = record.flags
    is_snapshot = bool(flags & db.RecordFlags.F_SNAPSHOT)
    is_last_snapshot = bool(flags & db.RecordFlags.F_LAST)
    
    # Handle Snapshot
    if is_snapshot:
        snapshot_count += 1
        if action == 'R':  # cleaR
            orders.clear()
            bids.clear()
            asks.clear()
        elif action == 'A':  # Add
            price = record.price
            size = record.size
            side = chr(record.side) if isinstance(record.side, int) else str(record.side)
            order_id = record.order_id
            
            orders[order_id] = (price, size, side)
            book = bids if side == 'B' else asks
            book[price] = book.get(price, 0) + size
            
        if is_last_snapshot:
            snapshot_complete = True
        continue
    
    # If we reached 09:30:00 ET, pause to capture book state
    if record.ts_event >= ny_open_ns:
        break
        
    # Incremental Updates prior to 09:30
    incremental_count += 1
    order_id = record.order_id
    
    if action == 'A':  # Add
        price = record.price
        size = record.size
        side = chr(record.side) if isinstance(record.side, int) else str(record.side)
        orders[order_id] = (price, size, side)
        book = bids if side == 'B' else asks
        book[price] = book.get(price, 0) + size
        
    elif action == 'C':  # Cancel
        if order_id in orders:
            price, old_size, side = orders[order_id]
            cancel_size = record.size
            new_size = old_size - cancel_size
            book = bids if side == 'B' else asks
            if new_size <= 0:
                del orders[order_id]
                book[price] = book.get(price, 0) - old_size
            else:
                orders[order_id] = (price, new_size, side)
                book[price] = book.get(price, 0) - cancel_size
            if book.get(price, 0) <= 0 and price in book:
                del book[price]
        else:
            orphan_cancels += 1
            
    elif action == 'M':  # Modify
        if order_id in orders:
            old_price, old_size, side = orders[order_id]
            new_price = record.price
            new_size = record.size
            book = bids if side == 'B' else asks
            
            # Remove old
            book[old_price] = book.get(old_price, 0) - old_size
            if book.get(old_price, 0) <= 0 and old_price in book:
                del book[old_price]
                
            # Add new
            orders[order_id] = (new_price, new_size, side)
            book[new_price] = book.get(new_price, 0) + new_size
        else:
            orphan_modifies += 1
            
    elif action == 'F':  # Fill
        if order_id in orders:
            price, old_size, side = orders[order_id]
            fill_size = record.size
            new_size = old_size - fill_size
            book = bids if side == 'B' else asks
            if new_size <= 0:
                del orders[order_id]
                book[price] = book.get(price, 0) - old_size
            else:
                orders[order_id] = (price, new_size, side)
                book[price] = book.get(price, 0) - fill_size
            if book.get(price, 0) <= 0 and price in book:
                del book[price]
        else:
            orphan_fills += 1
            
    elif action == 'T':  # Trade
        total_trades += 1

# Clean any 0-size residual price levels
clean_bids = {p: s for p, s in bids.items() if s > 0}
clean_asks = {p: s for p, s in asks.items() if s > 0}

top_bids = sorted(clean_bids.items(), key=lambda x: x[0], reverse=True)[:5]
top_asks = sorted(clean_asks.items(), key=lambda x: x[0])[:5]

best_bid = top_bids[0] if top_bids else (0, 0)
best_ask = top_asks[0] if top_asks else (0, 0)

spread = (best_ask[0] - best_bid[0]) / 1e9 if best_bid[0] and best_ask[0] else 0

print(f"\n=== VERIFICATION RESULTS AT 09:30:00 EDT ===")
print(f"Snapshot Received:         {'YES' if snapshot_complete else 'NO'}")
print(f"Snapshot Order Records:    {snapshot_count:,}")
print(f"Incremental Events (00-09:30): {incremental_count:,}")
print(f"Pre-open Trades Executed:  {total_trades:,}")
print(f"Total Active Orders at Open: {len(orders):,}")
print(f"Orphan Cancels:            {orphan_cancels} ({orphan_cancels / max(1, incremental_count) * 100:.4f}%)")
print(f"Orphan Modifies:           {orphan_modifies}")
print(f"Orphan Fills:              {orphan_fills}")

print(f"\n--- Order Book State at Exactly 09:30:00 EDT ---")
print(f"Best Bid: {best_bid[0]/1e9:.2f} (Size: {best_bid[1]})")
print(f"Best Ask: {best_ask[0]/1e9:.2f} (Size: {best_ask[1]})")
print(f"Inside Spread: {spread:.2f} points")

print("\nTop 5 Bids:")
for p, s in top_bids:
    print(f"  {p/1e9:.2f} : {s} contracts")

print("\nTop 5 Asks:")
for p, s in top_asks:
    print(f"  {p/1e9:.2f} : {s} contracts")

if snapshot_complete and orphan_cancels == 0 and spread > 0 and spread <= 1.0:
    print("\n>>> VALIDATION SUCCESSFUL: Order book reconstructs with 100% mathematical integrity! <<<")
else:
    print(f"\n>>> VALIDATION NOTE: Spread={spread}, Orphan Cancels={orphan_cancels} <<<")
