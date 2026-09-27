"""
Order Book Reconstruction Engine
Based on Databento's official MBO specification and event dispatch semantics.

Architecture:
  - Book State Mutations: Driven exclusively by actions 'A' (Add), 'C' (Cancel), 'M' (Modify), 'R' (Clear).
  - Execution Notifications: 'T' (Trade) and 'F' (Fill) are handled separately for trade-flow analysis
    and do NOT mutate the resting book (CME Globex explicitly issues corresponding 'C' events to mutate resting orders).
"""

from sortedcontainers import SortedDict


class LimitOrderBook:
    def __init__(self):
        # order_id -> (price, size, side)
        self.orders = {}
        # price -> total_size at price level
        self.bids = SortedDict()
        self.asks = SortedDict()
        
        # Performance & Diagnostic counters
        self.snapshot_orders = 0
        self.snapshot_complete = False
        self.events_processed = 0
        self.orphan_cancels = 0
        self.orphan_modifies = 0
        self.trades_count = 0
        self.fills_count = 0

    def clear(self):
        """Reset internal book state (called upon receiving action == 'R')."""
        self.orders.clear()
        self.bids.clear()
        self.asks.clear()

    def add(self, order_id: int, price: int, size: int, side: str):
        """Insert a new resting order into the book."""
        self.orders[order_id] = (price, size, side)
        book = self.bids if side == 'B' else self.asks
        book[price] = book.get(price, 0) + size

    def cancel(self, order_id: int, cancel_size: int):
        """Cancel or reduce a resting order in the book."""
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

    def modify(self, order_id: int, new_price: int, new_size: int):
        """Modify the price and/or quantity of an existing order."""
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

    def handle_trade(self, record):
        """Record aggressive trade event (action == 'T')."""
        self.trades_count += 1

    def handle_fill(self, record):
        """Record passive order fill event (action == 'F')."""
        self.fills_count += 1

    def apply_record(self, record, is_snapshot: bool = False, is_last_snapshot: bool = False):
        """Apply an MBO record using official Databento dispatch rules."""
        action = chr(record.action) if isinstance(record.action, int) else str(record.action)
        
        if is_snapshot:
            self.snapshot_orders += 1
            if action == 'R':
                self.clear()
            elif action == 'A':
                side = chr(record.side) if isinstance(record.side, int) else str(record.side)
                self.add(record.order_id, record.price, record.size, side)
            if is_last_snapshot:
                self.snapshot_complete = True
            return
            
        self.events_processed += 1
        
        if action == 'A':
            side = chr(record.side) if isinstance(record.side, int) else str(record.side)
            self.add(record.order_id, record.price, record.size, side)
        elif action == 'C':
            self.cancel(record.order_id, record.size)
        elif action == 'M':
            self.modify(record.order_id, record.price, record.size)
        elif action == 'T':
            self.handle_trade(record)
        elif action == 'F':
            self.handle_fill(record)
        elif action == 'R':
            self.clear()

    def get_bbo(self):
        """Return (best_bid, best_ask, spread). Prices in raw integers (fixed-point)."""
        best_bid = self.bids.peekitem(-1) if len(self.bids) > 0 else (0, 0)
        best_ask = self.asks.peekitem(0) if len(self.asks) > 0 else (0, 0)
        spread = (best_ask[0] - best_bid[0]) / 1e9 if best_bid[0] and best_ask[0] else 0.0
        return best_bid, best_ask, spread

    def get_depth(self, levels: int = 5):
        """Return top N price levels for bids and asks."""
        top_bids = [(p, self.bids[p]) for p in reversed(self.bids.keys()[-levels:])]
        top_asks = [(p, self.asks[p]) for p in self.asks.keys()[:levels]]
        return top_bids, top_asks
