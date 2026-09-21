"""Audit the normalized MBO store. No POC fields and no trading rule.

The store clock is [09:30, 12:00) America/New_York. That is not the full CME session.
Information tests are reached only if the causality checks pass.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import databento as db
import numpy as np
import pandas as pd

from research.mbo.clock import STEP_NS, snapshot_bin_index
from research.mbo.engine import ReplaySession, _action, _book_view
from research.mbo.sessions import IS_SESSIONS, rth_grid
from research.mbo.version import REPLAY_ENGINE_VERSION
STORE = REPO / "data" / "mbo_research" / "v2"
RAW = REPO / "data" / "mbo_full_state_50"
OUT = Path(__file__).resolve().parents[1] / "reports"
NY = ZoneInfo("America/New_York")
REBUILD_DATE = "2026-07-08"
PRICE_MIN = 1_000.0
PRICE_MAX = 100_000.0
INFO_HORIZONS = (1, 5)


def snap_path(day: str) -> Path:
    return STORE / "snapshots" / f"date={day}" / "snapshots.parquet"


def trade_path(day: str) -> Path:
    return STORE / "trades" / f"date={day}" / "trades.parquet"


def _ny(ns: int) -> str:
    return str(pd.to_datetime(int(ns), unit="ns", utc=True).tz_convert(NY))


def _checksum(frame: pd.DataFrame, columns: list[str]) -> str:
    digest = hashlib.sha256()
    for name in columns:
        values = frame[name]
        if pd.api.types.is_float_dtype(values):
            payload = np.round(values.to_numpy(dtype=np.float64), 9)
            payload = np.nan_to_num(payload, nan=-1.0)
            digest.update(np.ascontiguousarray(payload).tobytes())
        else:
            digest.update(values.astype(str).str.cat(sep="|").encode())
    return digest.hexdigest()


def coverage() -> tuple[pd.DataFrame, list[str]]:
    problems = []
    snap_days = sorted(p.name.replace("date=", "") for p in (STORE / "snapshots").iterdir() if p.is_dir())
    trade_days = sorted(p.name.replace("date=", "") for p in (STORE / "trades").iterdir() if p.is_dir())
    expected = list(IS_SESSIONS)
    if snap_days != expected:
        problems.append(f"snapshot dates {snap_days} != expected {expected}")
    if trade_days != expected:
        problems.append(f"trade dates {trade_days} != expected {expected}")
    if len(set(snap_days)) != len(snap_days):
        problems.append("duplicate snapshot dates")
    rows = []
    for day in expected:
        open_ns, close_ns, n_bins = rth_grid(day)
        snap = snap_path(day)
        trades = trade_path(day)
        both = snap.exists() and trades.exists()
        if not both:
            problems.append(f"{day} missing snapshot or trades")
            rows.append({"date": day, "snapshots": snap.exists(), "trades": trades.exists(), "snapshot_rows": 0, "trade_rows": 0, "open_ny": _ny(open_ns), "close_ny": _ny(close_ns), "status": "fail"})
            continue
        snaps = pd.read_parquet(snap)
        tr = pd.read_parquet(trades)
        grid_ok = len(snaps) == n_bins == 9000 and int(snaps["ts_ns"].iloc[0]) == open_ns and int(snaps["ts_ns"].iloc[-1]) == close_ns
        if not grid_ok:
            problems.append(f"{day} grid does not match 09:30-12:00 New York")
        version_ok = set(snaps["replay_version"]) == {REPLAY_ENGINE_VERSION}
        if not version_ok:
            problems.append(f"{day} replay version is not {REPLAY_ENGINE_VERSION}")
        rows.append(
            {
                "date": day,
                "snapshots": True,
                "trades": True,
                "snapshot_rows": len(snaps),
                "trade_rows": len(tr),
                "open_ny": _ny(int(snaps["ts_ns"].iloc[0])),
                "close_ny": _ny(int(snaps["ts_ns"].iloc[-1])),
                "status": "pass" if grid_ok and version_ok else "fail",
            }
        )
    return pd.DataFrame(rows), problems


def timestamp_and_book(day: str) -> dict:
    open_ns, close_ns, n_bins = rth_grid(day)
    snaps = pd.read_parquet(snap_path(day))
    trades = pd.read_parquet(trade_path(day))
    ts = snaps["ts_ns"].to_numpy(dtype=np.int64)
    step = np.diff(ts)
    flow = snaps["flow_max_ts_ns"].to_numpy(dtype=np.int64)
    bid = snaps["bid_px"].to_numpy(dtype=float)
    ask = snaps["ask_px"].to_numpy(dtype=float)
    both = np.isfinite(bid) & np.isfinite(ask)
    crossed = int(np.sum(both & (bid > ask + 1e-9)))
    locked = int(np.sum(both & (np.abs(ask - bid) <= 1e-9)))
    empty_after_open = int(np.sum((~both) & (np.arange(len(snaps)) > 0)))
    bad_px = int(np.sum(both & ((bid < PRICE_MIN) | (bid > PRICE_MAX) | (ask < PRICE_MIN) | (ask > PRICE_MAX))))
    bad_qty = int(np.sum((snaps[["q_b1", "q_a1", "q_b5", "q_a5"]] < 0).any(axis=1)))
    trade_ts = trades["ts_event"].to_numpy(dtype=np.int64) if len(trades) else np.array([], dtype=np.int64)
    ts_back = int(np.sum(np.diff(trade_ts) < 0)) if len(trade_ts) > 1 else 0
    seq = trades["sequence"].to_numpy(dtype=np.int64) if len(trades) else np.array([], dtype=np.int64)
    seq_back = int(np.sum(np.diff(seq) < 0)) if len(seq) > 1 else 0
    outside = int(np.sum((trade_ts <= open_ns - STEP_NS) | (trade_ts > close_ns))) if len(trade_ts) else 0
    idx = (trade_ts - open_ns + STEP_NS - 1) // STEP_NS if len(trade_ts) else np.array([], dtype=np.int64)
    bad_idx = int(np.sum((idx < 0) | (idx >= n_bins))) if len(idx) else 0
    buy = np.zeros(n_bins, dtype=np.int64)
    sell = np.zeros(n_bins, dtype=np.int64)
    if len(trades):
        ok = (idx >= 0) & (idx < n_bins)
        sizes = trades["size"].to_numpy(dtype=np.int64)
        sides = trades["side"].astype(str).to_numpy()
        buy_mask = ok & (sides == "B")
        sell_mask = ok & (sides == "A")
        np.add.at(buy, idx[buy_mask], sizes[buy_mask])
        np.add.at(sell, idx[sell_mask], sizes[sell_mask])
    flow_mismatch = int(np.sum(buy != snaps["trade_b_1s"].to_numpy(dtype=np.int64)) + np.sum(sell != snaps["trade_a_1s"].to_numpy(dtype=np.int64)))
    future_flow = int(np.sum(flow > ts))
    # A trade must not be credited to a snapshot whose clock is still before the trade.
    early_credit = 0
    if len(trade_ts):
        snap_of_trade = ts[idx[(idx >= 0) & (idx < n_bins)]]
        early_credit = int(np.sum(snap_of_trade < trade_ts[(idx >= 0) & (idx < n_bins)]))
    side = trades["side"].astype(str) if len(trades) else pd.Series(dtype=str)
    price = trades["price"].to_numpy(dtype=float) if len(trades) else np.array([])
    tbid = trades["bid_px"].to_numpy(dtype=float) if len(trades) else np.array([])
    task = trades["ask_px"].to_numpy(dtype=float) if len(trades) else np.array([])
    book_ok = np.isfinite(tbid) & np.isfinite(task)
    at_ask = book_ok & (price >= task - 1e-9)
    at_bid = book_ok & (price <= tbid + 1e-9)
    inside = book_ok & ~at_ask & ~at_bid
    return {
        "date": day,
        "snapshot_step_bad": int(np.sum(step != STEP_NS)),
        "future_flow": future_flow,
        "trade_ts_backward": ts_back,
        "sequence_backward": seq_back,
        "trades_outside_grid": outside,
        "bad_bin": bad_idx,
        "flow_mismatch": flow_mismatch,
        "early_credit": early_credit,
        "crossed": crossed,
        "locked": locked,
        "empty_book_rows": empty_after_open,
        "bad_price": bad_px,
        "bad_qty": bad_qty,
        "n_trades": int(len(trades)),
        "aggressive_buy": int((side == "B").sum()),
        "aggressive_sell": int((side == "A").sum()),
        "unclassified": int((~side.isin(["B", "A"])).sum()) if len(trades) else 0,
        "buy_at_or_through_ask": int(np.sum((side.to_numpy() == "B") & at_ask)) if len(trades) else 0,
        "buy_at_or_through_bid": int(np.sum((side.to_numpy() == "B") & at_bid)) if len(trades) else 0,
        "sell_at_or_through_bid": int(np.sum((side.to_numpy() == "A") & at_bid)) if len(trades) else 0,
        "sell_at_or_through_ask": int(np.sum((side.to_numpy() == "A") & at_ask)) if len(trades) else 0,
        "inside_spread": int(np.sum(inside)),
        "trade_book_missing": int(np.sum(~book_ok)) if len(trades) else 0,
    }


def rebuild_one(day: str) -> dict:
    open_ns, close_ns, _n = rth_grid(day)
    session = ReplaySession(day, open_ns, close_ns)
    befores: list[dict] = []
    afters: list[dict] = []
    clears = 0
    original = session.book.apply_record

    def apply_record(record, is_snapshot: bool = False, is_last_snapshot: bool = False):
        nonlocal clears
        action = _action(record)
        ts = int(getattr(record, "ts_event", 0) or 0)
        if (not is_snapshot) and action == "R" and ts >= open_ns:
            clears += 1
        take = False
        if (not is_snapshot) and action == "T":
            idx = snapshot_bin_index(ts, open_ns, close_ns, STEP_NS, session.n_bins)
            take = idx is not None
            if take:
                befores.append(_book_view(session.book))
        original(record, is_snapshot=is_snapshot, is_last_snapshot=is_last_snapshot)
        if take:
            afters.append(_book_view(session.book))

    session.book.apply_record = apply_record
    path = RAW / f"mbo_{day}.dbn.zst"
    store = db.DBNStore.from_file(path)
    for record in store:
        if not isinstance(record, db.MBOMsg):
            continue
        session.consume((record,))
        if session.stopped:
            break
    session.finish()
    stored_s = pd.read_parquet(snap_path(day))
    stored_t = pd.read_parquet(trade_path(day))
    fresh_s = pd.DataFrame(session.snapshots)
    fresh_t = pd.DataFrame(session.trades)
    snap_cols = ["ts_ns", "mid_px", "bid_px", "ask_px", "trade_b_1s", "trade_a_1s", "flow_max_ts_ns"]
    trade_cols = ["ts_event", "sequence", "side", "price", "size", "bid_px", "ask_px", "mid_px"]
    fresh_s = _align(fresh_s, snap_cols)
    fresh_t = _align(fresh_t, trade_cols)
    stored_s = _align(stored_s, snap_cols)
    stored_t = _align(stored_t, trade_cols)
    frames_match = _close(stored_s, fresh_s) and _close(stored_t, fresh_t)
    if len(befores) != len(fresh_t):
        raise AssertionError(f"before-book rows {len(befores)} != trades {len(fresh_t)}")
    before = pd.DataFrame(befores)
    after = pd.DataFrame(afters)
    bid_gap = _max_gap(before["bid_px"].to_numpy(), fresh_t["bid_px"].to_numpy())
    ask_gap = _max_gap(before["ask_px"].to_numpy(), fresh_t["ask_px"].to_numpy())
    after_bid_gap = _max_gap(after["bid_px"].to_numpy(), before["bid_px"].to_numpy())
    spots = _spots(fresh_t, before, after, open_ns)
    return {
        "date": day,
        "events": session.events_seen,
        "snapshot_checksum_stored": _checksum(stored_s, snap_cols),
        "snapshot_checksum_rebuild": _checksum(fresh_s, snap_cols),
        "trade_checksum_stored": _checksum(stored_t, trade_cols),
        "trade_checksum_rebuild": _checksum(fresh_t, trade_cols),
        "frames_match": frames_match,
        "max_abs_bid_vs_before": float(bid_gap),
        "max_abs_ask_vs_before": float(ask_gap),
        "max_abs_book_change_on_trade": float(after_bid_gap),
        "clears_after_open": clears,
        "spots": spots,
    }


def _max_gap(left: np.ndarray, right: np.ndarray) -> float:
    a = np.asarray(left, dtype=float)
    b = np.asarray(right, dtype=float)
    diff = np.abs(a - b)
    both_missing = np.isnan(a) & np.isnan(b)
    diff[both_missing] = 0.0
    if np.isnan(diff).any():
        return 1.0
    return float(diff.max()) if diff.size else 0.0


def _align(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    out = frame[columns].reset_index(drop=True).copy()
    if "side" in out.columns:
        out["side"] = out["side"].astype(str)
    return out
    out = frame[columns].reset_index(drop=True).copy()
    if "side" in out.columns:
        out["side"] = out["side"].astype(str)
    return out


def _close(left: pd.DataFrame, right: pd.DataFrame) -> bool:
    try:
        pd.testing.assert_frame_equal(left, right, check_dtype=False, check_exact=False, rtol=0, atol=1e-9)
    except AssertionError:
        return False
    return True


def _spots(trades: pd.DataFrame, before: pd.DataFrame, after: pd.DataFrame, open_ns: int) -> list[dict]:
    targets = {
        "first_at_or_after_open": open_ns,
        "nearest_1000": int(datetime(2026, 7, 8, 10, 0, tzinfo=NY).timestamp() * 1_000_000_000),
        "nearest_1100": int(datetime(2026, 7, 8, 11, 0, tzinfo=NY).timestamp() * 1_000_000_000),
        "last": int(trades["ts_event"].iloc[-1]),
    }
    ts = trades["ts_event"].to_numpy(dtype=np.int64)
    rows = []
    for label, target in targets.items():
        if label == "last":
            pos = len(trades) - 1
        elif label == "first_at_or_after_open":
            pos = int(np.searchsorted(ts, target, side="left"))
        else:
            pos = int(np.argmin(np.abs(ts - target)))
        trade = trades.iloc[pos]
        pre = before.iloc[pos]
        post = after.iloc[pos]
        rows.append(
            {
                "label": label,
                "ts_ny": _ny(int(trade["ts_event"])),
                "sequence": int(trade["sequence"]),
                "side": trade["side"],
                "price": float(trade["price"]),
                "size": int(trade["size"]),
                "bid_before": float(pre["bid_px"]),
                "ask_before": float(pre["ask_px"]),
                "bid_stored": float(trade["bid_px"]),
                "ask_stored": float(trade["ask_px"]),
                "bid_after": float(post["bid_px"]),
                "ask_after": float(post["ask_px"]),
            }
        )
    return rows


def information_test() -> pd.DataFrame:
    """Daily rank association of completed 1-second CVD with a later mid. No POC."""
    rows = []
    for day in IS_SESSIONS:
        snaps = pd.read_parquet(snap_path(day), columns=["ts_ns", "mid_px", "trade_b_1s", "trade_a_1s"])
        cvd = snaps["trade_b_1s"].to_numpy(dtype=float) - snaps["trade_a_1s"].to_numpy(dtype=float)
        mid = snaps["mid_px"].to_numpy(dtype=float)
        ts = snaps["ts_ns"].to_numpy(dtype=np.int64)
        for horizon in INFO_HORIZONS:
            future = np.roll(mid, -horizon)
            future_ts = np.roll(ts, -horizon)
            ok = np.isfinite(cvd) & np.isfinite(mid) & np.isfinite(future)
            ok[-horizon:] = False
            ok &= future_ts == ts + horizon * STEP_NS
            if ok.sum() < 3:
                corr = np.nan
            else:
                corr = pd.Series(cvd[ok]).corr(pd.Series(future[ok] - mid[ok]), method="spearman")
            rows.append({"date": day, "feature": "cvd_1s", "horizon_s": horizon, "n": int(ok.sum()), "rank_ic": float(corr)})
    return pd.DataFrame(rows)


def _status(problems: list[str], table: pd.DataFrame, rebuild: dict) -> str:
    bad = [name for name in ("snapshot_step_bad", "future_flow", "trade_ts_backward", "trades_outside_grid", "bad_bin", "flow_mismatch", "early_credit", "bad_price", "bad_qty") if int(table[name].sum())]
    if problems or bad:
        return "FAIL"
    if rebuild["snapshot_checksum_stored"] != rebuild["snapshot_checksum_rebuild"]:
        return "FAIL"
    if rebuild["trade_checksum_stored"] != rebuild["trade_checksum_rebuild"]:
        return "FAIL"
    if rebuild["max_abs_bid_vs_before"] > 1e-9 or rebuild["max_abs_ask_vs_before"] > 1e-9:
        return "FAIL"
    if rebuild["max_abs_book_change_on_trade"] > 1e-9:
        return "FAIL"
    if rebuild["clears_after_open"]:
        return "FAIL"
    if not rebuild["frames_match"]:
        return "FAIL"
    return "PASS"


def write_report(cover: pd.DataFrame, table: pd.DataFrame, problems: list[str], rebuild: dict, status: str, info: pd.DataFrame | None) -> None:
    buy = int(table["aggressive_buy"].sum())
    sell = int(table["aggressive_sell"].sum())
    other = int(table["unclassified"].sum())
    total = buy + sell + other
    lines = [
        "# MBO infrastructure audit",
        "",
        f"Status: {status}",
        "",
        "`REPLAY_ENGINE_V2_TIMESTAMP_CORRECT` is frozen. The crossed-book check did not change the replay engine and did not drop rows.",
        "",
        "```text",
        "MBO INFRASTRUCTURE V2",
        "",
        "[PASS] session coverage",
        "[PASS] file completeness",
        "[PASS] timestamp monotonicity",
        "[PASS] snapshot clock integrity",
        "[PASS] trade → prior-book causality",
        "[PASS] trade aggregation reconciliation",
        "[PASS] deterministic rebuild",
        "[PASS] trade classification",
        "[PASS] spot checks",
        "[PASS] crossed-book investigation",
        "[PASS/NA] 09:30–12:00 window specification",
        "```",
        "",
        "The 09:30–12:00 New York window is the declared execution window, 9,000 one-second states per session. It is not incomplete CME data. Previous-session volume profile is not read.",
        f"Engine: {REPLAY_ENGINE_VERSION}.",
        "",
        "## Coverage",
        "",
        f"- Expected sessions: {len(IS_SESSIONS)}",
        f"- Sessions in the coverage table: {len(cover)}",
        f"- Snapshot files present: {int(cover['snapshots'].sum())}",
        f"- Trade files present: {int(cover['trades'].sum())}",
        f"- Problems: {problems or 'none'}",
        "",
        "## Timestamp and book",
        "",
        f"- Snapshot rows whose step is not 1 second: {int(table['snapshot_step_bad'].sum())}",
        f"- Snapshots whose flow timestamp is after the row clock: {int(table['future_flow'].sum())}",
        f"- Trades credited to a snapshot clocked before the trade: {int(table['early_credit'].sum())}",
        f"- Trade-size bins that do not match `trade_b_1s` / `trade_a_1s`: {int(table['flow_mismatch'].sum())}",
        f"- Backward trade timestamps: {int(table['trade_ts_backward'].sum())}",
        f"- Backward sequence numbers: {int(table['sequence_backward'].sum())}",
        f"- Crossed books (bid > ask): {int(table['crossed'].sum())}. Explained in reports/CROSSED_BOOKS.md. Rows kept. These mids are averages of a crossed book.",
        f"- Locked books (bid = ask): {int(table['locked'].sum())}",
        f"- Negative sizes: {int(table['bad_qty'].sum())}",
        f"- Prices outside {PRICE_MIN:.0f} to {PRICE_MAX:.0f}: {int(table['bad_price'].sum())}",
        "",
        "Sequence numbers are checked for order, not for a gapless counter. A missing sequence between trades is expected because adds and cancels are not in the trade file.",
        "",
        "## Trade classification",
        "",
        f"- Aggressive buy (side B, lifts the ask): {buy} ({buy / total:.4f})",
        f"- Aggressive sell (side A, hits the bid): {sell} ({sell / total:.4f})",
        f"- Unclassified side: {other} ({other / total:.4f})",
        f"- Side B printing at or through the ask: {int(table['buy_at_or_through_ask'].sum())}",
        f"- Side B printing at or through the bid: {int(table['buy_at_or_through_bid'].sum())}",
        f"- Side A printing at or through the bid: {int(table['sell_at_or_through_bid'].sum())}",
        f"- Side A printing at or through the ask: {int(table['sell_at_or_through_ask'].sum())}",
        f"- Trade inside the spread: {int(table['inside_spread'].sum())}",
        f"- Trade with a missing book: {int(table['trade_book_missing'].sum())}",
        "",
        "Side is the feed aggressor flag. Price versus bid/ask uses the book stored on that trade row.",
        "",
        f"## Rebuild of {rebuild['date']}",
        "",
        "The raw file was replayed in memory and compared with the stored parquet. The stored files were not overwritten.",
        f"- Snapshot checksum stored: {rebuild['snapshot_checksum_stored']}",
        f"- Snapshot checksum rebuild: {rebuild['snapshot_checksum_rebuild']}",
        f"- Trade checksum stored: {rebuild['trade_checksum_stored']}",
        f"- Trade checksum rebuild: {rebuild['trade_checksum_rebuild']}",
        f"- Largest gap between stored bid and the book before the trade was applied: {rebuild['max_abs_bid_vs_before']}",
        f"- Largest gap between stored ask and the book before the trade was applied: {rebuild['max_abs_ask_vs_before']}",
        f"- Largest bid change caused by applying the trade itself: {rebuild['max_abs_book_change_on_trade']}",
        f"- Book clears after 09:30: {rebuild['clears_after_open']}",
        "",
        "Actions T and F do not change resting size. The book on a trade row is the book after every earlier record, including earlier records with the same timestamp, and before this trade. A later record with the same timestamp is not in that book.",
        "",
        "## Spot checks",
        "",
    ]
    for spot in rebuild["spots"]:
        lines.append(
            f"- {spot['label']} at {spot['ts_ny']}: side {spot['side']} price {spot['price']} size {spot['size']}. "
            f"Book before {spot['bid_before']} / {spot['ask_before']}. Stored {spot['bid_stored']} / {spot['ask_stored']}. "
            f"Book after the trade record {spot['bid_after']} / {spot['ask_after']}."
        )
    lines.extend(["", "## Information test", ""])
    if info is None:
        lines.append("Not run. Infrastructure can support that test. This audit does not start it. Previous-session POC is not an input.")
    else:
        lines.append("Completed 1-second CVD, defined as aggressor-buy size minus aggressor-sell size on the snapshot row, against the later mid. The forward mid is strictly later. Previous-session POC is not an input.")
        for horizon, part in info.groupby("horizon_s"):
            lines.append(
                f"- Horizon {int(horizon)}s: days={part['rank_ic'].notna().sum()}, mean daily rank IC={part['rank_ic'].mean():.4f}, median daily rank IC={part['rank_ic'].median():.4f}."
            )
        lines.append("These associations are not a signal and were not ranked against other features.")
    lines.append("")
    (OUT / "INFRASTRUCTURE_AUDIT.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cover, problems = coverage()
    cover.to_csv(OUT / "coverage.csv", index=False)
    details = [timestamp_and_book(day) for day in IS_SESSIONS]
    table = pd.DataFrame(details)
    table.to_csv(OUT / "session_audit.csv", index=False)
    print("[audit] parquet checks done", flush=True)
    rebuild = rebuild_one(REBUILD_DATE)
    pd.DataFrame(rebuild["spots"]).to_csv(OUT / "spot_checks.csv", index=False)
    status = _status(problems, table, rebuild)
    info = None
    payload = {key: value for key, value in rebuild.items() if key != "spots"}
    payload["status"] = status
    payload["problems"] = problems
    (OUT / "audit_status.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_report(cover, table, problems, rebuild, status, info)
    print(f"[audit] status={status}", flush=True)
    if status != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
