"""Causal one-session replay. Accepts any records with MBO fields. No file IO."""

from __future__ import annotations

from common.order_book import LimitOrderBook
from research.mbo.clock import F_LAST, F_SNAPSHOT, STEP_NS, snapshot_bin_index
from research.mbo.version import REPLAY_ENGINE_VERSION

PRICE_SCALE = 1_000_000_000


def _action(record) -> str:
    action = record.action
    if isinstance(action, int):
        return chr(action)
    return str(action)


def _side(record) -> str:
    side = record.side
    if isinstance(side, int):
        return chr(side)
    return str(side)


def _book_view(book: LimitOrderBook) -> dict[str, float | int]:
    best_bid, best_ask, _spread = book.get_bbo()
    bid_raw, bid_sz = best_bid
    ask_raw, ask_sz = best_ask
    bids, asks = book.get_depth(5)
    q_b5 = int(sum(size for _px, size in bids))
    q_a5 = int(sum(size for _px, size in asks))
    q_b1 = int(bid_sz) if bid_raw else 0
    q_a1 = int(ask_sz) if ask_raw else 0
    bid_px = bid_raw / PRICE_SCALE if bid_raw else float("nan")
    ask_px = ask_raw / PRICE_SCALE if ask_raw else float("nan")
    if bid_raw and ask_raw:
        mid = (bid_px + ask_px) / 2.0
        spread = ask_px - bid_px
    else:
        mid = float("nan")
        spread = float("nan")
    obi_1 = (q_b1 - q_a1) / (q_b1 + q_a1) if (q_b1 + q_a1) else float("nan")
    obi_5 = (q_b5 - q_a5) / (q_b5 + q_a5) if (q_b5 + q_a5) else float("nan")
    return {
        "mid_px": mid,
        "bid_px": bid_px,
        "ask_px": ask_px,
        "spread": spread,
        "q_b1": q_b1,
        "q_a1": q_a1,
        "q_b5": q_b5,
        "q_a5": q_a5,
        "obi_1": obi_1,
        "obi_5": obi_5,
    }


class ReplaySession:
    """Replay one session. Call consume() on one chunk or many, then finish()."""

    def __init__(
        self,
        date_str: str,
        open_ns: int,
        close_ns: int,
        step_ns: int = STEP_NS,
        instrument: str = "NQ",
    ) -> None:
        self.date = date_str
        self.open_ns = open_ns
        self.close_ns = close_ns
        self.step_ns = step_ns
        self.instrument = instrument
        self.n_bins = ((close_ns - open_ns) // step_ns) + 1
        self.book = LimitOrderBook()
        self.gi = 0
        self.flow_max_ts = 0
        self.stopped = False
        self.events_seen = 0
        self._reset_flow()
        self.snapshots: list[dict] = []
        self.trades: list[dict] = []

    def _reset_flow(self) -> None:
        self.trade_b = 0
        self.trade_a = 0
        self.cnt_b = 0
        self.cnt_a = 0
        self.fill_b = 0
        self.fill_a = 0
        self.add_b = 0
        self.add_a = 0
        self.cancel_b = 0
        self.cancel_a = 0
        self.flow_max_ts = 0

    def consume(self, records) -> None:
        if self.stopped:
            raise RuntimeError("session already closed")
        for record in records:
            self._one(record)
            if self.stopped:
                break

    def finish(self) -> None:
        if not self.stopped:
            self._flush_until(self.close_ns + 1)
            self.stopped = True

    def _flush_until(self, ts: int) -> None:
        while self.gi < self.n_bins and (self.open_ns + self.gi * self.step_ns) < ts:
            self._emit(self.open_ns + self.gi * self.step_ns)
            self.gi += 1
            self._reset_flow()

    def _emit(self, ts_ns: int) -> None:
        row = _book_view(self.book)
        row.update(
            {
                "replay_version": REPLAY_ENGINE_VERSION,
                "date": self.date,
                "instrument": self.instrument,
                "ts_ns": ts_ns,
                "trade_b_1s": self.trade_b,
                "trade_a_1s": self.trade_a,
                "trade_cnt_b_1s": self.cnt_b,
                "trade_cnt_a_1s": self.cnt_a,
                "fill_b_1s": self.fill_b,
                "fill_a_1s": self.fill_a,
                "add_b_1s": self.add_b,
                "add_a_1s": self.add_a,
                "cancel_b_1s": self.cancel_b,
                "cancel_a_1s": self.cancel_a,
                "flow_max_ts_ns": self.flow_max_ts,
            }
        )
        if self.flow_max_ts > ts_ns:
            raise RuntimeError(f"flow at {self.flow_max_ts} landed on snapshot {ts_ns}")
        self.snapshots.append(row)

    def _one(self, record) -> None:
        flags = int(getattr(record, "flags", 0) or 0)
        if flags & F_SNAPSHOT:
            is_last = bool(flags & F_LAST)
            self.book.apply_record(record, is_snapshot=True, is_last_snapshot=is_last)
            return

        ts = int(record.ts_event)
        self.events_seen += 1
        if ts > self.close_ns:
            self._flush_until(self.close_ns + 1)
            self.stopped = True
            return

        self._flush_until(ts)
        self.book.apply_record(record, is_snapshot=False)
        idx = snapshot_bin_index(ts, self.open_ns, self.close_ns, self.step_ns, self.n_bins)
        if idx is None:
            return
        if idx != self.gi:
            raise RuntimeError(f"bin {idx} != open bin {self.gi} at ts {ts}")

        action = _action(record)
        side = _side(record)
        size = int(record.size)
        if ts > self.flow_max_ts:
            self.flow_max_ts = ts
        if action == "T":
            if side == "B":
                self.trade_b += size
                self.cnt_b += 1
            elif side == "A":
                self.trade_a += size
                self.cnt_a += 1
            self._record_trade(record, ts, side, size)
        elif action == "F":
            if side == "B":
                self.fill_b += size
            elif side == "A":
                self.fill_a += size
        elif action == "A":
            if side == "B":
                self.add_b += size
            elif side == "A":
                self.add_a += size
        elif action == "C":
            if side == "B":
                self.cancel_b += size
            elif side == "A":
                self.cancel_a += size

    def _record_trade(self, record, ts: int, side: str, size: int) -> None:
        view = _book_view(self.book)
        price_raw = int(getattr(record, "price", 0) or 0)
        price = price_raw / PRICE_SCALE if price_raw else float("nan")
        mid = view["mid_px"]
        self.trades.append(
            {
                "replay_version": REPLAY_ENGINE_VERSION,
                "date": self.date,
                "instrument": self.instrument,
                "ts_event": ts,
                "sequence": int(getattr(record, "sequence", 0) or 0),
                "order_id": int(getattr(record, "order_id", 0) or 0),
                "action": "T",
                "side": side,
                "price": price,
                "size": size,
                "mid_px": mid,
                "bid_px": view["bid_px"],
                "ask_px": view["ask_px"],
                "spread": view["spread"],
                "distance_from_mid": price - mid if mid == mid else float("nan"),
            }
        )
