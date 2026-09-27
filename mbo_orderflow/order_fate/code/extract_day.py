"""Read-only spell extract for the frozen order-fate preregistration.

Does not modify the replay engine or the one-second store.
Does not compute a forward-return association.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import databento as db
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from mbo_orderflow.order_fate.code.definitions import (
    HORIZONS,
    P_COLUMNS,
    R_COLUMNS,
    anchor_index,
    assert_study_p_schema,
    classify_removal,
)
from research.mbo.clock import STEP_NS
from research.mbo.engine import PRICE_SCALE, ReplaySession, _action, _side
from research.mbo.sessions import rth_grid
from research.mbo.version import REPLAY_ENGINE_VERSION

DATA_DIR = REPO / "data" / "mbo_full_state_50"
STORE = REPO / "data" / "mbo_research" / "v2" / "snapshots"
OUT = Path(__file__).resolve().parents[1] / "results"


def _raw_price(value: float) -> int:
    if not np.isfinite(value):
        return 0
    return int(round(float(value) * PRICE_SCALE))


def _load_controls(date_str: str) -> dict[str, np.ndarray]:
    path = STORE / f"date={date_str}" / "snapshots.parquet"
    frame = pd.read_parquet(
        path,
        columns=[
            "ts_ns",
            "bid_px",
            "ask_px",
            "q_b1",
            "q_a1",
            "trade_b_1s",
            "trade_a_1s",
            "add_b_1s",
            "add_a_1s",
            "cancel_b_1s",
            "cancel_a_1s",
            "flow_max_ts_ns",
            "replay_version",
        ],
    )
    if len(frame) != 9000:
        raise RuntimeError(f"{date_str} has {len(frame)} snapshots, expected 9000")
    if set(frame["replay_version"].unique()) != {REPLAY_ENGINE_VERSION}:
        raise RuntimeError(f"{date_str} snapshot version is not {REPLAY_ENGINE_VERSION}")
    ts = frame["ts_ns"].to_numpy(dtype=np.int64)
    if np.any(np.diff(ts) != STEP_NS):
        raise RuntimeError(f"{date_str} snapshot clock is not a 1-second grid")
    flow = frame["flow_max_ts_ns"].to_numpy(dtype=np.int64)
    if np.any(flow > ts):
        raise RuntimeError(f"{date_str} control bin contains an event after the anchor")
    bid = frame["bid_px"].to_numpy(dtype=np.float64)
    ask = frame["ask_px"].to_numpy(dtype=np.float64)
    finite = np.isfinite(bid) & np.isfinite(ask)
    quote = finite & (bid < ask)
    mid = np.where(quote, (bid + ask) / 2.0, np.nan)
    qb1 = frame["q_b1"].to_numpy(dtype=np.float64)
    qa1 = frame["q_a1"].to_numpy(dtype=np.float64)
    den = qb1 + qa1
    obi = np.full(len(frame), np.nan, dtype=np.float64)
    ok_obi = quote & (den != 0)
    obi[ok_obi] = (qb1[ok_obi] - qa1[ok_obi]) / den[ok_obi]
    depth = np.full(len(frame), np.nan, dtype=np.float64)
    depth_ok = quote.copy()
    depth_ok[0] = False
    depth_ok[1:] &= quote[:-1]
    depth_idx = np.flatnonzero(depth_ok)
    depth[depth_idx] = (qb1[depth_idx] - qb1[depth_idx - 1]) - (qa1[depth_idx] - qa1[depth_idx - 1])
    buy = frame["trade_b_1s"].to_numpy(dtype=np.float64)
    sell = frame["trade_a_1s"].to_numpy(dtype=np.float64)
    timb = np.full(len(frame), np.nan, dtype=np.float64)
    tden = buy + sell
    ok_t = tden != 0
    timb[ok_t] = (buy[ok_t] - sell[ok_t]) / tden[ok_t]
    add_b = frame["add_b_1s"].to_numpy(dtype=np.float64)
    add_a = frame["add_a_1s"].to_numpy(dtype=np.float64)
    cancel_b = frame["cancel_b_1s"].to_numpy(dtype=np.float64)
    cancel_a = frame["cancel_a_1s"].to_numpy(dtype=np.float64)
    replenish = (add_b - cancel_b) - (add_a - cancel_a)
    return {
        "ts": ts,
        "bid_raw": np.array([_raw_price(v) for v in bid], dtype=np.int64),
        "ask_raw": np.array([_raw_price(v) for v in ask], dtype=np.int64),
        "qb1": qb1.astype(np.int64),
        "qa1": qa1.astype(np.int64),
        "quote": quote,
        "mid": mid,
        "obi": obi,
        "depth": depth,
        "timb": timb,
        "replenish": replenish,
        "buy": buy.astype(np.int64),
        "sell": sell.astype(np.int64),
    }


class _Writer:
    def __init__(self, path: Path, columns: tuple[str, ...]) -> None:
        self.path = path
        self.columns = columns
        self._chunks: dict[str, list] = {name: [] for name in columns}
        self.rows = 0
        self._writer: pq.ParquetWriter | None = None

    def add(self, values: dict) -> None:
        for name in self.columns:
            self._chunks[name].append(values[name])
        if len(self._chunks["date"]) >= 200_000:
            self._flush()

    def _flush(self) -> None:
        n = len(self._chunks["date"])
        if n == 0:
            return
        arrays = []
        for name in self.columns:
            values = self._chunks[name]
            if name == "date":
                arrays.append(pa.array(values, type=pa.string()))
            elif name in {"side_sign", "fate"}:
                arrays.append(pa.array(values, type=pa.int8()))
            elif name in {"age_ms", "lifetime_ms", "trade_size_at_price"}:
                arrays.append(pa.array(values, type=pa.float64()))
            else:
                arrays.append(pa.array(np.asarray(values, dtype=np.float64), type=pa.float64()))
            self._chunks[name] = []
        table = pa.Table.from_arrays(arrays, names=list(self.columns))
        if self._writer is None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._writer = pq.ParquetWriter(self.path, table.schema, compression="zstd")
        self._writer.write_table(table)
        self.rows += n

    def close(self) -> None:
        self._flush()
        if self._writer is not None:
            self._writer.close()
        elif self.rows == 0:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            empty = {name: [] for name in self.columns}
            pd.DataFrame(empty).to_parquet(self.path, index=False)


class SpellTracker:
    """Inside-quote spells. Study P never receives a completed lifetime or fate."""

    def __init__(self, date_str: str, open_ns: int, n_bins: int, controls: dict[str, np.ndarray]) -> None:
        self.date = date_str
        self.open_ns = open_ns
        self.n_bins = n_bins
        self.controls = controls
        self.book = None
        self.level: dict[tuple[str, int], dict[int, int]] = {}
        self.add_ns: dict[int, int] = {}
        self.eligible: set[int] = set()
        self.active: dict[int, dict] = {}
        self.at_price: dict[int, set[int]] = {}
        self._old: tuple | None = None
        self._next_id = 1
        self.ready = False
        self.labels = {
            "cancel": 0,
            "fill": 0,
            "partial_then_cancel": 0,
            "modify_away": 0,
            "left_inside": 0,
            "censored": 0,
        }
        self.p_skipped_unusable = 0
        self.r_no_anchor = 0
        self.emit_i = 0
        self.mismatches = 0
        assert_study_p_schema(P_COLUMNS)
        self.p_writer = _Writer(OUT / "p" / f"date={date_str}" / "rows.parquet", P_COLUMNS)
        self.r_writer = _Writer(OUT / "r" / f"date={date_str}" / "rows.parquet", R_COLUMNS)

    def before(self, record, is_snapshot: bool) -> None:
        if is_snapshot or self.book is None:
            self._old = None
            return
        ts = int(record.ts_event)
        if not self.ready and ts > self.open_ns:
            self._index_existing()
            self.ready = True
        if not self.ready:
            self._old = None
            return
        oid = int(getattr(record, "order_id", 0) or 0)
        self._old = self.book.orders.get(oid)

    def after(self, record, is_snapshot: bool) -> None:
        if is_snapshot or not self.ready:
            return
        action = _action(record)
        oid = int(getattr(record, "order_id", 0) or 0)
        ts = int(record.ts_event)
        if ts > self.open_ns + (self.n_bins - 1) * STEP_NS:
            return
        size = int(record.size)
        if action == "A" and oid in self.book.orders:
            price, order_size, side = self.book.orders[oid]
            self.level.setdefault((side, price), {})[oid] = order_size
            if ts > self.open_ns:
                self.eligible.add(oid)
                self.add_ns[oid] = ts
        elif action == "C":
            self._on_cancel(oid, size, ts)
        elif action == "M":
            self._on_modify(oid, ts)
        elif action == "F":
            spell = self.active.get(oid)
            if spell is not None:
                spell["fill_qty"] += size
        elif action == "T":
            self._on_trade(int(getattr(record, "price", 0) or 0), size)
        elif action == "R":
            self._censor_all(ts)
            self.level.clear()
        if action in {"A", "C", "M", "R"}:
            self._sync_inside(ts)

    def _index_existing(self) -> None:
        for oid, (price, size, side) in self.book.orders.items():
            self.level.setdefault((side, int(price)), {})[int(oid)] = int(size)
            self.add_ns[int(oid)] = 0

    def on_snapshot(self, session: ReplaySession) -> None:
        row = session.snapshots[-1]
        i = self.emit_i
        self.emit_i += 1
        controls = self.controls
        if int(row["ts_ns"]) != int(controls["ts"][i]):
            self.mismatches += 1
            raise RuntimeError(f"{self.date} snapshot timestamp diverged at row {i}")
        if int(row["q_b1"]) != int(controls["qb1"][i]) or int(row["q_a1"]) != int(controls["qa1"][i]):
            self.mismatches += 1
            raise RuntimeError(f"{self.date} top-of-book size diverged at {row['ts_ns']}")
        if _raw_price(row["bid_px"]) != int(controls["bid_raw"][i]) or _raw_price(row["ask_px"]) != int(
            controls["ask_raw"][i]
        ):
            self.mismatches += 1
            raise RuntimeError(f"{self.date} top-of-book price diverged at {row['ts_ns']}")
        if not bool(controls["quote"][i]):
            self.p_skipped_unusable += len(self.active)
            return
        ts_ns = int(row["ts_ns"])
        outcomes = self._outcomes(i)
        base = self._controls(i)
        for spell in self.active.values():
            self.p_writer.add(
                {
                    "date": self.date,
                    "side_sign": 1 if spell["side"] == "B" else -1,
                    "age_ms": (ts_ns - spell["start_ns"]) / 1_000_000.0,
                    "trade_size_at_price": float(spell["trade_at_price"]),
                    "obi": base["obi"],
                    "depth_change": base["depth"],
                    "trade_imbalance": base["timb"],
                    "replenishment": base["replenish"],
                    "y1": outcomes[1],
                    "y5": outcomes[5],
                    "y15": outcomes[15],
                    "y30": outcomes[30],
                }
            )

    def close_open_spells(self, ts: int) -> None:
        self._censor_all(ts)

    def finish_files(self) -> None:
        self.p_writer.close()
        self.r_writer.close()

    def _on_trade(self, price: int, size: int) -> None:
        oids = self.at_price.get(price)
        if not oids:
            return
        for oid in oids:
            self.active[oid]["trade_at_price"] += size

    def _on_cancel(self, oid: int, cancel_size: int, ts: int) -> None:
        old = self._old
        spell = self.active.get(oid)
        removed = oid not in self.book.orders
        if old is not None:
            old_price, _old_size, side = old
            level = self.level.get((side, old_price))
            if removed:
                if level and oid in level:
                    del level[oid]
                    if not level:
                        del self.level[(side, old_price)]
            elif level and oid in level:
                level[oid] = self.book.orders[oid][1]
        if spell is None:
            return
        pending = spell["fill_qty"] - spell["fill_matched"]
        explained = min(cancel_size, pending) if pending > 0 else 0
        spell["fill_matched"] += explained
        unexplained = cancel_size - explained
        if removed:
            self._end(oid, classify_removal(spell["fill_qty"], unexplained), ts)

    def _on_modify(self, oid: int, ts: int) -> None:
        old = self._old
        current = self.book.orders.get(oid)
        if old is not None:
            old_price, _old_size, side = old
            level = self.level.get((side, old_price))
            if level and oid in level:
                del level[oid]
                if not level:
                    del self.level[(side, old_price)]
        if current is not None:
            price, size, side = current
            self.level.setdefault((side, price), {})[oid] = size
        spell = self.active.get(oid)
        if spell is None or current is None:
            if spell is not None and current is None:
                self._end(oid, "censored", ts)
            return
        if current[0] != spell["price"]:
            self._end(oid, "modify_away", ts)

    def _sync_inside(self, ts: int) -> None:
        best_bid, best_ask, _spread = self.book.get_bbo()
        bbo = {"B": best_bid[0], "A": best_ask[0]}
        for oid, spell in list(self.active.items()):
            if spell["price"] != bbo[spell["side"]]:
                self._end(oid, "left_inside", ts)
        for side in ("B", "A"):
            price = bbo[side]
            if not price:
                continue
            level = self.level.get((side, price))
            if not level:
                continue
            for oid, size in level.items():
                if oid in self.eligible and oid not in self.active:
                    self._start(oid, side, price, size, ts)

    def _start(self, oid: int, side: str, price: int, size: int, ts: int) -> None:
        self.active[oid] = {
            "spell_id": self._next_id,
            "side": side,
            "price": price,
            "start_ns": ts,
            "fill_qty": 0,
            "fill_matched": 0,
            "trade_at_price": 0,
            "add_ns": self.add_ns.get(oid, ts),
        }
        self.at_price.setdefault(price, set()).add(oid)
        self._next_id += 1

    def _end(self, oid: int, label: str, ts: int) -> None:
        spell = self.active.pop(oid, None)
        if spell is None:
            return
        mates = self.at_price.get(spell["price"])
        if mates is not None:
            mates.discard(oid)
            if not mates:
                del self.at_price[spell["price"]]
        self.labels[label] = self.labels.get(label, 0) + 1
        if label not in {"cancel", "fill"}:
            return
        if ts < spell["start_ns"]:
            raise RuntimeError(f"{self.date} spell ended before it started")
        idx = anchor_index(ts, self.open_ns, self.n_bins)
        if idx is None:
            self.r_no_anchor += 1
            return
        anchor_ns = int(self.controls["ts"][idx])
        if anchor_ns <= ts:
            raise RuntimeError(f"{self.date} Study R anchor includes the terminal event")
        outcomes = self._outcomes(idx)
        base = self._controls(idx)
        self.r_writer.add(
            {
                "date": self.date,
                "side_sign": 1 if spell["side"] == "B" else -1,
                "lifetime_ms": (ts - spell["start_ns"]) / 1_000_000.0,
                "fate": 1 if label == "fill" else 0,
                "obi": base["obi"],
                "depth_change": base["depth"],
                "trade_imbalance": base["timb"],
                "replenishment": base["replenish"],
                "y1": outcomes[1],
                "y5": outcomes[5],
                "y15": outcomes[15],
                "y30": outcomes[30],
            }
        )

    def _censor_all(self, ts: int) -> None:
        for oid in list(self.active):
            self._end(oid, "censored", ts)

    def _controls(self, idx: int) -> dict[str, float]:
        return {
            "obi": float(self.controls["obi"][idx]),
            "depth": float(self.controls["depth"][idx]),
            "timb": float(self.controls["timb"][idx]),
            "replenish": float(self.controls["replenish"][idx]),
        }

    def _outcomes(self, idx: int) -> dict[int, float]:
        mid = self.controls["mid"]
        anchor = mid[idx]
        out = {}
        for horizon in HORIZONS:
            j = idx + horizon
            if j >= self.n_bins or not np.isfinite(anchor) or not np.isfinite(mid[j]):
                out[horizon] = float("nan")
            else:
                out[horizon] = float(mid[j] - anchor)
        return out


def extract_day(date_str: str, force: bool = False) -> dict:
    p_path = OUT / "p" / f"date={date_str}" / "rows.parquet"
    r_path = OUT / "r" / f"date={date_str}" / "rows.parquet"
    audit_path = OUT / "audit" / f"{date_str}.json"
    if p_path.exists() and r_path.exists() and audit_path.exists() and not force:
        return json.loads(audit_path.read_text(encoding="utf-8"))

    controls = _load_controls(date_str)
    open_ns, close_ns, n_bins = rth_grid(date_str)
    if int(controls["ts"][0]) != open_ns or int(controls["ts"][-1]) != close_ns:
        raise RuntimeError(f"{date_str} snapshot grid does not match the frozen clock")
    if n_bins != 9000:
        raise RuntimeError(f"{date_str} grid has {n_bins} bins, expected 9000")

    session = ReplaySession(date_str, open_ns, close_ns)
    session._record_trade = lambda *_args, **_kwargs: None
    tracker = SpellTracker(date_str, open_ns, n_bins, controls)
    tracker.book = session.book
    original_apply = session.book.apply_record
    original_emit = session._emit

    def apply_record(record, is_snapshot: bool = False, is_last_snapshot: bool = False):
        tracker.before(record, is_snapshot)
        original_apply(record, is_snapshot=is_snapshot, is_last_snapshot=is_last_snapshot)
        tracker.after(record, is_snapshot)

    def emit(ts_ns: int) -> None:
        original_emit(ts_ns)
        tracker.on_snapshot(session)

    session.book.apply_record = apply_record
    session._emit = emit

    src = DATA_DIR / f"mbo_{date_str}.dbn.zst"
    store = db.DBNStore.from_file(src)
    seen = 0
    for record in store:
        if not isinstance(record, db.MBOMsg):
            continue
        session.consume((record,))
        seen += 1
        if seen % 5_000_000 == 0:
            print(f"[{date_str}] events={seen:,} active={len(tracker.active):,}", flush=True)
        if session.stopped:
            break
    if not session.stopped:
        session.finish()
    tracker.close_open_spells(close_ns + 1)
    if tracker.emit_i != 9000:
        raise RuntimeError(f"{date_str} emitted {tracker.emit_i} snapshots, expected 9000")
    if tracker.mismatches:
        raise RuntimeError(f"{date_str} book diverged from the frozen store")
    tracker.finish_files()
    assert_study_p_schema(pq.read_schema(p_path).names)

    audit = {
        "date": date_str,
        "replay_version": REPLAY_ENGINE_VERSION,
        "events_consumed": seen,
        "spell_labels": tracker.labels,
        "study_r_rows": tracker.r_writer.rows,
        "study_p_rows": tracker.p_writer.rows,
        "study_p_skipped_unusable_anchor": tracker.p_skipped_unusable,
        "study_r_no_anchor": tracker.r_no_anchor,
        "book_mismatches": tracker.mismatches,
    }
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(
        f"[{date_str}] R={audit['study_r_rows']:,} P={audit['study_p_rows']:,} "
        f"labels={tracker.labels}",
        flush=True,
    )
    return audit
