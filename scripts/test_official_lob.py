import databento as db
import pandas as pd
from sortedcontainers import SortedDict
from pathlib import Path

FILE_PATH = Path("d:/NQ-2/data/pilot_test/mbo_2026-09-10.dbn.zst")
data = db.DBNStore.from_file(FILE_PATH)

# Official Databento Limit Order Book implementation
# Using SortedDict for price levels, dict for order lookup
class DatabentoOfficialLOB:
    def __init__(self):
        self.orders = {}  # order_id -> (price, size, side)
        self.bids = SortedDict()  # price -> total_size
        self.asks = SortedDict()  # price -> total_size
        
        self.snapshot_orders = 0
        self.snapshot_complete = False
        self.events_processed = 0
        self.orphan_cancels = 0
        self.orphan_modifies = 0
        self.trades_count = 0
        self.fills_count = 0

    def clear(self):
        self.orders.clear()
        self.bids.clear()
        self.asks.clear()

    def add(self, order_id, price, size, side):
        self.orders[order_id] = (price, size, side)
        book = self.bids if side == 'B' else self.asks
        book[price] = book.get(price, 0) + size

    def cancel(self, order_id, cancel_size):
        if order_id in self.orders:
            price, old_size, side = self.orders[order_id]
            book = self.bids if side == 'B' else self.asks
            
            if cancel_size >= old_size:
                del self.orders[order_id]
                book[price] -= old_size
            else:
                self.orders[order_id] = (price, old_size - cancel_size, side)
                book[price] -= cancel_size
                
            if book[price] <= 0:
                del book[price]
        else:
            self.orphan_cancels += 1

    def modify(self, order_id, new_price, new_size):
        if order_id in self.orders:
            old_price, old_size, side = self.orders[order_id]
            book = self.bids if side == 'B' else self.asks
            
            book[old_price] -= old_size
            if book[old_price] <= 0:
                del book[old_price]
                
            self.orders[order_id] = (new_price, new_size, side)
            book[new_price] = book.get(new_price, 0) + new_size
        else:
            self.orphan_modifies += 1

    def get_bbo(self):
        best_bid = self.bids.peekitem(-1) if len(self.bids) > 0 else (0, 0)
        best_ask = self.asks.peekitem(0) if len(self.asks) > 0 else (0, 0)
        spread = (best_ask[0] - best_bid[0]) / 1e9 if best_bid[0] and best_ask[0] else 0
        return best_bid, best_ask, spread

    def get_depth(self, n=5):
        # Top n bids (highest to lowest)
        top_bids = []
        for p in reversed(self.bids.keys()[-n:]):
            top_bids.append((p, self.bids[p]))
            
        # Top n asks (lowest to highest)
        top_asks = []
        for p in self.asks.keys()[:n]:
            top_asks.append((p, self.asks[p]))
            
        return top_bids, top_asks

# Run up to 09:30 EDT
lob = DatabentoOfficialLOB()
ny_open_ns = pd.Timestamp("2026-09-10T13:30:00Z").value

print("Replaying 2026-09-10 MBO stream with Databento Official LOB implementation...")

for record in data:
    if not isinstance(record, db.MBOMsg):
        continue
    
    action = chr(record.action) if isinstance(record.action, int) else str(record.action)
    flags = record.flags
    is_snapshot = bool(flags & db.RecordFlags.F_SNAPSHOT)
    
    if is_snapshot:
        lob.snapshot_orders += 1
        if action == 'R':
            lob.clear()
        elif action == 'A':
            side = chr(record.side) if isinstance(record.side, int) else str(record.side)
            lob.add(record.order_id, record.price, record.size, side)
        if bool(flags & db.RecordFlags.F_LAST):
            lob.snapshot_complete = True
        continue
        
    if record.ts_event >= ny_open_ns:
        break
        
    lob.events_processed += 1
    
    # Official Databento LOB Action Dispatch:
    if action == 'A':
        side = chr(record.side) if isinstance(record.side, int) else str(record.side)
        lob.add(record.order_id, record.price, record.size, side)
    elif action == 'C':
        lob.cancel(record.order_id, record.size)
    elif action == 'M':
        lob.modify(record.order_id, record.price, record.size)
    elif action == 'T':
        lob.trades_count += 1
    elif action == 'F':
        lob.fills_count += 1
    elif action == 'R':
        lob.clear()

best_bid, best_ask, spread = lob.get_bbo()
top_bids, top_asks = lob.get_depth(5)

print("\n=== OFFICIAL DATABENTO LOB RESULTS AT 09:30:00 EDT ===")
print(f"Snapshot Received:         {'YES' if lob.snapshot_complete else 'NO'}")
print(f"Snapshot Order Records:    {lob.snapshot_orders:,}")
print(f"Events Processed (to 9:30):{lob.events_processed:,}")
print(f"Active Resting Orders:     {len(lob.orders):,}")
print(f"Orphan Cancels:            {lob.orphan_cancels} ({lob.orphan_cancels / max(1, lob.events_processed) * 100:.6f}%)")
print(f"Orphan Modifies:           {lob.orphan_modifies}")
print(f"Trades Count:              {lob.trades_count:,}")
print(f"Fills Count:               {lob.fills_count:,}")

print(f"\n--- Official LOB BBO at 09:30:00 EDT ---")
print(f"Best Bid: {best_bid[0]/1e9:.2f} (Size: {best_bid[1]})")
print(f"Best Ask: {best_ask[0]/1e9:.2f} (Size: {best_ask[1]})")
print(f"Spread:   {spread:.2f} points")

print("\nTop 5 Bids (Official LOB):")
for p, s in top_bids:
    print(f"  {p/1e9:.2f} : {s} contracts")

print("\nTop 5 Asks (Official LOB):")
for p, s in top_asks:
    print(f"  {p/1e9:.2f} : {s} contracts")
