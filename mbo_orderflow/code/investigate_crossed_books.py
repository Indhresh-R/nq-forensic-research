"""Explain the 25 crossed snapshots from the raw MBO file.

Does not change the replay engine, does not drop rows, and does not read volume-profile data.
One-tick event crosses are counted, not printed. The report is the wide inversion that
survives onto the one-second snapshot clock.
"""

from __future__ import annotations

import sys
from pathlib import Path

import databento as db
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from common.order_book import LimitOrderBook

RAW = REPO / "data" / "mbo_full_state_50"
STORE = REPO / "data" / "mbo_research" / "v2" / "snapshots"
OUT = Path(__file__).resolve().parents[1] / "reports"
PRICE_SCALE = 1_000_000_000
WIDE_RAW = 10 * PRICE_SCALE
STEP = 1_000_000_000

BURSTS = (
    ("2026-07-10", 1783693962000000000, 1783693976000000000),
    ("2026-07-13", 1783952206000000000, 1783952210000000000),
    ("2026-08-11", 1786455962000000000, 1786455966000000000),
)


def _flags() -> dict[str, int]:
    names = ("F_MAYBE_BAD_BOOK", "F_BAD_TS_RECV", "F_SNAPSHOT", "F_LAST")
    found = {}
    for cls in (getattr(db, "RecordFlags", None), getattr(getattr(db, "common", None), "RecordFlags", None)):
        if cls is None:
            continue
        for name in names:
            if hasattr(cls, name):
                found[name] = int(getattr(cls, name))
    defaults = {"F_MAYBE_BAD_BOOK": 4, "F_BAD_TS_RECV": 8, "F_SNAPSHOT": 32, "F_LAST": 128}
    for name, value in defaults.items():
        found.setdefault(name, value)
    return found


FLAGS = _flags()


def _px(raw: int) -> float:
    return raw / PRICE_SCALE


def _action(record) -> str:
    action = record.action
    return chr(action) if isinstance(action, int) else str(action)


def _side(record) -> str:
    side = record.side
    return chr(side) if isinstance(side, int) else str(side)


def _bbo(book: LimitOrderBook) -> tuple[int, int, int, int]:
    bid_px, bid_sz = book.bids.peekitem(-1) if book.bids else (0, 0)
    ask_px, ask_sz = book.asks.peekitem(0) if book.asks else (0, 0)
    return int(bid_px), int(bid_sz), int(ask_px), int(ask_sz)


def _levels(book: LimitOrderBook, side: str, n: int) -> list[tuple[int, int]]:
    tree = book.bids if side == "B" else book.asks
    if not tree:
        return []
    keys = list(reversed(tree.keys()[-n:])) if side == "B" else list(tree.keys()[:n])
    return [(int(px), int(tree[px])) for px in keys]


def _orders_at(book: LimitOrderBook, price: int, side: str) -> list[tuple[int, int]]:
    found = []
    for order_id, (px, size, order_side) in book.orders.items():
        if px == price and order_side == side:
            found.append((int(order_id), int(size)))
    return sorted(found)


def _ladder(book: LimitOrderBook, added: dict, bbo: tuple[int, int, int, int]) -> dict:
    ask_px = bbo[2]
    bids_above = []
    for px, size in _levels(book, "B", 12):
        if px <= ask_px:
            break
        orders = _orders_at(book, px, "B")
        bids_above.append((px, size, [(oid, sz, _birth_text(added, oid)) for oid, sz in orders[:8]]))
    ask_orders = _orders_at(book, ask_px, "A")
    return {
        "bids_above": bids_above,
        "ask": (ask_px, bbo[3], [(oid, sz, _birth_text(added, oid)) for oid, sz in ask_orders[:8]]),
        "next_asks": [_px(px) for px, _sz in _levels(book, "A", 4)],
        "next_bids": [_px(px) for px, _sz in _levels(book, "B", 4)],
    }


def _birth_text(added: dict, order_id: int) -> str:
    meta = added.get(order_id)
    if meta is None:
        return "birth not recorded"
    return (
        f"born {meta['origin']} ts={meta['ts']} seq={meta['seq']} "
        f"iid={meta['iid']} side={meta['side']} px={_px(meta['price'])} sz={meta['size']}"
    )


def _event_row(record, ts: int, seq: int, action: str, before: tuple, after: tuple) -> dict:
    return {
        "ts": ts,
        "seq": seq,
        "action": action,
        "side": _side(record),
        "price": int(getattr(record, "price", 0) or 0),
        "size": int(record.size),
        "order_id": int(getattr(record, "order_id", 0) or 0),
        "flags": int(getattr(record, "flags", 0) or 0),
        "iid": int(record.instrument_id),
        "before": before,
        "after": after,
    }


def _fmt_event(row: dict, added: dict) -> str:
    before = row["before"]
    after = row["after"]
    return (
        f"ts={row['ts']} seq={row['seq']} {row['action']} {row['side']} "
        f"px={_px(row['price'])} sz={row['size']} order={row['order_id']} "
        f"flags={row['flags']} iid={row['iid']} "
        f"book {_px(before[0])}/{_px(before[2])} -> {_px(after[0])}/{_px(after[2])} "
        f"({_birth_text(added, row['order_id'])})"
    )


def investigate(day: str, start_ns: int, end_ns: int) -> list[str]:
    book = LimitOrderBook()
    added: dict[int, dict] = {}
    window_lo = start_ns - 2 * STEP
    window_hi = end_ns + 2 * STEP
    snap_ns = list(range(start_ns - STEP, end_ns + 2 * STEP, STEP))
    snap_i = 0
    boundaries: list[tuple[int, tuple]] = []
    first_ladder = None
    last_ladder = None
    flag_counts = {"maybe_bad_book": 0, "bad_ts_recv": 0, "snapshot": 0, "clear": 0}
    action_counts = {name: 0 for name in ("A", "C", "M", "T", "F", "R")}
    instruments = set()
    ts_back = 0
    seq_back = 0
    prev_ts = -1
    prev_seq = -1
    wide_episodes = 0
    wide_before_window = 0
    max_wide_before = 0
    was_wide = False
    current = None
    saved = []
    path = RAW / f"mbo_{day}.dbn.zst"
    store = db.DBNStore.from_file(path)

    def _close_episode(row: dict) -> None:
        nonlocal wide_episodes, wide_before_window, max_wide_before, current
        current["closer"] = row
        duration = row["ts"] - current["start"]
        current["duration_ns"] = duration
        wide_episodes += 1
        if current["start"] < window_lo:
            wide_before_window += 1
            max_wide_before = max(max_wide_before, current["max_width"])
        if current["start"] <= window_hi and current["end"] >= window_lo:
            saved.append(current)
        current = None

    for record in store:
        if not isinstance(record, db.MBOMsg):
            continue
        flags = int(getattr(record, "flags", 0) or 0)
        ts = int(record.ts_event)
        seq = int(getattr(record, "sequence", 0) or 0)
        action = _action(record)
        while snap_i < len(snap_ns) and ts > snap_ns[snap_i]:
            bbo_now = _bbo(book)
            boundaries.append((snap_ns[snap_i], bbo_now))
            if bbo_now[0] and bbo_now[2] and bbo_now[0] > bbo_now[2]:
                ladder = _ladder(book, added, bbo_now)
                if first_ladder is None:
                    first_ladder = (snap_ns[snap_i], ladder)
                last_ladder = (snap_ns[snap_i], ladder)
            snap_i += 1
        if ts < prev_ts:
            ts_back += 1
        if window_lo <= ts <= window_hi and seq < prev_seq and ts == prev_ts:
            seq_back += 1
        prev_ts = ts
        prev_seq = seq
        if flags & FLAGS["F_SNAPSHOT"]:
            if action == "A":
                added[int(record.order_id)] = {
                    "ts": ts,
                    "seq": seq,
                    "iid": int(record.instrument_id),
                    "side": _side(record),
                    "price": int(record.price),
                    "size": int(record.size),
                    "origin": "snapshot",
                }
            book.apply_record(record, is_snapshot=True, is_last_snapshot=bool(flags & FLAGS["F_LAST"]))
            if window_lo <= ts <= window_hi:
                flag_counts["snapshot"] += 1
            continue
        if action == "A":
            added[int(record.order_id)] = {
                "ts": ts,
                "seq": seq,
                "iid": int(record.instrument_id),
                "side": _side(record),
                "price": int(record.price),
                "size": int(record.size),
                "origin": "incremental",
            }
        before = _bbo(book)
        book.apply_record(record, is_snapshot=False)
        after = _bbo(book)
        width = after[0] - after[2] if after[0] and after[2] else 0
        wide = width >= WIDE_RAW
        in_window = window_lo <= ts <= window_hi
        if in_window:
            instruments.add(int(record.instrument_id))
            action_counts[action] = action_counts.get(action, 0) + 1
            if flags & FLAGS["F_MAYBE_BAD_BOOK"]:
                flag_counts["maybe_bad_book"] += 1
            if flags & FLAGS["F_BAD_TS_RECV"]:
                flag_counts["bad_ts_recv"] += 1
            if action == "R":
                flag_counts["clear"] += 1
        row = None
        if wide != was_wide or (wide and width > (current["max_width"] if current else 0)):
            row = _event_row(record, ts, seq, action, before, after)
        if wide and not was_wide:
            current = {
                "start": ts,
                "end": ts,
                "max_width": width,
                "opener": row,
                "widest": row,
                "closer": None,
            }
        elif wide and current is not None:
            current["end"] = ts
            if width > current["max_width"]:
                current["max_width"] = width
                current["widest"] = row
        elif was_wide and not wide and current is not None:
            if row is None:
                row = _event_row(record, ts, seq, action, before, after)
            _close_episode(row)
        was_wide = wide
        if ts > window_hi and not wide and snap_i >= len(snap_ns):
            break
    if current is not None:
        current["duration_ns"] = window_hi - current["start"]
        current["closer"] = None
        if current["start"] <= window_hi and current["end"] >= window_lo:
            saved.append(current)
    while snap_i < len(snap_ns):
        boundaries.append((snap_ns[snap_i], _bbo(book)))
        snap_i += 1

    stored = pd.read_parquet(
        STORE / f"date={day}" / "snapshots.parquet",
        columns=["ts_ns", "bid_px", "ask_px", "q_b1", "q_a1"],
    )
    stored = stored[stored["ts_ns"].isin(snap_ns)].set_index("ts_ns")
    mismatches = 0
    lines = [
        f"## {day}",
        "",
        f"- Flag constants used: {FLAGS}",
        f"- Instrument ids in the ±2s window: {sorted(instruments)}",
        f"- Action counts in the ±2s window: {action_counts}",
        f"- Flags in the ±2s window: {flag_counts}",
        f"- Timestamp reversals from file start through the window: {ts_back}",
        f"- Same-timestamp sequence reversals inside the ±2s window: {seq_back}",
        f"- Orphan cancels by the end of the window: {book.orphan_cancels}",
        f"- Orphan modifies by the end of the window: {book.orphan_modifies}",
        f"- Wide episodes (bid at least 10 points through ask) before the window: {wide_before_window}",
        f"- Largest such pre-window width, points: {_px(max_wide_before)}",
        f"- Wide episodes that overlap the burst window: {len(saved)}",
        f"- Wide episodes closed before the window ended: {wide_episodes}",
        "",
    ]
    for episode in saved:
        lines.append(
            f"Wide episode start={episode['start']} end={episode['end']} "
            f"max_width_points={_px(episode['max_width'])} duration_ns={episode.get('duration_ns')}"
        )
        lines.append(f"- opener: {_fmt_event(episode['opener'], added)}")
        if episode["widest"] is not episode["opener"]:
            lines.append(f"- widest: {_fmt_event(episode['widest'], added)}")
        if episode["closer"] is not None:
            lines.append(f"- closer: {_fmt_event(episode['closer'], added)}")
        else:
            lines.append("- closer: still wide when the replay stopped")
        lines.append("")
    lines.append("Snapshot-clock book versus stored parquet. Neighbors one second outside the burst are included.")
    lines.append("")
    for ts_boundary, bbo in boundaries:
        bid, qb, ask, qa = bbo
        row = stored.loc[ts_boundary] if ts_boundary in stored.index else None
        if row is None:
            lines.append(f"- ts={ts_boundary} reconstructed {_px(bid)}/{_px(ask)} stored MISSING")
            mismatches += 1
            continue
        bid_gap = abs(_px(bid) - float(row["bid_px"]))
        ask_gap = abs(_px(ask) - float(row["ask_px"]))
        qty_match = int(qb) == int(row["q_b1"]) and int(qa) == int(row["q_a1"])
        match = bid_gap < 1e-9 and ask_gap < 1e-9 and qty_match
        if not match:
            mismatches += 1
        crossed = bid and ask and bid > ask
        lines.append(
            f"- ts={ts_boundary} reconstructed bid={_px(bid)} sz={qb} ask={_px(ask)} sz={qa} "
            f"stored bid={float(row['bid_px'])} sz={int(row['q_b1'])} ask={float(row['ask_px'])} sz={int(row['q_a1'])} "
            f"match={match} crossed={bool(crossed)}"
        )
    lines.append("")
    lines.append(f"Stored-versus-replay mismatches on these boundaries: {mismatches}")
    lines.append("")

    def _emit_ladder(title: str, captured) -> None:
        if captured is None:
            lines.append(title + ": none")
            return
        ts_boundary, ladder = captured
        lines.append(f"{title} ts={ts_boundary}:")
        lines.append("Bids above the ask, best first:")
        if not ladder["bids_above"]:
            lines.append("- none")
        for px, size, orders in ladder["bids_above"]:
            lines.append(f"- bid level px={_px(px)} sz={size} orders={orders}")
        ask_px, ask_sz, ask_orders = ladder["ask"]
        lines.append(f"- best ask px={_px(ask_px)} sz={ask_sz} orders={ask_orders}")
        lines.append(f"- next ask levels: {ladder['next_asks']}")
        lines.append(f"- next bid levels from the top: {ladder['next_bids']}")
        lines.append("")

    _emit_ladder("Orders at the first crossed snapshot boundary", first_ladder)
    _emit_ladder("Orders at the last crossed snapshot boundary", last_ladder)
    return lines


def main() -> None:
    text = [
        "# Crossed-book investigation",
        "",
        "Raw MBO applied with the existing `LimitOrderBook` rules. The replay engine was not modified.",
        "A wide episode is a bid at least 10 index points above the ask. One-tick crosses are not listed.",
        "",
    ]
    for day, start_ns, end_ns in BURSTS:
        print(f"[cross] {day}", flush=True)
        text.extend(investigate(day, start_ns, end_ns))
    path = OUT / "CROSSED_BOOKS.md"
    path.write_text("\n".join(text), encoding="utf-8")
    print(f"[cross] wrote {path}", flush=True)


if __name__ == "__main__":
    main()
