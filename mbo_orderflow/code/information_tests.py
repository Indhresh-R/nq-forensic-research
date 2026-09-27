"""Information diagnostics declared in mbo_orderflow/PREREGISTRATION.md.

Does not modify the replay engine, does not drop stored rows, and does not read volume_profile.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from research.mbo.sessions import IS_SESSIONS

STORE = REPO / "data" / "mbo_research" / "v2" / "snapshots"
OUT = Path(__file__).resolve().parents[1]
STEP_NS = 1_000_000_000
WINDOWS = (1, 5, 15, 30, 60)
HORIZONS = (1, 5, 15, 30, 60)
MIN_IC_N = 30
MIN_DAILY_N = 100
EARLY = IS_SESSIONS[:13]
LATE = IS_SESSIONS[13:]

COLUMNS = (
    "ts_ns",
    "bid_px",
    "ask_px",
    "q_b1",
    "q_a1",
    "q_b5",
    "q_a5",
    "trade_b_1s",
    "trade_a_1s",
    "trade_cnt_b_1s",
    "trade_cnt_a_1s",
    "add_b_1s",
    "add_a_1s",
    "cancel_b_1s",
    "cancel_a_1s",
)

SHAPE_FEATURES = (
    [("trade_imbalance", w) for w in WINDOWS]
    + [("obi_1", 0), ("obi_5", 0)]
    + [("depth_net_change", w) for w in (1, 5, 15)]
    + [("replenish_net", w) for w in (1, 5)]
    + [("obi_x_flow", 5)]
)


def _roll_sum(values: np.ndarray, window: int) -> np.ndarray:
    out = np.full(values.shape[0], np.nan, dtype=np.float64)
    if window > values.shape[0]:
        return out
    cumulative = np.cumsum(values)
    out[window - 1] = cumulative[window - 1]
    if window < values.shape[0]:
        out[window:] = cumulative[window:] - cumulative[:-window]
    return out


def _ratio(num: np.ndarray, den: np.ndarray) -> np.ndarray:
    out = np.full(num.shape[0], np.nan, dtype=np.float64)
    ok = np.isfinite(num) & np.isfinite(den) & (den != 0)
    out[ok] = num[ok] / den[ok]
    return out


def _level_change(level: np.ndarray, quote: np.ndarray, window: int) -> np.ndarray:
    out = np.full(level.shape[0], np.nan, dtype=np.float64)
    if window >= level.shape[0]:
        return out
    both = quote[window:] & quote[:-window]
    out[window:] = np.where(both, level[window:] - level[:-window], np.nan)
    return out


def _spearman(feature: np.ndarray, forward: np.ndarray) -> tuple[float, int]:
    mask = np.isfinite(feature) & np.isfinite(forward)
    n = int(mask.sum())
    if n < MIN_IC_N:
        return float("nan"), n
    x = feature[mask]
    y = forward[mask]
    if np.unique(x).size < 2 or np.unique(y).size < 2:
        return float("nan"), n
    ic = float(spearmanr(x, y).statistic)
    return ic, n


def _signed_stats(feature: np.ndarray, forward: np.ndarray) -> dict[str, float]:
    mask = np.isfinite(feature) & np.isfinite(forward)
    x = feature[mask]
    y = forward[mask]
    pos = x > 0
    neg = x < 0
    nonzero = (x != 0) & (y != 0)
    return {
        "n_pos": int(pos.sum()),
        "n_neg": int(neg.sum()),
        "median_pos": float(np.median(y[pos])) if pos.any() else float("nan"),
        "mean_pos": float(np.mean(y[pos])) if pos.any() else float("nan"),
        "median_neg": float(np.median(y[neg])) if neg.any() else float("nan"),
        "mean_neg": float(np.mean(y[neg])) if neg.any() else float("nan"),
        "n_sign": int(nonzero.sum()),
        "sign_pct": float(np.mean(np.sign(x[nonzero]) == np.sign(y[nonzero]))) if nonzero.any() else float("nan"),
    }


def _load_day(day: str) -> dict[str, np.ndarray]:
    frame = pd.read_parquet(STORE / f"date={day}" / "snapshots.parquet", columns=list(COLUMNS))
    if len(frame) != 9000:
        raise RuntimeError(f"{day} has {len(frame)} rows, expected 9000")
    ts = frame["ts_ns"].to_numpy(dtype=np.int64)
    if np.any(np.diff(ts) != STEP_NS):
        raise RuntimeError(f"{day} snapshot clock is not a 1-second grid")
    bid = frame["bid_px"].to_numpy(dtype=np.float64)
    ask = frame["ask_px"].to_numpy(dtype=np.float64)
    finite = np.isfinite(bid) & np.isfinite(ask)
    crossed = finite & (bid > ask)
    locked = finite & (bid == ask)
    quote = finite & (bid < ask)
    mid = np.where(quote, (bid + ask) / 2.0, np.nan)
    qb1 = frame["q_b1"].to_numpy(dtype=np.float64)
    qa1 = frame["q_a1"].to_numpy(dtype=np.float64)
    qb5 = frame["q_b5"].to_numpy(dtype=np.float64)
    qa5 = frame["q_a5"].to_numpy(dtype=np.float64)
    buy = frame["trade_b_1s"].to_numpy(dtype=np.float64)
    sell = frame["trade_a_1s"].to_numpy(dtype=np.float64)
    cnt_b = frame["trade_cnt_b_1s"].to_numpy(dtype=np.float64)
    cnt_a = frame["trade_cnt_a_1s"].to_numpy(dtype=np.float64)
    add_b = frame["add_b_1s"].to_numpy(dtype=np.float64)
    add_a = frame["add_a_1s"].to_numpy(dtype=np.float64)
    cancel_b = frame["cancel_b_1s"].to_numpy(dtype=np.float64)
    cancel_a = frame["cancel_a_1s"].to_numpy(dtype=np.float64)
    for name, values in (
        ("buy", buy),
        ("sell", sell),
        ("add_b", add_b),
        ("add_a", add_a),
        ("cancel_b", cancel_b),
        ("cancel_a", cancel_a),
    ):
        if not np.isfinite(values).all():
            raise RuntimeError(f"{day} {name} has a non-finite value")
    features: dict[str, np.ndarray] = {}
    for window in WINDOWS:
        buy_w = _roll_sum(buy, window)
        sell_w = _roll_sum(sell, window)
        cnt_b_w = _roll_sum(cnt_b, window)
        cnt_a_w = _roll_sum(cnt_a, window)
        add_b_w = _roll_sum(add_b, window)
        add_a_w = _roll_sum(add_a, window)
        cancel_b_w = _roll_sum(cancel_b, window)
        cancel_a_w = _roll_sum(cancel_a, window)
        features[f"buy_volume_{window}"] = buy_w
        features[f"sell_volume_{window}"] = sell_w
        features[f"trade_imbalance_{window}"] = _ratio(buy_w - sell_w, buy_w + sell_w)
        features[f"signed_volume_{window}"] = buy_w - sell_w
        features[f"count_imbalance_{window}"] = _ratio(cnt_b_w - cnt_a_w, cnt_b_w + cnt_a_w)
        features[f"add_signed_{window}"] = add_b_w - add_a_w
        features[f"cancel_signed_{window}"] = cancel_b_w - cancel_a_w
        features[f"replenish_net_{window}"] = (add_b_w - cancel_b_w) - (add_a_w - cancel_a_w)
        bid_change = _level_change(qb1, quote, window)
        ask_change = _level_change(qa1, quote, window)
        features[f"depth_bid_change_{window}"] = bid_change
        features[f"depth_ask_change_{window}"] = ask_change
        features[f"depth_net_change_{window}"] = bid_change - ask_change
    obi_1 = _ratio(qb1 - qa1, qb1 + qa1)
    obi_1 = np.where(quote, obi_1, np.nan)
    obi_5 = _ratio(qb5 - qa5, qb5 + qa5)
    obi_5 = np.where(quote, obi_5, np.nan)
    features["obi_1_0"] = obi_1
    features["obi_5_0"] = obi_5
    features["spread_0"] = np.where(quote, ask - bid, np.nan)
    features["tob_depth_0"] = np.where(quote, qb1 + qa1, np.nan)
    features["obi_x_flow_5"] = obi_1 * features["trade_imbalance_5"]
    return {
        "ts": ts,
        "crossed": crossed,
        "locked": locked,
        "quote": quote,
        "mid": mid,
        "features": features,
    }


def _feature_table() -> list[tuple[str, str, int, bool]]:
    rows: list[tuple[str, str, int, bool]] = []
    for window in WINDOWS:
        rows.append(("trade", "buy_volume", window, False))
        rows.append(("trade", "sell_volume", window, False))
        rows.append(("trade", "trade_imbalance", window, True))
        rows.append(("trade", "signed_volume", window, True))
        rows.append(("trade", "count_imbalance", window, True))
        rows.append(("book_change", "depth_bid_change", window, True))
        rows.append(("book_change", "depth_ask_change", window, True))
        rows.append(("book_change", "depth_net_change", window, True))
        rows.append(("order_flow", "add_signed", window, True))
        rows.append(("order_flow", "cancel_signed", window, True))
        rows.append(("order_flow", "replenish_net", window, True))
    rows.append(("book", "obi_1", 0, True))
    rows.append(("book", "obi_5", 0, True))
    rows.append(("book", "spread", 0, False))
    rows.append(("book", "tob_depth", 0, False))
    rows.append(("combined", "obi_x_flow", 5, True))
    return rows


def _key(name: str, window: int) -> str:
    return f"{name}_{window}"


def _evaluate(feature: np.ndarray, forward: np.ndarray, dates: np.ndarray, day_ids: np.ndarray) -> dict[str, float]:
    ic, n = _spearman(feature, forward)
    early = np.isin(dates, EARLY)
    late = np.isin(dates, LATE)
    ic_early, n_early = _spearman(feature[early], forward[early])
    ic_late, n_late = _spearman(feature[late], forward[late])
    daily = []
    for day_id in np.unique(day_ids):
        mask = day_ids == day_id
        daily_ic, daily_n = _spearman(feature[mask], forward[mask])
        if daily_n >= MIN_DAILY_N and np.isfinite(daily_ic):
            daily.append(daily_ic)
    out = {
        "n": n,
        "ic": ic,
        "n_early": n_early,
        "ic_early": ic_early,
        "n_late": n_late,
        "ic_late": ic_late,
        "n_daily": len(daily),
        "ic_daily_median": float(np.median(daily)) if daily else float("nan"),
    }
    out.update(_signed_stats(feature, forward))
    return out


def _exclusion(days: list[dict[str, np.ndarray]]) -> pd.DataFrame:
    rows = []
    n_rows = sum(len(day["quote"]) for day in days)
    n_crossed = sum(int(day["crossed"].sum()) for day in days)
    n_locked = sum(int(day["locked"].sum()) for day in days)
    n_quote = sum(int(day["quote"].sum()) for day in days)
    for horizon in HORIZONS:
        slot = 0
        anchor_crossed = 0
        anchor_other = 0
        endpoint_crossed = 0
        endpoint_other = 0
        valid = 0
        for day in days:
            n = len(day["quote"])
            slot += n - horizon
            anchor = day["quote"][:-horizon]
            crossed_anchor = day["crossed"][:-horizon]
            endpoint_quote = day["quote"][horizon:]
            end_crossed = day["crossed"][horizon:]
            anchor_crossed += int(crossed_anchor.sum())
            anchor_other += int((~anchor & ~crossed_anchor).sum())
            endpoint_bad = anchor & ~endpoint_quote
            endpoint_crossed += int((endpoint_bad & end_crossed).sum())
            endpoint_other += int((endpoint_bad & ~end_crossed).sum())
            valid += int((anchor & endpoint_quote).sum())
        rows.append(
            {
                "horizon_s": horizon,
                "snapshot_rows": n_rows,
                "crossed_rows": n_crossed,
                "locked_rows": n_locked,
                "usable_quote_rows": n_quote,
                "future_slots": slot,
                "excluded_anchor_crossed": anchor_crossed,
                "excluded_anchor_not_usable": anchor_other,
                "excluded_endpoint_crossed": endpoint_crossed,
                "excluded_endpoint_not_usable": endpoint_other,
                "valid_return_anchors": valid,
            }
        )
    return pd.DataFrame(rows)


def _shape_line(summary: pd.DataFrame) -> str:
    lines = []
    for name, window in SHAPE_FEATURES:
        part = summary[(summary["feature"] == name) & (summary["window_s"] == window)].sort_values("horizon_s")
        ics = part["ic"].to_numpy(dtype=float)
        if not np.isfinite(ics).all() or np.any(ics == 0):
            lines.append(f"- {name} window {window}: not horizon-stable")
            continue
        sign = np.sign(ics)
        horizon_stable = np.all(sign == sign[0])
        row5 = part[part["horizon_s"] == 5].iloc[0]
        split_stable = (
            horizon_stable
            and np.isfinite(row5["ic_early"])
            and np.isfinite(row5["ic_late"])
            and np.sign(row5["ic_early"]) == sign[0]
            and np.sign(row5["ic_late"]) == sign[0]
        )
        lines.append(
            f"- {name} window {window}: horizon-stable={bool(horizon_stable)} "
            f"split-stable={bool(split_stable)} full-sample IC sign={int(sign[0])}"
        )
    return "\n".join(lines)


def _fmt(value: float, digits: int = 4) -> str:
    if not np.isfinite(value):
        return ""
    return f"{value:.{digits}f}"


def _report(summary: pd.DataFrame, exclusion: pd.DataFrame) -> str:
    base = exclusion.iloc[0]
    lines = [
        "# MBO information diagnostic",
        "",
        "Preregistered in `PREREGISTRATION.md` and run once. No feature was dropped after seeing these numbers.",
        "The replay engine was not modified. Previous-session POC was not joined. Crossed rows remain in the store.",
        "",
        "This is a 26-session diagnostic. It is not evidence of a durable edge.",
        "",
        "## Exclusions",
        "",
        f"- Snapshot rows: {int(base['snapshot_rows'])}",
        f"- Crossed rows kept in the store and removed as anchors: {int(base['crossed_rows'])}",
        f"- Locked rows, also not usable quotes: {int(base['locked_rows'])}",
        f"- Usable quotes (bid < ask): {int(base['usable_quote_rows'])}",
        "",
    ]
    for _, row in exclusion.iterrows():
        lines.append(
            f"- Horizon {int(row['horizon_s'])}s: future slots {int(row['future_slots'])}, "
            f"anchor crossed {int(row['excluded_anchor_crossed'])}, "
            f"anchor otherwise unusable {int(row['excluded_anchor_not_usable'])}, "
            f"endpoint crossed {int(row['excluded_endpoint_crossed'])}, "
            f"endpoint otherwise unusable {int(row['excluded_endpoint_not_usable'])}, "
            f"valid return anchors {int(row['valid_return_anchors'])}."
        )
    lines.extend(
        [
            "",
            "Feature N is lower than the valid-anchor count when that feature is missing. Imbalance is missing when its denominator is 0. Rolling features are missing for the first w-1 seconds. Depth changes are missing unless both endpoints are usable quotes.",
            "",
            "## Shape check",
            "",
            "Horizon-stable means the five full-sample Spearman ICs share a sign. Split-stable means the early half and the late half at 5 seconds share that sign. Neither label selects a feature.",
            "",
            _shape_line(summary),
            "",
            "## Primary table",
            "",
            "Median and mean are the forward mid return, in index points, when the feature is strictly positive. Sign % uses both nonzero sides. IC is the pooled Spearman correlation. Early is 2026-07-08 through 2026-07-24. Late is 2026-07-27 through 2026-08-12.",
            "",
            "| Feature | Window | Horizon | N | Median fwd | Mean fwd | Median fwd x<0 | Sign % | IC | IC early | IC late |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    primary = summary[summary.apply(lambda row: (row["feature"], int(row["window_s"])) in SHAPE_FEATURES, axis=1)]
    primary = primary.sort_values(["family", "feature", "window_s", "horizon_s"])
    for _, row in primary.iterrows():
        lines.append(
            "| {feature} | {window} | {horizon} | {n} | {med} | {mean} | {med_neg} | {sign} | {ic} | {early} | {late} |".format(
                feature=row["feature"],
                window=int(row["window_s"]),
                horizon=int(row["horizon_s"]),
                n=int(row["n"]),
                med=_fmt(row["median_pos"], 3),
                mean=_fmt(row["mean_pos"], 3),
                med_neg=_fmt(row["median_neg"], 3),
                sign=_fmt(row["sign_pct"], 3),
                ic=_fmt(row["ic"]),
                early=_fmt(row["ic_early"]),
                late=_fmt(row["ic_late"]),
            )
        )
    lines.extend(
        [
            "",
            "The full grid, including buy volume, sell volume, spread, depth, adds, and cancels, is in `results/information_summary.csv`.",
            "Non-negative features have a rank correlation only. Their sign columns are blank.",
            "",
            "Modification counts are not in the frozen store and were not tested.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    days = []
    for day in IS_SESSIONS:
        print(f"[info] {day}", flush=True)
        loaded = _load_day(day)
        loaded["date"] = np.full(loaded["quote"].shape[0], day, dtype=object)
        loaded["day_id"] = np.full(loaded["quote"].shape[0], len(days), dtype=np.int16)
        days.append(loaded)
    exclusion = _exclusion(days)
    dates = np.concatenate([day["date"] for day in days])
    day_ids = np.concatenate([day["day_id"] for day in days])
    mids = [day["mid"] for day in days]
    quotes = [day["quote"] for day in days]
    forwards = {}
    for horizon in HORIZONS:
        parts = []
        for mid, quote in zip(mids, quotes):
            forward = np.full(mid.shape[0], np.nan, dtype=np.float64)
            ok = quote[:-horizon] & quote[horizon:]
            forward[:-horizon] = np.where(ok, mid[horizon:] - mid[:-horizon], np.nan)
            parts.append(forward)
        forwards[horizon] = np.concatenate(parts)
    stacked = {
        _key(name, window): np.concatenate([day["features"][_key(name, window)] for day in days])
        for _family, name, window, _signed in _feature_table()
    }
    rows = []
    for family, name, window, signed in _feature_table():
        feature = stacked[_key(name, window)]
        for horizon in HORIZONS:
            stats = _evaluate(feature, forwards[horizon], dates, day_ids)
            if not signed:
                for field in ("n_pos", "n_neg", "median_pos", "mean_pos", "median_neg", "mean_neg", "n_sign", "sign_pct"):
                    stats[field] = float("nan")
            stats.update({"family": family, "feature": name, "window_s": window, "horizon_s": horizon, "signed": signed})
            rows.append(stats)
            print(f"[info] {name} w={window} h={horizon} n={stats['n']} ic={stats['ic']}", flush=True)
    summary = pd.DataFrame(rows)
    results = OUT / "results"
    reports = OUT / "reports"
    results.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)
    summary.to_csv(results / "information_summary.csv", index=False)
    exclusion.to_csv(results / "information_exclusion.csv", index=False)
    (reports / "INFORMATION.md").write_text(_report(summary, exclusion), encoding="utf-8")
    (results / "information_meta.json").write_text(
        json.dumps({"early": list(EARLY), "late": list(LATE), "horizons": list(HORIZONS), "windows": list(WINDOWS)}, indent=2),
        encoding="utf-8",
    )
    print("[info] wrote reports/INFORMATION.md", flush=True)


if __name__ == "__main__":
    main()
