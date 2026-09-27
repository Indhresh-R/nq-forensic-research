"""Predeclared mechanism tests. No threshold search and no trading rule."""

from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_session_profiles import VP, load_config, read_trades, trades_dir

REQUIRED = (
    "session_assignment",
    "no_lookahead",
    "volume_conservation",
    "poc_correctness",
    "value_area_correctness",
    "tick_alignment",
    "determinism",
    "partition_equivalence",
    "event_timestamp_integrity",
    "same_event_contamination",
)
TOUCH_LEVELS = ("poc", "vah", "val")
HORIZONS = None


def require_validation() -> None:
    status = json.loads((VP / "data" / "validation_status.json").read_text(encoding="utf-8"))
    if status.get("failed_test"):
        raise SystemExit(f"validation failed: {status['failed_test']}")
    missing = [name for name in REQUIRED if status.get(name) != "pass"]
    if missing:
        raise SystemExit("validation incomplete: " + ", ".join(missing))


def usable(frame: pd.DataFrame) -> pd.DataFrame:
    mask = (
        ~frame["is_roll_transition"].astype(bool)
        & ~frame["prev_is_roll_transition"].astype(bool)
        & frame["is_complete"].astype(bool)
        & frame["prev_is_complete"].astype(bool)
    )
    return frame.loc[mask].copy()


def directional(frame: pd.DataFrame) -> pd.DataFrame:
    return frame[frame["approach"].isin(["from_below", "from_above"])].copy()


def summarize(values: np.ndarray, mfe: np.ndarray | None, mae: np.ndarray | None, seed: int, draws: int) -> dict:
    clean = values[np.isfinite(values)]
    out = {
        "N": int(clean.size),
        "mean": np.nan,
        "median": np.nan,
        "std": np.nan,
        "p25": np.nan,
        "p75": np.nan,
        "positive_fraction": np.nan,
        "mean_MFE": np.nan,
        "median_MFE": np.nan,
        "mean_MAE": np.nan,
        "median_MAE": np.nan,
        "ci_low": np.nan,
        "ci_high": np.nan,
    }
    if clean.size == 0:
        return out
    out["mean"] = float(np.mean(clean))
    out["median"] = float(np.median(clean))
    out["std"] = float(np.std(clean, ddof=1)) if clean.size > 1 else np.nan
    out["p25"] = float(np.percentile(clean, 25))
    out["p75"] = float(np.percentile(clean, 75))
    out["positive_fraction"] = float(np.mean(clean > 0))
    if mfe is not None:
        mfe_clean = mfe[np.isfinite(values) & np.isfinite(mfe)]
        mae_clean = mae[np.isfinite(values) & np.isfinite(mae)]
        if mfe_clean.size:
            out["mean_MFE"] = float(np.mean(mfe_clean))
            out["median_MFE"] = float(np.median(mfe_clean))
        if mae_clean.size:
            out["mean_MAE"] = float(np.mean(mae_clean))
            out["median_MAE"] = float(np.median(mae_clean))
    rng = np.random.default_rng(seed)
    sample = clean[rng.integers(0, clean.size, size=(draws, clean.size))].mean(axis=1)
    out["ci_low"] = float(np.percentile(sample, 2.5))
    out["ci_high"] = float(np.percentile(sample, 97.5))
    return out


def row_from(study: str, group: str, metric: str, stats: dict, period: str = "all") -> dict:
    return {"study": study, "group": group, "period": period, "metric": metric, **stats}


def assign_distance(value: float, bins: list) -> str:
    for lo, hi, label in bins:
        lo_v = -np.inf if lo is None else float(lo)
        hi_v = np.inf if hi is None else float(hi)
        if lo_v <= value < hi_v:
            return str(label)
    return "unbinned"


def assign_migration(value: float, bins: list) -> str:
    for lo, hi, label in bins:
        lo_v = -np.inf if lo is None else float(lo)
        hi_v = np.inf if hi is None else float(hi)
        if lo_v < value <= hi_v:
            return str(label)
    return "unbinned"


def month_name(value: str) -> str:
    return pd.Timestamp(value).strftime("%B")


def half_label(dates: pd.Series) -> pd.Series:
    ordered = sorted(dates.astype(str).unique())
    cut = ordered[len(ordered) // 2]
    return np.where(dates.astype(str) < cut, "early", "late")


def touch_tables(events: pd.DataFrame, cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    seed = int(cfg["bootstrap_seed"])
    draws = int(cfg["bootstrap_draws"])
    horizons = [int(v) for v in cfg["horizons_minutes"]]
    summary_rows = []
    monthly_rows = []
    base = directional(usable(events))
    base["month"] = base["session_date"].map(month_name)
    base["half"] = half_label(base["session_date"])
    for level in TOUCH_LEVELS:
        part = base[base["level_name"] == level]
        for approach in ("from_below", "from_above"):
            block = part[part["approach"] == approach]
            for minutes in horizons:
                metric = f"ret_{minutes}m"
                stats = summarize(
                    block[metric].to_numpy(dtype=float),
                    block[f"mfe_{minutes}m"].to_numpy(dtype=float),
                    block[f"mae_{minutes}m"].to_numpy(dtype=float),
                    seed,
                    draws,
                )
                summary_rows.append(row_from("first_touch", f"{level}|{approach}", metric, stats))
                if minutes == 5:
                    for period_name, period_frame in list(block.groupby("month")) + list(block.groupby("half")):
                        period_stats = summarize(
                            period_frame[metric].to_numpy(dtype=float),
                            period_frame["mfe_5m"].to_numpy(dtype=float),
                            period_frame["mae_5m"].to_numpy(dtype=float),
                            seed,
                            draws,
                        )
                        monthly_rows.append(row_from("first_touch", f"{level}|{approach}", metric, period_stats, str(period_name)))
        crossed = usable(events)
        crossed = crossed[(crossed["level_name"] == level) & crossed["level_name"].isin(["vah", "val"])]
        if level in ("vah", "val") and "time_to_cross_sec" in events.columns:
            subset = directional(usable(events))
            subset = subset[subset["level_name"] == level]
            observed = subset["time_to_cross_sec"].to_numpy(dtype=float)
            finite = np.isfinite(observed)
            summary_rows.append(
                row_from(
                    "cross",
                    level,
                    "time_to_cross_sec",
                    summarize(observed[finite], None, None, seed, draws) | {"N": int(subset.shape[0]), "positive_fraction": float(finite.mean()) if len(subset) else np.nan},
                )
            )
            excursion = subset.loc[finite, "excursion_after_cross"].to_numpy(dtype=float) if finite.any() else np.array([])
            summary_rows.append(row_from("cross", level, "excursion_after_cross", summarize(excursion, None, None, seed, draws)))
    summary = pd.DataFrame(summary_rows)
    monthly = pd.DataFrame(monthly_rows)
    touch = {}
    for level in TOUCH_LEVELS:
        touch[level] = summary[(summary["study"] == "first_touch") & summary["group"].str.startswith(level + "|")].copy()
    return touch["poc"], touch["vah"], touch["val"], summary, monthly


def location_and_migration(events: pd.DataFrame, research: pd.DataFrame, profiles: pd.DataFrame, cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    seed = int(cfg["bootstrap_seed"])
    draws = int(cfg["bootstrap_draws"])
    sessions = usable(research)
    sessions["distance_ratio"] = np.where(
        sessions["prev_profile_range"].to_numpy(dtype=float) > 0,
        np.abs(sessions["open_price"] - sessions["prev_poc"]) / sessions["prev_profile_range"],
        np.nan,
    )
    sessions["distance_bin"] = [
        assign_distance(v, cfg["distance_bins"]) if np.isfinite(v) else "undefined_range" for v in sessions["distance_ratio"]
    ]
    sessions["location"] = np.where(
        sessions["open_price"] < sessions["prev_val"],
        "below_val",
        np.where(sessions["open_price"] > sessions["prev_vah"], "above_vah", "inside_value"),
    )
    poc_events = directional(usable(events))
    poc_events = poc_events[poc_events["level_name"] == "poc"][
        ["session_date", "event_ts", "approach", "ret_5m", "ret_60m", "mfe_60m", "mae_60m"]
    ].rename(columns={"approach": "poc_approach", "event_ts": "poc_event_ts"})
    boundary = usable(events)
    boundary = boundary[boundary["level_name"].isin(["vah", "val"])][
        ["session_date", "level_name", "event_ts", "approach", "ret_5m", "mfe_60m", "mae_60m"]
    ]
    first_trade = profiles[["session_date", "first_trade_ts"]].copy()
    first_trade["session_date"] = first_trade["session_date"].astype(str).str[:10]
    sessions["session_date"] = sessions["session_date"].astype(str).str[:10]
    poc_events["session_date"] = poc_events["session_date"].astype(str).str[:10]
    boundary["session_date"] = boundary["session_date"].astype(str).str[:10]
    joined = sessions.merge(first_trade, on="session_date", how="left").merge(poc_events, on="session_date", how="left")
    rows = []
    monthly = []
    for label, part in joined.groupby("location"):
        stats = summarize(part["ret_5m"].to_numpy(dtype=float), part["mfe_60m"].to_numpy(dtype=float), part["mae_60m"].to_numpy(dtype=float), seed, draws)
        rows.append(row_from("profile_location", str(label), "poc_ret_5m", stats))
        part = part.copy()
        part["month"] = part["session_date"].map(month_name)
        for month, month_part in part.groupby("month"):
            monthly.append(
                row_from(
                    "profile_location",
                    str(label),
                    "poc_ret_5m",
                    summarize(month_part["ret_5m"].to_numpy(dtype=float), month_part["mfe_60m"].to_numpy(dtype=float), month_part["mae_60m"].to_numpy(dtype=float), seed, draws),
                    str(month),
                )
            )
    for label, part in joined.groupby("distance_bin"):
        stats = summarize(part["ret_5m"].to_numpy(dtype=float), part["mfe_60m"].to_numpy(dtype=float), part["mae_60m"].to_numpy(dtype=float), seed, draws)
        rows.append(row_from("distance_from_poc", str(label), "poc_ret_5m", stats))
    # Migration known at the start of D is (POC of D-1 minus POC of D-2) / range of D-2.
    ordered = profiles.sort_values("session_date").reset_index(drop=True)
    ordered["session_date"] = ordered["session_date"].astype(str).str[:10]
    ordered["migration_ratio"] = (ordered["poc"] - ordered["poc"].shift(1)) / ordered["profile_range"].shift(1)
    ordered["migration_for_next"] = ordered["migration_ratio"].shift(1)
    ordered["roll_d2"] = ordered["is_roll_transition"].shift(2).fillna(False).astype(bool)
    mig = joined.merge(ordered[["session_date", "migration_for_next", "roll_d2"]], on="session_date", how="left")
    mig = mig[~mig["roll_d2"].astype(bool) & mig["migration_for_next"].notna()].copy()
    mig["migration_bin"] = [assign_migration(float(v), cfg["migration_bins"]) for v in mig["migration_for_next"]]
    mig_rows = []
    for label, part in mig.groupby("migration_bin"):
        stats = summarize(part["ret_5m"].to_numpy(dtype=float), part["mfe_60m"].to_numpy(dtype=float), part["mae_60m"].to_numpy(dtype=float), seed, draws)
        location_share = part["location"].value_counts(normalize=True)
        stats = stats | {
            "share_below_val": float(location_share.get("below_val", 0.0)),
            "share_inside_value": float(location_share.get("inside_value", 0.0)),
            "share_above_vah": float(location_share.get("above_vah", 0.0)),
        }
        mig_rows.append(row_from("poc_migration", str(label), "poc_ret_5m", stats))
    # Boundary timing is descriptive and is stored beside the location rows.
    boundary_rows = []
    for _, row in joined.iterrows():
        if row["location"] == "inside_value":
            boundary_rows.append({"session_date": row["session_date"], "location": row["location"], "time_to_value_sec": 0.0, "time_to_poc_sec": _seconds(row["first_trade_ts"], row["poc_event_ts"])})
        else:
            level = "val" if row["location"] == "below_val" else "vah"
            hit = boundary[(boundary["session_date"] == row["session_date"]) & (boundary["level_name"] == level)]
            event_ts = hit["event_ts"].iloc[0] if len(hit) else pd.NaT
            boundary_rows.append(
                {
                    "session_date": row["session_date"],
                    "location": row["location"],
                    "time_to_value_sec": _seconds(row["first_trade_ts"], event_ts),
                    "time_to_poc_sec": _seconds(row["first_trade_ts"], row["poc_event_ts"]),
                }
            )
    timing = pd.DataFrame(boundary_rows)
    for label, part in timing.groupby("location"):
        rows.append(row_from("profile_location", str(label), "time_to_value_sec", summarize(part["time_to_value_sec"].to_numpy(dtype=float), None, None, seed, draws)))
        rows.append(row_from("profile_location", str(label), "time_to_poc_sec", summarize(part["time_to_poc_sec"].to_numpy(dtype=float), None, None, seed, draws)))
    return pd.DataFrame(rows), pd.DataFrame(mig_rows), pd.DataFrame(monthly), joined


def _seconds(start, end) -> float:
    if pd.isna(start) or pd.isna(end):
        return np.nan
    return (pd.Timestamp(end) - pd.Timestamp(start)).total_seconds()


def write_plots(events: pd.DataFrame, profiles: pd.DataFrame, vap: pd.DataFrame, research: pd.DataFrame, cfg: dict) -> str:
    figures = VP / "reports" / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    base = directional(usable(events))
    eligible_dates = sorted(usable(research)["session_date"].astype(str).str[:10].unique())
    example = eligible_dates[len(eligible_dates) // 2]
    example_vap = vap[vap["session_date"].astype(str).str[:10] == example]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(example_vap["price"], example_vap["volume"], color="black", linewidth=0.8)
    ax.set_title(f"Volume at price, CME session {example}")
    ax.set_xlabel("price")
    ax.set_ylabel("volume")
    fig.tight_layout()
    fig.savefig(figures / "example_volume_profile.png", dpi=100)
    plt.close(fig)

    prev = research[research["session_date"].astype(str).str[:10] == example]
    prev_date = str(prev["prev_session_date"].iloc[0])[:10] if len(prev) else example
    prev_vap = vap[vap["session_date"].astype(str).str[:10] == prev_date]
    path = _session_path(example, cfg)
    fig, ax = plt.subplots(figsize=(8, 4))
    if len(prev_vap):
        ax2 = ax.twiny()
        ax2.barh(prev_vap["price"], prev_vap["volume"], height=float(cfg["tick_size"]), color="0.75")
        ax2.set_xlabel("previous-session volume")
    if len(path):
        ax.plot(path["minute"], path["price"], color="black", linewidth=0.8)
    if len(prev):
        for name, color in (("prev_poc", "C0"), ("prev_vah", "C1"), ("prev_val", "C2")):
            ax.axhline(float(prev[name].iloc[0]), color=color, linewidth=0.7, label=name)
        ax.legend(fontsize=8)
    ax.set_title(f"Session {example} price and previous profile {prev_date}")
    ax.set_ylabel("price")
    fig.tight_layout()
    fig.savefig(figures / "example_previous_profile_path.png", dpi=100)
    plt.close(fig)

    for level in TOUCH_LEVELS:
        part = base[base["level_name"] == level]
        fig, ax = plt.subplots(figsize=(8, 4))
        values = part["ret_5m"].to_numpy(dtype=float)
        values = values[np.isfinite(values)]
        if values.size:
            ax.hist(values, bins=40, color="0.3")
        ax.axvline(0, color="black", linewidth=0.6)
        ax.set_title(f"5-minute price minus {level.upper()} after first touch")
        ax.set_xlabel("points")
        fig.tight_layout()
        fig.savefig(figures / f"{level}_5m_excursion.png", dpi=100)
        plt.close(fig)

    ordered = profiles.sort_values("session_date").copy()
    migration = ordered["poc"] - ordered["poc"].shift(1)
    keep = ~ordered["is_roll_transition"].astype(bool) & ~ordered["is_roll_transition"].shift(1).fillna(False).astype(bool)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(migration[keep].dropna().to_numpy(dtype=float), bins=40, color="0.3")
    ax.axvline(0, color="black", linewidth=0.6)
    ax.set_title("Completed POC migration, points")
    ax.set_xlabel("POC minus previous POC")
    fig.tight_layout()
    fig.savefig(figures / "poc_migration.png", dpi=100)
    plt.close(fig)

    counts = base[base["level_name"] == "poc"].copy()
    counts["month"] = counts["session_date"].map(month_name)
    order = ["March", "April", "May", "June", "July", "August", "September"]
    tally = counts["month"].value_counts().reindex(order).fillna(0)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(tally.index, tally.to_numpy(), color="0.3")
    ax.set_title("POC first-touch sample by month")
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    fig.savefig(figures / "monthly_sample_counts.png", dpi=100)
    plt.close(fig)
    return example


def _session_path(session: str, cfg: dict) -> pd.DataFrame:
    day = date.fromisoformat(session[:10])
    frames = []
    for offset in (0, 1):
        stamp = day + timedelta(days=offset)
        path = trades_dir(cfg) / f"trades_24h_{stamp.isoformat()}.dbn.zst"
        if not path.exists():
            continue
        frame = read_trades(path, cfg)
        frame = frame[frame["session_date"] == day]
        frames.append(frame)
    if not frames:
        return pd.DataFrame(columns=["minute", "price"])
    trades = pd.concat(frames, ignore_index=True).sort_values(["ts_event", "sequence"])
    trades["minute"] = trades["ts_event"].dt.floor("min")
    last = trades.groupby("minute", sort=True)["price_ticks"].last() * float(cfg["tick_size"])
    return pd.DataFrame({"minute": last.index, "price": last.to_numpy()})


def fmt(value) -> str:
    if value is None or (isinstance(value, float) and not np.isfinite(value)):
        return "n/a"
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    return f"{float(value):.3f}"


def write_mechanism_report(summary: pd.DataFrame, location: pd.DataFrame, migration: pd.DataFrame, monthly: pd.DataFrame, example: str, cfg: dict) -> None:
    def pick(frame: pd.DataFrame, group: str, metric: str, period: str = "all") -> pd.Series:
        hit = frame[(frame["group"] == group) & (frame["metric"] == metric) & (frame["period"] == period)]
        return hit.iloc[0] if len(hit) else pd.Series(dtype=float)

    lines = [
        "# Mechanism report",
        "",
        "These are conditional descriptions. They are not a trading rule.",
        "Parameters were fixed in CONFIG.yaml before the results were read.",
        f"Touch tolerance is {cfg['interaction_tolerance_ticks']} NQ tick. Horizons are {cfg['horizons_minutes']} minutes.",
        f"Crossing continuation is {cfg['cross_ticks']} ticks, observed for {cfg['cross_observe_minutes']} minutes.",
        "Return means the later trade price minus the touched level, in index points. A positive number means the later trade printed above the level.",
        "MFE and MAE are path statistics over the same window, measured in the direction of the recorded approach. They are not a result.",
        "Bootstrap intervals are percentile intervals of the mean, seed "
        f"{cfg['bootstrap_seed']}, {cfg['bootstrap_draws']} draws. With about six months of sessions they describe sampling variation. They are not a license to rank horizons.",
        "",
        "## POC first touch",
        "",
        "Question: after the next complete CME session first trades within one tick of the previous POC, where is price at the fixed horizons?",
        "",
        "Definition: first trade in `(ts_event, sequence)` order with absolute distance of at most one tick. Approach uses the last earlier trade outside that band. Ambiguous opens are excluded from these rows. Roll-transition sessions and incomplete sessions are excluded.",
        "",
    ]
    for approach in ("from_below", "from_above"):
        stats = pick(summary, f"poc|{approach}", "ret_5m")
        lines.append(
            f"Sample, {approach}: N={fmt(stats.get('N'))}. Median 5-minute price-minus-POC={fmt(stats.get('median'))}. "
            f"Mean={fmt(stats.get('mean'))} (interval {fmt(stats.get('ci_low'))} to {fmt(stats.get('ci_high'))}). "
            f"Fraction above the level={fmt(stats.get('positive_fraction'))}. "
            f"Median 5-minute MFE={fmt(stats.get('median_MFE'))}, MAE={fmt(stats.get('median_MAE'))}."
        )
        early = monthly[(monthly["group"] == f"poc|{approach}") & (monthly["period"] == "early")]
        late = monthly[(monthly["group"] == f"poc|{approach}") & (monthly["period"] == "late")]
        if len(early) and len(late):
            lines.append(
                f"Stability, {approach}: early median={fmt(early.iloc[0]['median'])} (N={fmt(early.iloc[0]['N'])}); "
                f"late median={fmt(late.iloc[0]['median'])} (N={fmt(late.iloc[0]['N'])})."
            )
    lines.extend(
        [
            "",
            "The same fixed calculation is in `results/poc_first_touch.csv` for 1, 15, 30, and 60 minutes. Those horizons were not ranked.",
            "",
            "## VAH and VAL first touch",
            "",
            "Question: after the first trade within one tick of the previous value-area boundary, does the later trade sit beyond that boundary or back inside it?",
            "",
            "Definition: same touch and approach rules as POC. For an approach from below, a later trade above VAH has crossed upward. For an approach from above, a later trade below VAL has crossed downward. The sign reported here is still price minus the level, so the two boundaries are not flipped into a common score.",
            "",
        ]
    )
    for level in ("vah", "val"):
        for approach in ("from_below", "from_above"):
            stats = pick(summary, f"{level}|{approach}", "ret_5m")
            lines.append(
                f"{level.upper()} {approach}: N={fmt(stats.get('N'))}, median 5-minute price-minus-level={fmt(stats.get('median'))}, "
                f"mean={fmt(stats.get('mean'))}, fraction above the level={fmt(stats.get('positive_fraction'))}."
            )
        cross = summary[(summary["study"] == "cross") & (summary["group"] == level) & (summary["metric"] == "time_to_cross_sec")]
        if len(cross):
            lines.append(
                f"{level.upper()} cross check: share of directional touches that print {cfg['cross_ticks']} ticks through the boundary "
                f"before the session window ends={fmt(cross.iloc[0]['positive_fraction'])}. "
                f"This share is not a selected threshold."
            )
    lines.extend(
        [
            "",
            "## Opening location and distance from previous POC",
            "",
            "Question: where does the first trade of session D sit relative to the previous value area and previous POC, and what is the 5-minute response after the later POC touch?",
            "",
            "Definition: open is the first trade of session D. Location is below previous VAL, inside previous VAL to VAH, or above previous VAH. Distance bins are the predeclared fractions of the previous profile range. A zero range is left undefined.",
            "",
        ]
    )
    if len(location):
        show = location[(location["metric"] == "poc_ret_5m") & (location["period"] == "all")]
        for _, item in show.iterrows():
            lines.append(
                f"{item['study']} {item['group']}: N={fmt(item['N'])}, median 5-minute POC response={fmt(item['median'])}, mean={fmt(item['mean'])}."
            )
    lines.extend(
        [
            "",
            "## POC migration",
            "",
            "Question: is the already completed migration from POC(D-2) to POC(D-1), scaled by the D-2 profile range, associated with where session D opens or with the later 5-minute POC response?",
            "",
            "Definition: session D does not contribute its own POC. Rows are dropped when D, D-1, or D-2 is a roll transition. Bins were declared in CONFIG.yaml.",
            "",
        ]
    )
    for _, item in migration.iterrows():
        lines.append(
            f"{item['group']}: N={fmt(item['N'])}, median 5-minute POC response={fmt(item['median'])}, "
            f"share inside previous value={fmt(item.get('share_inside_value'))}, "
            f"share below VAL={fmt(item.get('share_below_val'))}, share above VAH={fmt(item.get('share_above_vah'))}."
        )
    lines.extend(
        [
            "",
            "## Limitations",
            "",
            "- About six months of one continuous contract series. A month with a small N cannot confirm or reject a mechanism.",
            "- `NQ.c.0` changes contracts. Flagged transition sessions are removed from these tables rather than back-adjusted.",
            "- The first and last sessions can be incomplete because the files start and end on UTC midnights. The 30-minute coverage rule removes them. It does not use the later price path.",
            "- Forward prices stop at the session boundary. A horizon that would run into the next session is left empty.",
            "- Same-timestamp order is Databento sequence, not an exchange match-time finer than that.",
            f"- The diagnostic profile and path use the middle eligible session date {example}, not a date chosen after seeing the response.",
            "- No horizon, tolerance, value-area percentage, or bin was changed after seeing these numbers.",
            "",
        ]
    )
    path = VP / "reports" / "MECHANISM_REPORT.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    require_validation()
    cfg = load_config()
    events = pd.read_parquet(VP / "data" / "interaction_events.parquet")
    research = pd.read_parquet(VP / "data" / "session_research.parquet")
    profiles = pd.read_parquet(VP / "data" / "session_profiles.parquet")
    vap = pd.read_parquet(VP / "data" / "session_volume_profile.parquet")
    poc, vah, val, summary, monthly_touch = touch_tables(events, cfg)
    location, migration, monthly_location, _joined = location_and_migration(events, research, profiles, cfg)
    results = VP / "results"
    results.mkdir(parents=True, exist_ok=True)
    poc.to_csv(results / "poc_first_touch.csv", index=False)
    vah.to_csv(results / "vah_first_touch.csv", index=False)
    val.to_csv(results / "val_first_touch.csv", index=False)
    location.to_csv(results / "value_location.csv", index=False)
    migration.to_csv(results / "poc_migration.csv", index=False)
    summary.to_csv(results / "mechanism_summary.csv", index=False)
    monthly = pd.concat([monthly_touch, monthly_location], ignore_index=True)
    monthly.to_csv(results / "monthly_stability.csv", index=False)
    example = write_plots(events, profiles, vap, research, cfg)
    write_mechanism_report(summary, location, migration, monthly, example, cfg)
    print(f"[mechanism] example_session={example} summary_rows={len(summary)}", flush=True)


if __name__ == "__main__":
    main()
