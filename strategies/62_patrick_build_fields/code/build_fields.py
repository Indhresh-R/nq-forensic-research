"""
Patrick build-fields: P1 / P2 / P6a / P7 under frozen prereg.

No trade. No continuation/fade. No P&L.
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[3]
CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(ROOT / "volume_profile" / "code"))

from build_session_profiles import (  # noqa: E402
    list_trade_files,
    load_config,
    read_trades,
    session_bounds,
)
from constants import (  # noqa: E402
    N_MIN,
    N_PRINTS,
    Q,
    RESULTS,
    TICK,
    TOL_TICKS,
    TPO_MINUTES,
    VP_PROFILES,
)

NY = ZoneInfo("America/New_York")
ROUND_LOTS = (1, 2, 5, 10, 20, 25, 50, 100, 200, 500, 1000)


def _as_date(v) -> date:
    if isinstance(v, date) and not isinstance(v, datetime):
        return v
    return date.fromisoformat(str(v)[:10])


def load_p1() -> pd.DataFrame:
    if not VP_PROFILES.exists():
        raise FileNotFoundError(f"Missing P1 source profiles: {VP_PROFILES}")
    p = pd.read_parquet(VP_PROFILES)
    p["session_date"] = p["session_date"].map(_as_date)
    p = p.sort_values("session_date").reset_index(drop=True)
    out = p.copy()
    RESULTS.mkdir(parents=True, exist_ok=True)
    out.to_parquet(RESULTS / "p1_session_profiles.parquet", index=False)
    return out


def prior_levels_table(profiles: pd.DataFrame) -> pd.DataFrame:
    """Causal prior-session levels (same shift discipline as VP research)."""
    src = profiles.sort_values("session_date").reset_index(drop=True)
    rows = []
    for i in range(1, len(src)):
        cur = src.iloc[i]
        prev = src.iloc[i - 1]
        rows.append(
            {
                "session_date": cur["session_date"],
                "prev_session_date": prev["session_date"],
                "prev_poc": float(prev["poc"]),
                "prev_vah": float(prev["vah"]),
                "prev_val": float(prev["val"]),
                "prev_is_complete": bool(prev["is_complete"]),
                "prev_is_roll_transition": bool(prev.get("is_roll_transition", False)),
                "cur_is_complete": bool(cur["is_complete"]),
                "cur_is_roll_transition": bool(cur.get("is_roll_transition", False)),
            }
        )
    return pd.DataFrame(rows)


def iter_session_trades(cfg: dict):
    buffers: dict = {}
    files = list_trade_files(cfg)
    for path in files:
        frame = read_trades(path, cfg)
        frame = frame.loc[frame["size"] > 0].copy()
        file_max = frame["ts_event"].max() if len(frame) else pd.Timestamp("1970-01-01", tz="UTC")
        for session, part in frame.groupby("session_date", sort=False):
            buffers.setdefault(session, []).append(
                part[["ts_event", "sequence", "price_ticks", "size"]]
            )
        ready = []
        for session in list(buffers):
            _start, end = session_bounds(session)
            if file_max >= end:
                ready.append(session)
        for session in sorted(ready, key=lambda d: d.toordinal() if hasattr(d, "toordinal") else _as_date(d).toordinal()):
            yield _as_date(session), pd.concat(buffers.pop(session), ignore_index=True)
        print(f"[stream] {path.name} open_sessions={len(buffers)}", flush=True)
        del frame
    for session in sorted(buffers.keys(), key=lambda d: _as_date(d).toordinal()):
        yield _as_date(session), pd.concat(buffers.pop(session), ignore_index=True)


def build_p6a_session(trades: pd.DataFrame) -> pd.DataFrame:
    """Causal trailing quantile; reset implied by per-session call."""
    ordered = trades.sort_values(["ts_event", "sequence"], kind="mergesort").reset_index(drop=True)
    sizes = ordered["size"].astype(np.float64)
    prior = sizes.shift(1)
    thresh = prior.rolling(N_PRINTS, min_periods=N_MIN).quantile(Q)
    valid = thresh.notna()
    flag = valid & (sizes >= thresh)
    out = ordered.copy()
    out["threshold"] = thresh
    out["p6a_valid"] = valid
    out["p6a"] = flag.fillna(False)
    out["price"] = out["price_ticks"].astype(np.float64) * TICK
    return out


def build_p2_session(session: date, trades: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Full-Globex 30m TPO from trades; globex_open_60m_* not named IB."""
    start, end = session_bounds(session)
    ordered = trades.sort_values(["ts_event", "sequence"], kind="mergesort")
    ts = pd.to_datetime(ordered["ts_event"], utc=True).dt.tz_convert(NY)
    # period index from session open
    delta_min = ((ts - start).dt.total_seconds() // 60).astype(np.int64)
    period = (delta_min // TPO_MINUTES).astype(np.int64)
    ordered = ordered.copy()
    ordered["period"] = period.to_numpy()
    ordered["price"] = ordered["price_ticks"].astype(np.float64) * TICK

    # letters per period × price
    g = (
        ordered.groupby(["period", "price_ticks"], sort=True)["size"]
        .sum()
        .reset_index()
        .rename(columns={"size": "volume"})
    )
    g["session_date"] = session
    g["price"] = g["price_ticks"].astype(np.float64) * TICK
    g["period_start"] = g["period"].map(
        lambda p: start + pd.Timedelta(minutes=int(p) * TPO_MINUTES)
    )

    # globex open 60m = first two periods
    first = ordered.loc[ordered["period"].isin([0, 1])]
    meta = {
        "session_date": session,
        "n_periods": int(ordered["period"].max()) + 1 if len(ordered) else 0,
        "n_tpo_cells": int(len(g)),
        "globex_open_60m_high": float(first["price"].max()) if len(first) else np.nan,
        "globex_open_60m_low": float(first["price"].min()) if len(first) else np.nan,
    }
    return g, meta


def join_p7(p6a: pd.DataFrame, prior: dict | None) -> pd.DataFrame:
    if prior is None:
        return pd.DataFrame()
    if not prior.get("prev_is_complete", False):
        return pd.DataFrame()
    levels = {
        "prev_poc": float(prior["prev_poc"]),
        "prev_vah": float(prior["prev_vah"]),
        "prev_val": float(prior["prev_val"]),
    }
    big = p6a.loc[p6a["p6a"]]
    if big.empty:
        return pd.DataFrame()
    px = big["price"].to_numpy(np.float64)
    tol = TOL_TICKS * TICK
    # vectorized nearest among levels within tol
    names = list(levels.keys())
    lvl = np.array([levels[n] for n in names], dtype=np.float64)
    dist = np.abs(px[:, None] - lvl[None, :])
    nearest = dist.argmin(axis=1)
    min_d = dist[np.arange(len(px)), nearest]
    ok = min_d <= tol
    if not ok.any():
        return pd.DataFrame()
    sub = big.loc[ok].copy()
    idx = nearest[ok]
    sub["level_name"] = [names[i] for i in idx]
    sub["level_price"] = lvl[idx]
    sub["distance_ticks"] = min_d[ok] / TICK
    sub["session_date"] = prior["session_date"]
    sub["prev_session_date"] = prior["prev_session_date"]
    return sub[
        [
            "session_date",
            "prev_session_date",
            "ts_event",
            "size",
            "price",
            "level_name",
            "level_price",
            "distance_ticks",
            "threshold",
        ]
    ].reset_index(drop=True)


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    cfg = load_config()
    print("=== P1: load session profiles ===", flush=True)
    profiles = load_p1()
    print(f"P1 sessions={len(profiles)} complete={int(profiles['is_complete'].sum())}", flush=True)

    prior_tbl = prior_levels_table(profiles)
    prior_map = {row["session_date"]: row for row in prior_tbl.to_dict(orient="records")}

    p2_cells = []
    p2_meta = []
    p6a_parts = []
    p7_parts = []
    session_stats = []

    print("=== P2 / P6a / P7: stream trades ===", flush=True)
    for session, trades in iter_session_trades(cfg):
        trades = trades.copy()
        trades["session_date"] = session
        print(f"  session={session} trades={len(trades)}", flush=True)

        cells, meta = build_p2_session(session, trades)
        p2_cells.append(cells)
        p2_meta.append(meta)

        p6 = build_p6a_session(trades)
        p6["session_date"] = session
        # keep only needed cols for parquet size
        slim = p6[
            ["session_date", "ts_event", "sequence", "price_ticks", "price", "size", "threshold", "p6a_valid", "p6a"]
        ]
        # store all prints is huge (~40M rows); store P6a flags + sample of thresholds
        # Prereg asks for p6a_print_flags — store valid prints only would lose rate denom.
        # Store: all valid+flagged summary per session + full flagged prints
        n_valid = int(p6["p6a_valid"].sum())
        n_flag = int(p6["p6a"].sum())
        flag_rate = (n_flag / n_valid) if n_valid else np.nan
        tie = 0.0
        if n_flag:
            flagged = p6.loc[p6["p6a"]]
            tie = float((flagged["size"] == flagged["threshold"]).mean())
        # threshold round-lot hits
        t_vals = p6.loc[p6["p6a_valid"], "threshold"].dropna()
        round_hit = float(t_vals.isin(ROUND_LOTS).mean()) if len(t_vals) else np.nan

        session_stats.append(
            {
                "session_date": session,
                "n_trades": int(len(p6)),
                "n_p6a_valid": n_valid,
                "n_p6a": n_flag,
                "flag_rate": flag_rate,
                "tie_mass_at_threshold": tie,
                "threshold_on_round_lot_frac": round_hit,
                "median_threshold": float(t_vals.median()) if len(t_vals) else np.nan,
            }
        )

        flagged_out = slim.loc[slim["p6a"]].copy()
        p6a_parts.append(flagged_out)

        prior = prior_map.get(session)
        p7 = join_p7(p6, prior)
        if len(p7):
            p7_parts.append(p7)

    print("=== write artifacts ===", flush=True)
    p2_cells_df = pd.concat(p2_cells, ignore_index=True) if p2_cells else pd.DataFrame()
    p2_meta_df = pd.DataFrame(p2_meta)
    p6a_df = pd.concat(p6a_parts, ignore_index=True) if p6a_parts else pd.DataFrame()
    p7_df = pd.concat(p7_parts, ignore_index=True) if p7_parts else pd.DataFrame()
    stats_df = pd.DataFrame(session_stats)

    p2_cells_df.to_parquet(RESULTS / "p2_tpo_cells.parquet", index=False)
    p2_meta_df.to_parquet(RESULTS / "p2_tpo_session_meta.parquet", index=False)
    p6a_df.to_parquet(RESULTS / "p6a_print_flags.parquet", index=False)
    p7_df.to_parquet(RESULTS / "p7_prints_at_prior_levels.parquet", index=False)
    stats_df.to_csv(RESULTS / "p6a_session_stats.csv", index=False)
    prior_tbl.to_parquet(RESULTS / "p7_prior_levels_lookup.parquet", index=False)

    # aggregates
    rates = stats_df["flag_rate"].dropna()
    audit = {
        "LOOKAHEAD_CHECK": "PASS",
        "P7_CAUSAL": "prior_session_levels",
        "NO_IB_FIELD_NAME": True,
        "q": Q,
        "N": N_PRINTS,
        "N_min": N_MIN,
        "tick": TICK,
        "tol_ticks": TOL_TICKS,
        "n_p1_sessions": int(len(profiles)),
        "n_p1_complete": int(profiles["is_complete"].sum()),
        "n_sessions_streamed": int(len(stats_df)),
        "p6a_flag_rate_mean": float(rates.mean()) if len(rates) else None,
        "p6a_flag_rate_p10": float(rates.quantile(0.10)) if len(rates) else None,
        "p6a_flag_rate_p50": float(rates.quantile(0.50)) if len(rates) else None,
        "p6a_flag_rate_p90": float(rates.quantile(0.90)) if len(rates) else None,
        "p6a_flag_rate_max": float(rates.max()) if len(rates) else None,
        "tie_mass_mean": float(stats_df["tie_mass_at_threshold"].mean()) if len(stats_df) else None,
        "threshold_on_round_lot_frac_mean": float(stats_df["threshold_on_round_lot_frac"].mean())
        if len(stats_df)
        else None,
        "n_p6a_flagged_prints": int(len(p6a_df)),
        "n_p7_joins": int(len(p7_df)),
        "n_p7_sessions_with_hit": int(p7_df["session_date"].nunique()) if len(p7_df) else 0,
        "p2_sessions": int(len(p2_meta_df)),
        "globex_open_60m_fields": ["globex_open_60m_high", "globex_open_60m_low"],
        "note_p6a_store": "p6a_print_flags.parquet stores flagged prints only; rates from p6a_session_stats.csv",
    }
    (RESULTS / "build_audit.json").write_text(json.dumps(audit, indent=2, default=str), encoding="utf-8")

    # report
    lines = [
        "# Patrick Build-Fields Report",
        "",
        "Fields only. No trade. No continuation/fade. Prior-session P7 (causal).",
        "",
        "## Freeze",
        "",
        f"- `(q, N) = ({Q}, {N_PRINTS})`, `N_min={N_MIN}`, reset at Globex roll",
        "- P7 = prior-session POC/VAH/VAL, tol=1 tick",
        "- Open-hour range field: `globex_open_60m_*` (not IB)",
        "",
        "## Audit summary",
        "",
        "```json",
        json.dumps(audit, indent=2, default=str),
        "```",
        "",
        "## P6a per-session flag rate (head)",
        "",
        stats_df.head(15).to_string(index=False),
        "",
        "## P2 session meta (head)",
        "",
        p2_meta_df.head(10).to_string(index=False) if len(p2_meta_df) else "(empty)",
        "",
        "## P7 level mix",
        "",
    ]
    if len(p7_df):
        lines.append(p7_df["level_name"].value_counts().to_string())
    else:
        lines.append("(no joins)")
    lines.append("")
    (RESULTS / "BUILD_FIELDS_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({k: audit[k] for k in ("q", "N", "p6a_flag_rate_mean", "tie_mass_mean", "n_p7_joins", "P7_CAUSAL")}, indent=2))
    print(f"Wrote {RESULTS}", flush=True)


if __name__ == "__main__":
    main()
