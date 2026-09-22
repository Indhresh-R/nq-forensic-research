"""Distribution tables for Strategy 52 market-state census (descriptive only)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(CODE))

from constants import DOW_NAMES, RESULTS, TOD_BLOCKS


def _pct_table(series: pd.Series, name: str = "state") -> pd.DataFrame:
    vc = series.value_counts(dropna=False)
    total = int(vc.sum())
    rows = []
    for state, n in vc.items():
        rows.append(
            {
                name: state if pd.notna(state) else "NA",
                "observations": int(n),
                "pct": 100.0 * float(n) / total if total else np.nan,
            }
        )
    out = pd.DataFrame(rows)
    out["total"] = total
    return out


def eligible(df: pd.DataFrame) -> pd.DataFrame:
    return df.loc[df["census_eligible"]].copy()


def overall_tables(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    e = eligible(df)
    return {
        "table1_composite_primary": _pct_table(e["composite_primary"]),
        "table1b_composite_flags": pd.DataFrame(
            [
                {
                    "state": name,
                    "observations": int(e[col].sum()),
                    "pct": 100.0 * float(e[col].mean()) if len(e) else np.nan,
                }
                for name, col in (
                    ("TRENDING", "flag_trending"),
                    ("CHOP_RANGE", "flag_chop"),
                    ("HIGH_ACTIVITY", "flag_high_activity"),
                    ("LOW_ACTIVITY", "flag_low_activity"),
                    ("COMPRESSION", "flag_compression"),
                    ("EXPANSION", "flag_expansion"),
                )
            ]
        ),
        "table2_directionality": _pct_table(e["directionality_state"]),
        "table3_volatility": _pct_table(e["volatility_state"]),
        "table4_volume": _pct_table(e["volume_state"]),
        "table5_range": _pct_table(e["range_state"]),
    }


def tod_tables(df: pd.DataFrame) -> pd.DataFrame:
    e = eligible(df)
    rows = []
    for block, (lo, hi) in TOD_BLOCKS.items():
        sub = e[(e["ny_min"] >= lo) & (e["ny_min"] < hi)]
        n = len(sub)
        if n == 0:
            continue
        for col, label in (
            ("directionality_state", "directionality"),
            ("volatility_state", "volatility"),
            ("volume_state", "volume"),
            ("range_state", "range"),
            ("composite_primary", "composite"),
        ):
            for state, cnt in sub[col].value_counts().items():
                rows.append(
                    {
                        "block": block,
                        "dimension": label,
                        "state": state,
                        "observations": int(cnt),
                        "pct": 100.0 * float(cnt) / n,
                        "block_n": n,
                    }
                )
    return pd.DataFrame(rows)


def dow_tables(df: pd.DataFrame) -> pd.DataFrame:
    e = eligible(df)
    # dow: 0=Mon .. 4=Fri for RTH
    rows = []
    for d in range(5):
        sub = e[e["dow"] == d]
        n = len(sub)
        if n == 0:
            continue
        name = DOW_NAMES[d]
        for col, label in (
            ("directionality_state", "directionality"),
            ("volatility_state", "volatility"),
            ("volume_state", "volume"),
            ("range_state", "range"),
            ("composite_primary", "composite"),
        ):
            for state, cnt in sub[col].value_counts().items():
                rows.append(
                    {
                        "dow": name,
                        "dow_i": d,
                        "dimension": label,
                        "state": state,
                        "observations": int(cnt),
                        "pct": 100.0 * float(cnt) / n,
                        "dow_n": n,
                    }
                )
    return pd.DataFrame(rows)


def year_tables(df: pd.DataFrame) -> pd.DataFrame:
    e = eligible(df)
    rows = []
    for y, sub in e.groupby("session_year", sort=True):
        n = len(sub)
        partial = bool(y == 2026)
        for col, label in (
            ("directionality_state", "directionality"),
            ("volatility_state", "volatility"),
            ("volume_state", "volume"),
            ("range_state", "range"),
            ("composite_primary", "composite"),
        ):
            for state, cnt in sub[col].value_counts().items():
                rows.append(
                    {
                        "year": int(y),
                        "partial_year": partial,
                        "dimension": label,
                        "state": state,
                        "observations": int(cnt),
                        "pct": 100.0 * float(cnt) / n,
                        "year_n": n,
                    }
                )
    return pd.DataFrame(rows)


def overlap_tables(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    e = eligible(df)
    n = len(e)
    pairs = [
        ("HIGH_DIRECTIONALITY", "HIGH_VOLATILITY", "directionality_state", "volatility_state"),
        ("HIGH_DIRECTIONALITY", "LOW_VOLATILITY", "directionality_state", "volatility_state"),
        ("LOW_DIRECTIONALITY", "HIGH_VOLATILITY", "directionality_state", "volatility_state"),
        ("LOW_DIRECTIONALITY", "LOW_VOLATILITY", "directionality_state", "volatility_state"),
        ("HIGH_VOLUME", "HIGH_VOLATILITY", "volume_state", "volatility_state"),
        ("HIGH_VOLUME", "LOW_VOLATILITY", "volume_state", "volatility_state"),
        ("LOW_VOLUME", "HIGH_VOLATILITY", "volume_state", "volatility_state"),
        ("LOW_VOLUME", "LOW_VOLATILITY", "volume_state", "volatility_state"),
        ("COMPRESSION", "LOW_DIRECTIONALITY", "range_state", "directionality_state"),
        ("EXPANSION", "HIGH_DIRECTIONALITY", "range_state", "directionality_state"),
        ("COMPRESSION", "HIGH_DIRECTIONALITY", "range_state", "directionality_state"),
        ("EXPANSION", "LOW_DIRECTIONALITY", "range_state", "directionality_state"),
    ]
    rows = []
    for a, b, ca, cb in pairs:
        mask = (e[ca] == a) & (e[cb] == b)
        cnt = int(mask.sum())
        rows.append(
            {
                "combo": f"{a} + {b}",
                "observations": cnt,
                "pct_of_eligible": 100.0 * cnt / n if n else np.nan,
            }
        )
    # Full 2x2 directionality x volatility
    ct = pd.crosstab(e["directionality_state"], e["volatility_state"], margins=True)
    ct_pct = pd.crosstab(
        e["directionality_state"], e["volatility_state"], normalize="all"
    ) * 100.0
    return {
        "overlap_key_combos": pd.DataFrame(rows),
        "crosstab_dir_x_vol_counts": ct.reset_index(),
        "crosstab_dir_x_vol_pct": ct_pct.reset_index(),
        "crosstab_vol_x_vlm_pct": (
            pd.crosstab(e["volatility_state"], e["volume_state"], normalize="all") * 100.0
        ).reset_index(),
        "crosstab_dir_x_range_pct": (
            pd.crosstab(e["directionality_state"], e["range_state"], normalize="all")
            * 100.0
        ).reset_index(),
    }


def continuous_summaries(df: pd.DataFrame) -> dict:
    e = eligible(df)
    cols = [
        "er_30",
        "er_60",
        "er_120",
        "rv_30",
        "rv_60",
        "atr_30",
        "range_30",
        "range_60",
        "range_norm_30",
        "range_norm_60",
        "volume",
        "vol_roll_30",
        "rvol",
    ]
    summary = {}
    for c in cols:
        if c not in e.columns:
            continue
        v = e[c].to_numpy(np.float64)
        v = v[np.isfinite(v)]
        if len(v) == 0:
            continue
        summary[c] = {
            "n": int(len(v)),
            "mean": float(np.mean(v)),
            "std": float(np.std(v)),
            "p10": float(np.quantile(v, 0.10)),
            "p25": float(np.quantile(v, 0.25)),
            "p50": float(np.quantile(v, 0.50)),
            "p75": float(np.quantile(v, 0.75)),
            "p90": float(np.quantile(v, 0.90)),
        }
    return summary


def main() -> None:
    path = RESULTS / "market_states.parquet"
    df = pd.read_parquet(path)
    print(f"Loaded states rows={len(df):,}")

    tables = overall_tables(df)
    for name, tab in tables.items():
        tab.to_csv(RESULTS / f"{name}.csv", index=False)

    tod = tod_tables(df)
    tod.to_csv(RESULTS / "table6_time_of_day.csv", index=False)

    dow = dow_tables(df)
    dow.to_csv(RESULTS / "table_day_of_week.csv", index=False)

    years = year_tables(df)
    years.to_csv(RESULTS / "table7_year_stability.csv", index=False)

    overlaps = overlap_tables(df)
    for name, tab in overlaps.items():
        tab.to_csv(RESULTS / f"{name}.csv", index=False)

    cont = continuous_summaries(df)
    (RESULTS / "continuous_feature_summary.json").write_text(
        json.dumps(cont, indent=2), encoding="utf-8"
    )

    # Bundle for report writer
    bundle = {
        "n_eligible": int(df["census_eligible"].sum()),
        "n_analysis_window": int(len(df)),
        "tables": {k: v.to_dict(orient="records") for k, v in tables.items()},
    }
    (RESULTS / "distribution_bundle.json").write_text(
        json.dumps(bundle, indent=2, default=str), encoding="utf-8"
    )
    print("Distribution tables written.")


if __name__ == "__main__":
    main()
