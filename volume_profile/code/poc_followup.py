"""Second study on the frozen CME volume-profile dataset.

Does not rebuild profiles, change the 70% value area, or search thresholds.
The horizon list and point targets were specified before this run.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_research_dataset import iter_session_trades
from build_session_profiles import VP, epoch_ns, load_config, session_bounds

NY = "America/New_York"


def _eligible(frame: pd.DataFrame) -> pd.DataFrame:
    mask = (
        ~frame["is_roll_transition"].astype(bool)
        & ~frame["prev_is_roll_transition"].astype(bool)
        & frame["is_complete"].astype(bool)
        & frame["prev_is_complete"].astype(bool)
    )
    return frame.loc[mask].copy()


def _cuts(cfg: dict) -> dict[str, int]:
    out = {}
    for key, value in cfg["followup_time_buckets"].items():
        hour, minute = str(value).split(":")
        out[key] = int(hour) * 60 + int(minute)
    return out


def _buckets(minutes: np.ndarray, cuts: dict[str, int]) -> np.ndarray:
    out = np.full(minutes.shape, "maintenance", dtype=object)
    out[(minutes >= 18 * 60) | (minutes < cuts["cash_open"])] = "overnight"
    out[(minutes >= cuts["cash_open"]) & (minutes < cuts["cash_rest"])] = "cash_open"
    out[(minutes >= cuts["cash_rest"]) & (minutes < cuts["cash_close"])] = "cash_rest"
    out[(minutes >= cuts["cash_close"]) & (minutes < 17 * 60)] = "cash_close"
    return out


def _bucket_one(ts_ns: int, cuts: dict[str, int]) -> str:
    ny = pd.to_datetime(ts_ns, unit="ns", utc=True).tz_convert(NY)
    return str(_buckets(np.array([ny.hour * 60 + ny.minute]), cuts)[0])


def _tercile(value: float, q1: float, q2: float) -> str:
    if value <= q1:
        return "low"
    if value <= q2:
        return "mid"
    return "high"


def _open_vs_poc(open_px: float, poc: float, tol_px: float) -> str:
    if open_px > poc + tol_px:
        return "above_poc"
    if open_px < poc - tol_px:
        return "below_poc"
    return "at_poc"


def _open_vs_value(open_px: float, val: float, vah: float) -> str:
    if val <= open_px <= vah:
        return "inside_value"
    return "outside_value"


def _price_at(ts: np.ndarray, ticks: np.ndarray, target: int, end_ns: int) -> float:
    if target >= end_ns:
        return np.nan
    pos = int(np.searchsorted(ts, target, side="left"))
    if pos >= len(ts) or int(ts[pos]) >= end_ns:
        return np.nan
    return float(ticks[pos])


def _path(ts: np.ndarray, ticks: np.ndarray, start_i: int, event_ns: int, window_ns: int, end_ns: int) -> tuple[np.ndarray, np.ndarray]:
    limit = min(event_ns + window_ns, end_ns)
    stop = int(np.searchsorted(ts, limit, side="left"))
    return ts[start_i:stop], ticks[start_i:stop]


def analyze_session(trades: pd.DataFrame, row: pd.Series, cfg: dict, q1: float, q2: float, cuts: dict[str, int]) -> tuple[list[dict], dict]:
    tick = float(cfg["tick_size"])
    tol = int(cfg["interaction_tolerance_ticks"])
    horizons = [int(v) for v in cfg["followup_horizons_minutes"]]
    targets = [int(v) for v in cfg["followup_excursion_points"]]
    passage_pts = int(cfg["followup_passage_points"])
    window_min = int(cfg["followup_passage_window_minutes"])
    ordered = trades.sort_values(["ts_event", "sequence"], kind="mergesort")
    if ordered.empty:
        return [], {}
    ticks = ordered["price_ticks"].to_numpy(dtype=np.int64)
    ts = epoch_ns(ordered["ts_event"])
    session = str(row["session_date"])[:10]
    start, end = session_bounds(pd.Timestamp(session).date())
    start_ns = int(start.value)
    end_ns = int(end.value)
    level = int(round(float(row["prev_poc"]) / tick))
    tercile = _tercile(float(row["prev_profile_range"]), q1, q2)
    open_poc = _open_vs_poc(float(row["open_price"]), float(row["prev_poc"]), tol * tick)
    open_value = _open_vs_value(float(row["open_price"]), float(row["prev_val"]), float(row["prev_vah"]))
    inside = np.abs(ticks - level) <= tol
    prev_out = np.empty(len(inside), dtype=bool)
    prev_out[0] = True
    prev_out[1:] = ~inside[:-1]
    starts = np.flatnonzero(inside & prev_out)
    touches = []
    for number, idx in enumerate(starts, start=1):
        event_ns = int(ts[idx])
        if event_ns < start_ns or event_ns >= end_ns:
            continue
        if idx == 0:
            approach = "ambiguous"
        elif int(ticks[idx - 1]) < level:
            approach = "from_below"
        elif int(ticks[idx - 1]) > level:
            approach = "from_above"
        else:
            approach = "ambiguous"
        record = {
            "session_date": session,
            "touch_number": number,
            "touch_group": "first" if number == 1 else "subsequent",
            "approach": approach,
            "event_ns": event_ns,
            "time_bucket": _bucket_one(event_ns, cuts),
            "range_tercile": tercile,
            "open_vs_poc": open_poc,
            "open_vs_value": open_value,
            "touch_ticks": int(ticks[idx]),
            "level_ticks": level,
        }
        window_ns = window_min * 60 * 1_000_000_000
        path_ts, path_px = _path(ts, ticks, int(idx), event_ns, window_ns, end_ns)
        for minutes in horizons:
            future = _price_at(ts, ticks, event_ns + minutes * 60 * 1_000_000_000, end_ns)
            record[f"level_ret_{minutes}m"] = (future - level) * tick if future == future else np.nan
            record[f"move_ret_{minutes}m"] = (future - int(ticks[idx])) * tick if future == future else np.nan
            limit = min(event_ns + minutes * 60 * 1_000_000_000, end_ns)
            stop = int(np.searchsorted(ts, limit, side="left"))
            segment = ticks[int(idx):stop]
            if segment.size == 0:
                record[f"mfe_{minutes}m"] = np.nan
                record[f"mae_{minutes}m"] = np.nan
            else:
                delta = segment - level
                if approach == "from_below":
                    record[f"mfe_{minutes}m"] = float(delta.max() * tick)
                    record[f"mae_{minutes}m"] = float((-delta).max() * tick)
                elif approach == "from_above":
                    record[f"mfe_{minutes}m"] = float((-delta).max() * tick)
                    record[f"mae_{minutes}m"] = float(delta.max() * tick)
                else:
                    record[f"mfe_{minutes}m"] = float(np.abs(delta).max() * tick)
                    record[f"mae_{minutes}m"] = record[f"mfe_{minutes}m"]
        passage = "unresolved"
        first_cont = np.nan
        first_rev = np.nan
        if approach in ("from_above", "from_below") and path_px.size:
            gap = int(round(passage_pts / tick))
            if approach == "from_above":
                cont = np.flatnonzero(path_px <= level - gap)
                rev = np.flatnonzero(path_px >= level + gap)
            else:
                cont = np.flatnonzero(path_px >= level + gap)
                rev = np.flatnonzero(path_px <= level - gap)
            if cont.size:
                first_cont = (int(path_ts[int(cont[0])]) - event_ns) / 1_000_000_000
            if rev.size:
                first_rev = (int(path_ts[int(rev[0])]) - event_ns) / 1_000_000_000
            if first_cont == first_cont and first_rev == first_rev:
                passage = "continuation" if first_cont < first_rev else "reversal" if first_rev < first_cont else "same_print"
            elif first_cont == first_cont:
                passage = "continuation"
            elif first_rev == first_rev:
                passage = "reversal"
        record["passage"] = passage
        for points in targets:
            gap = int(round(points / tick))
            if approach == "from_above":
                hit = np.flatnonzero(path_px <= level - gap) if path_px.size else np.array([])
            elif approach == "from_below":
                hit = np.flatnonzero(path_px >= level + gap) if path_px.size else np.array([])
            else:
                hit = np.array([])
            record[f"time_to_{points}pt"] = (int(path_ts[int(hit[0])]) - event_ns) / 1_000_000_000 if hit.size else np.nan
        touches.append(record)

    step = int(cfg["followup_control_step_minutes"])
    minute_ns = 60 * 1_000_000_000
    n = int((end_ns - start_ns) // minute_ns)
    grid = start_ns + np.arange(n, dtype=np.int64) * minute_ns
    pos = np.searchsorted(ts, grid, side="left")
    valid = pos < len(ts)
    got = np.full(n, -1, dtype=np.int64)
    got[valid] = ts[pos[valid]]
    px = np.full(n, np.nan)
    keep = valid & (got < grid + minute_ns) & (got < end_ns)
    px[keep] = ticks[pos[keep]]
    away = np.isfinite(px) & (np.abs(px - level) > tol)
    minutes = pd.to_datetime(grid, unit="ns", utc=True).tz_convert(NY)
    buckets = _buckets((minutes.hour * 60 + minutes.minute).to_numpy(), cuts)
    controls: dict[int, tuple[np.ndarray, np.ndarray]] = {}
    for minutes_h in horizons:
        base = np.arange(0, n - minutes_h, minutes_h)
        mask = away[base] & np.isfinite(px[base + minutes_h])
        controls[minutes_h] = ((px[base[mask] + minutes_h] - px[base[mask]]) * tick, buckets[base[mask]])
    return touches, {"tercile": tercile, "controls": controls, "step": step}


def _stats(values: np.ndarray, seed: int, draws: int) -> dict:
    clean = np.asarray(values, dtype=float)
    clean = clean[np.isfinite(clean)]
    out = {"N": int(clean.size), "mean": np.nan, "median": np.nan, "std": np.nan, "p25": np.nan, "p75": np.nan, "positive_fraction": np.nan, "ci_low": np.nan, "ci_high": np.nan}
    if clean.size == 0:
        return out
    out["mean"] = float(np.mean(clean))
    out["median"] = float(np.median(clean))
    out["std"] = float(np.std(clean, ddof=1)) if clean.size > 1 else np.nan
    out["p25"] = float(np.percentile(clean, 25))
    out["p75"] = float(np.percentile(clean, 75))
    out["positive_fraction"] = float(np.mean(clean > 0))
    rng = np.random.default_rng(seed)
    means = clean[rng.integers(0, clean.size, size=(draws, clean.size))].mean(axis=1)
    out["ci_low"] = float(np.percentile(means, 2.5))
    out["ci_high"] = float(np.percentile(means, 97.5))
    return out


def _continuation(values: np.ndarray, approach: str) -> float:
    clean = np.asarray(values, dtype=float)
    clean = clean[np.isfinite(clean)]
    if clean.size == 0 or approach not in ("from_above", "from_below"):
        return np.nan
    if approach == "from_above":
        return float(np.mean(clean < 0))
    return float(np.mean(clean > 0))


def _row(study: str, group: str, horizon: str, stats: dict, extra: dict | None = None) -> dict:
    item = {"study": study, "group": group, "horizon": horizon, **stats}
    if extra:
        item.update(extra)
    return item


def reproduce(touches: pd.DataFrame) -> dict:
    frozen = pd.read_parquet(VP / "data" / "interaction_events.parquet")
    keep = (
        (frozen["level_name"] == "poc")
        & (frozen["approach"] == "from_above")
        & ~frozen["is_roll_transition"].astype(bool)
        & ~frozen["prev_is_roll_transition"].astype(bool)
        & frozen["is_complete"].astype(bool)
        & frozen["prev_is_complete"].astype(bool)
    )
    old = frozen.loc[keep, ["session_date", "ret_5m"]].copy()
    old["session_date"] = old["session_date"].astype(str).str[:10]
    new = touches[(touches["touch_group"] == "first") & (touches["approach"] == "from_above")][["session_date", "level_ret_5m"]].copy()
    merged = old.merge(new, on="session_date", how="outer", indicator=True)
    both = merged[merged["_merge"] == "both"]
    gap = np.nanmax(np.abs(both["ret_5m"] - both["level_ret_5m"])) if len(both) else np.nan
    ok = len(merged) == len(both) and len(old) == len(new) and np.isfinite(gap) and gap <= 1e-6
    return {"pass": bool(ok), "frozen_n": int(len(old)), "new_n": int(len(new)), "max_abs_gap": None if gap != gap else float(gap), "only_frozen": int((merged["_merge"] == "left_only").sum()), "only_new": int((merged["_merge"] == "right_only").sum())}


def write_report(summary: pd.DataFrame, meta: dict, cfg: dict) -> None:
    def pick(study: str, group: str, horizon: str) -> pd.Series:
        hit = summary[(summary["study"] == study) & (summary["group"] == group) & (summary["horizon"] == horizon)]
        return hit.iloc[0] if len(hit) else pd.Series(dtype=float)

    def num(value) -> str:
        if value is None or (isinstance(value, float) and not np.isfinite(value)):
            return "n/a"
        if isinstance(value, (int, np.integer)):
            return str(int(value))
        return f"{float(value):.3f}"

    above = pick("direction", "first|from_above", "5")
    below = pick("direction", "first|from_below", "5")
    lines = [
        "# POC follow-up",
        "",
        "This file does not replace the frozen first study. Profiles, the 70% value area, the roll marks, and the 1-tick touch were not changed.",
        "Horizons are 1, 3, 5, 10, 15, and 30 minutes. Point targets are 5, 10, 15, and 20. None of these were chosen by scanning results.",
        "A return is the later trade minus the previous POC, in index points, except where a control comparison uses the later trade minus the touch trade.",
        "Continuation means the later trade is on the same side the price came from: below the POC after a touch from above, above the POC after a touch from below.",
        "A new touch starts only after at least one trade has printed outside the 1-tick band.",
        f"Reproduction of the frozen first-touch-from-above 5-minute sample: {meta['reproduction']}.",
        "",
        "## 1. Direction",
        "",
        f"First touch from above, 5 minutes: N={num(above.get('N'))}, median={num(above.get('median'))}, mean={num(above.get('mean'))}, fraction below the POC={num(above.get('continuation_fraction'))}.",
        f"First touch from below, 5 minutes: N={num(below.get('N'))}, median={num(below.get('median'))}, mean={num(below.get('mean'))}, fraction above the POC={num(below.get('continuation_fraction'))}.",
        "The same rows are in `results/poc_followup_summary.csv` for every listed horizon. Horizons are not ranked.",
        "",
        "## 2. Unconditional 5-minute moves",
        "",
        "Controls are non-overlapping forward moves on a 1-minute grid, stepped by the horizon, inside the same CME session window. Minutes whose first trade is already within 1 tick of the previous POC are left out.",
        f"Previous-profile-range tercile edges, from eligible sessions only: {meta['tercile_edges']}.",
        f"Time buckets are the clock cuts in CONFIG.yaml, not cuts fit to the returns.",
        f"Matched percentile: each from-above first touch is placed in the control distribution of its own range tercile and time bucket. Median of those percentiles={num(meta.get('median_matched_percentile'))}. A value near 0.50 means the touch move is typical of that bucket. Unmatched events={meta.get('unmatched_events')}.",
        f"Share of all 5-minute control moves at or below the from-above median={num(meta.get('control_tail_fraction'))}. Control 5-minute median={num(meta.get('control_5m_median'))}, N={meta.get('control_5m_n')}.",
        "",
        "## 3. Where the session opens",
        "",
        "Open is the first trade. Above or below the previous POC uses the same 1-tick band. Inside value means the open is between previous VAL and VAH, inclusive. These are reported as two separate splits.",
        "",
        "## 4. First touch versus later touches",
        "",
        f"Eligible sessions with at least one POC touch: {meta.get('sessions_with_touch')}. Median touches per such session: {num(meta.get('median_touches'))}.",
        "",
        "## 5. Excursion",
        "",
        f"MFE is the farthest print in the approach direction over the horizon. MAE is the farthest print against it. Both are measured from the POC.",
        f"The 5-point passage uses a {cfg['followup_passage_window_minutes']}-minute window. Continuation means a {cfg['followup_passage_points']}-point move in the approach direction prints before a {cfg['followup_passage_points']}-point move the other way. Reversal is the opposite. Unresolved means neither printed. This is not an entry rule.",
        "",
        "## Limits",
        "",
        "- The from-above cell is still a few dozen sessions. A repeated sign is not a finished claim.",
        "- Thirteen roll-transition sessions stay out. The 150-point gap rule, not only contract id, marked most of them.",
        "- Control moves overlap in clock time across sessions. They do not overlap inside one session at a given horizon.",
        "- MBO order flow is not in this file.",
        "",
    ]
    path = VP / "reports" / "POC_FOLLOWUP.md"
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    cfg = load_config()
    research = _eligible(pd.read_parquet(VP / "data" / "session_research.parquet"))
    research["session_date"] = research["session_date"].astype(str).str[:10]
    ranges = research["prev_profile_range"].to_numpy(dtype=float)
    q1, q2 = [float(v) for v in np.quantile(ranges, [1 / 3, 2 / 3])]
    cuts = _cuts(cfg)
    wanted = {}
    for _, row in research.iterrows():
        wanted[pd.Timestamp(row["session_date"]).date()] = row
    touch_rows = []
    control_store = {int(h): {"ret": [], "bucket": [], "tercile": []} for h in cfg["followup_horizons_minutes"]}
    for session, trades in iter_session_trades(cfg):
        row = wanted.get(session)
        if row is None:
            continue
        touches, extra = analyze_session(trades, row, cfg, q1, q2, cuts)
        touch_rows.extend(touches)
        tercile = extra.get("tercile")
        for horizon, (rets, buckets) in extra.get("controls", {}).items():
            if len(rets) == 0:
                continue
            control_store[horizon]["ret"].append(rets)
            control_store[horizon]["bucket"].append(buckets)
            control_store[horizon]["tercile"].append(np.full(len(rets), tercile, dtype=object))
        print(f"[followup] {session} touches={len(touches)}", flush=True)
    touches = pd.DataFrame(touch_rows)
    out = VP / "results"
    out.mkdir(parents=True, exist_ok=True)
    touches.to_parquet(out / "poc_followup_touches.parquet", index=False)
    check = reproduce(touches)
    print(f"[followup] reproduction={check}", flush=True)
    if not check["pass"]:
        raise SystemExit("frozen first-touch sample was not reproduced; follow-up interpretation stopped")

    seed = int(cfg["bootstrap_seed"])
    draws = int(cfg["bootstrap_draws"])
    horizons = [int(v) for v in cfg["followup_horizons_minutes"]]
    dates = sorted(research["session_date"].unique())
    cut = dates[len(dates) // 2]
    summary = []
    directional = touches[touches["approach"].isin(["from_above", "from_below"])].copy()
    directional["half"] = np.where(directional["session_date"] < cut, "early", "late")
    for group_name, part in directional[directional["touch_group"] == "first"].groupby("approach"):
        for horizon in horizons:
            values = part[f"level_ret_{horizon}m"].to_numpy(dtype=float)
            stats = _stats(values, seed, draws)
            stats["continuation_fraction"] = _continuation(values, str(group_name))
            mfe = part[f"mfe_{horizon}m"].to_numpy(dtype=float)
            mae = part[f"mae_{horizon}m"].to_numpy(dtype=float)
            finite = np.isfinite(values)
            stats["median_mfe"] = float(np.nanmedian(mfe[finite])) if finite.any() else np.nan
            stats["median_mae"] = float(np.nanmedian(mae[finite])) if finite.any() else np.nan
            summary.append(_row("direction", f"first|{group_name}", str(horizon), stats))
            if horizon == 5:
                for half, half_part in part.groupby("half"):
                    half_values = half_part[f"level_ret_{horizon}m"].to_numpy(dtype=float)
                    half_stats = _stats(half_values, seed, draws)
                    half_stats["continuation_fraction"] = _continuation(half_values, str(group_name))
                    summary.append(_row("direction_half", f"first|{group_name}|{half}", str(horizon), half_stats))
    for keys, part in directional.groupby(["touch_group", "approach"]):
        touch_group, approach = keys
        for horizon in horizons:
            values = part[f"level_ret_{horizon}m"].to_numpy(dtype=float)
            stats = _stats(values, seed, draws)
            stats["continuation_fraction"] = _continuation(values, str(approach))
            summary.append(_row("touch_order", f"{touch_group}|{approach}", str(horizon), stats))
    first = directional[directional["touch_group"] == "first"]
    for column, study in (("open_vs_poc", "open_poc"), ("open_vs_value", "open_value")):
        for keys, part in first.groupby([column, "approach"]):
            label, approach = keys
            values = part["level_ret_5m"].to_numpy(dtype=float)
            stats = _stats(values, seed, draws)
            stats["continuation_fraction"] = _continuation(values, str(approach))
            summary.append(_row(study, f"{label}|{approach}", "5", stats))
    for keys, part in directional.groupby(["touch_group", "approach"]):
        touch_group, approach = keys
        counts = part["passage"].value_counts(normalize=True)
        raw = part["passage"].value_counts()
        summary.append(_row("passage", f"{touch_group}|{approach}", "30", {"N": int(len(part)), "mean": np.nan, "median": np.nan, "std": np.nan, "p25": np.nan, "p75": np.nan, "positive_fraction": np.nan, "ci_low": np.nan, "ci_high": np.nan, "continuation_share": float(counts.get("continuation", 0.0)), "reversal_share": float(counts.get("reversal", 0.0)), "unresolved_share": float(counts.get("unresolved", 0.0)), "continuation_n": int(raw.get("continuation", 0)), "reversal_n": int(raw.get("reversal", 0))}))
        for points in cfg["followup_excursion_points"]:
            times = part[f"time_to_{points}pt"].to_numpy(dtype=float)
            stats = _stats(times[np.isfinite(times)], seed, draws)
            stats["reached_fraction"] = float(np.mean(np.isfinite(times))) if len(times) else np.nan
            summary.append(_row("time_to_target", f"{touch_group}|{approach}|{points}pt", "30", stats))

    control_5 = None
    for horizon, parts in control_store.items():
        if not parts["ret"]:
            continue
        rets = np.concatenate(parts["ret"])
        buckets = np.concatenate(parts["bucket"])
        terciles = np.concatenate(parts["tercile"])
        stats = _stats(rets, seed, draws)
        summary.append(_row("control", "all", str(horizon), stats))
        if horizon == 5:
            control_5 = {"ret": rets, "bucket": buckets, "tercile": terciles}
            for label, sub in (("low", terciles == "low"), ("mid", terciles == "mid"), ("high", terciles == "high")):
                summary.append(_row("control", f"range_{label}", "5", _stats(rets[sub], seed, draws)))
    summary_frame = pd.DataFrame(summary)
    summary_frame.to_csv(out / "poc_followup_summary.csv", index=False)

    above_first = first[first["approach"] == "from_above"]
    event_moves = above_first["move_ret_5m"].to_numpy(dtype=float)
    event_level = above_first["level_ret_5m"].to_numpy(dtype=float)
    median_level = float(np.nanmedian(event_level))
    matched = []
    if control_5 is not None:
        for _, event in above_first.iterrows():
            mask = (control_5["tercile"] == event["range_tercile"]) & (control_5["bucket"] == event["time_bucket"])
            sample = control_5["ret"][mask]
            move = event["move_ret_5m"]
            if sample.size == 0 or move != move:
                continue
            matched.append(float(np.mean(sample <= move)))
        tail = float(np.mean(control_5["ret"] <= median_level))
        control_median = float(np.median(control_5["ret"]))
        control_n = int(control_5["ret"].size)
    else:
        tail = control_median = np.nan
        control_n = 0
    edges = [float(v) for v in cfg["followup_hist_edges"]]
    hist = {}
    for name, series in (
        ("from_above", above_first["level_ret_5m"].to_numpy(dtype=float)),
        ("from_below", first.loc[first["approach"] == "from_below", "level_ret_5m"].to_numpy(dtype=float)),
        ("control", control_5["ret"] if control_5 is not None else np.array([])),
    ):
        clean = series[np.isfinite(series)] if len(series) else np.array([])
        counts, _ = np.histogram(clean, bins=edges)
        hist[name] = [int(v) for v in counts]
    touch_counts = touches.groupby("session_date").size() if len(touches) else pd.Series(dtype=int)
    meta = {
        "reproduction": check,
        "half_cut": cut,
        "tercile_edges": [q1, q2],
        "median_matched_percentile": float(np.median(matched)) if matched else None,
        "matched_n": len(matched),
        "unmatched_events": int(len(above_first) - len(matched)),
        "control_tail_fraction": tail,
        "control_5m_median": control_median,
        "control_5m_n": control_n,
        "event_5m_median_level": median_level,
        "event_5m_median_move": float(np.nanmedian(event_moves)),
        "sessions_with_touch": int(touch_counts.size),
        "median_touches": float(touch_counts.median()) if len(touch_counts) else None,
        "hist_edges": edges,
        "hist": hist,
    }
    (out / "poc_followup_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    write_report(summary_frame, meta, cfg)
    print(f"[followup] done cut={cut} matched_percentile={meta['median_matched_percentile']}", flush=True)


if __name__ == "__main__":
    main()
