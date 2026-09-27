"""
Classify market-state features into predetermined tercile buckets.

Thresholds are frozen on IS years (2010–2021) only, then applied to all years.
"""
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

from constants import (
    COMPOSITE_CHOP,
    COMPOSITE_COMPRESSION,
    COMPOSITE_EXPANSION,
    COMPOSITE_HIGH_ACT,
    COMPOSITE_LOW_ACT,
    COMPOSITE_MIXED,
    COMPOSITE_TRENDING,
    DIR_HIGH,
    DIR_LOW,
    DIR_MID,
    PRIMARY_ER_WINDOW,
    PRIMARY_RANGE_WINDOW,
    PRIMARY_RV_WINDOW,
    Q_HIGH,
    Q_LOW,
    RESULTS,
    RNG_COMP,
    RNG_EXP,
    RNG_MID,
    THRESHOLD_YEARS,
    VLM_HIGH,
    VLM_LOW,
    VLM_MID,
    VOL_HIGH,
    VOL_LOW,
    VOL_MID,
)


FEATURE_KEYS = {
    "directionality": f"er_{PRIMARY_ER_WINDOW}",
    "volatility": f"rv_{PRIMARY_RV_WINDOW}",
    "volume": "rvol",
    "range": f"range_norm_{PRIMARY_RANGE_WINDOW}",
}


def _tercile_thresholds(x: np.ndarray) -> dict[str, float]:
    x = x[np.isfinite(x)]
    if len(x) == 0:
        return {"q33": float("nan"), "q67": float("nan"), "n": 0}
    return {
        "q33": float(np.quantile(x, Q_LOW)),
        "q67": float(np.quantile(x, Q_HIGH)),
        "n": int(len(x)),
    }


def freeze_thresholds(df: pd.DataFrame) -> dict:
    """Compute and freeze tercile cuts on census-eligible IS bars only."""
    is_mask = df["census_eligible"] & df["session_year"].isin(THRESHOLD_YEARS)
    sample = df.loc[is_mask]
    thr: dict = {
        "threshold_years": sorted(THRESHOLD_YEARS),
        "n_is_eligible": int(len(sample)),
        "features": {},
    }
    for name, col in FEATURE_KEYS.items():
        thr["features"][name] = {
            "column": col,
            **_tercile_thresholds(sample[col].to_numpy(np.float64)),
        }
    # Extra continuous diagnostics (not used for primary labels)
    for col in ("er_30", "er_120", "rv_30", "range_norm_30", f"atr_30"):
        if col in sample.columns:
            thr["features"][f"diag_{col}"] = {
                "column": col,
                **_tercile_thresholds(sample[col].to_numpy(np.float64)),
            }
    return thr


def _bucket(series: pd.Series, q33: float, q67: float, low: str, mid: str, high: str) -> pd.Series:
    out = np.full(len(series), None, dtype=object)
    v = series.to_numpy(np.float64)
    ok = np.isfinite(v)
    out[ok & (v <= q33)] = low
    out[ok & (v > q33) & (v <= q67)] = mid
    out[ok & (v > q67)] = high
    return pd.Series(out, index=series.index)


def classify(df: pd.DataFrame, thresholds: dict) -> pd.DataFrame:
    out = df.copy()
    f = thresholds["features"]

    out["directionality_state"] = _bucket(
        out[FEATURE_KEYS["directionality"]],
        f["directionality"]["q33"],
        f["directionality"]["q67"],
        DIR_LOW,
        DIR_MID,
        DIR_HIGH,
    )
    out["volatility_state"] = _bucket(
        out[FEATURE_KEYS["volatility"]],
        f["volatility"]["q33"],
        f["volatility"]["q67"],
        VOL_LOW,
        VOL_MID,
        VOL_HIGH,
    )
    out["volume_state"] = _bucket(
        out[FEATURE_KEYS["volume"]],
        f["volume"]["q33"],
        f["volume"]["q67"],
        VLM_LOW,
        VLM_MID,
        VLM_HIGH,
    )
    out["range_state"] = _bucket(
        out[FEATURE_KEYS["range"]],
        f["range"]["q33"],
        f["range"]["q67"],
        RNG_COMP,
        RNG_MID,
        RNG_EXP,
    )

    # Percentile ranks vs frozen IS distribution (descriptive only)
    for name, col in FEATURE_KEYS.items():
        ref = out.loc[
            out["census_eligible"] & out["session_year"].isin(THRESHOLD_YEARS), col
        ].to_numpy(np.float64)
        ref = ref[np.isfinite(ref)]
        if len(ref) == 0:
            out[f"{name}_pctile"] = np.nan
            continue
        ref_sorted = np.sort(ref)
        vals = out[col].to_numpy(np.float64)
        # searchsorted gives rank in frozen IS sample
        ranks = np.full(len(vals), np.nan)
        ok = np.isfinite(vals)
        ranks[ok] = np.searchsorted(ref_sorted, vals[ok], side="right") / len(ref_sorted)
        out[f"{name}_pctile"] = ranks

    # Composite descriptive flags (not mutually exclusive)
    out["flag_trending"] = out["directionality_state"] == DIR_HIGH
    out["flag_chop"] = out["directionality_state"] == DIR_LOW
    out["flag_high_activity"] = (out["volatility_state"] == VOL_HIGH) | (
        out["volume_state"] == VLM_HIGH
    )
    out["flag_low_activity"] = (out["volatility_state"] == VOL_LOW) & (
        out["volume_state"] == VLM_LOW
    )
    out["flag_compression"] = out["range_state"] == RNG_COMP
    out["flag_expansion"] = out["range_state"] == RNG_EXP

    # Mutually exclusive primary composite for Table 1
    # Priority frozen: TRENDING > CHOP > COMPRESSION > EXPANSION > HIGH_ACT > LOW_ACT > MIXED
    n = len(out)
    primary = np.full(n, COMPOSITE_MIXED, dtype=object)
    ft = out["flag_trending"].to_numpy()
    fc = out["flag_chop"].to_numpy()
    fcomp = out["flag_compression"].to_numpy()
    fexp = out["flag_expansion"].to_numpy()
    fha = out["flag_high_activity"].to_numpy()
    fla = out["flag_low_activity"].to_numpy()
    assigned = np.zeros(n, dtype=bool)
    for mask, label in (
        (ft, COMPOSITE_TRENDING),
        (fc, COMPOSITE_CHOP),
        (fcomp, COMPOSITE_COMPRESSION),
        (fexp, COMPOSITE_EXPANSION),
        (fha, COMPOSITE_HIGH_ACT),
        (fla, COMPOSITE_LOW_ACT),
    ):
        take = mask & ~assigned
        primary[take] = label
        assigned |= take
    out["composite_primary"] = primary

    # Multi-label composite string (independent flags joined)
    tags = []
    for flag, name in (
        ("flag_trending", COMPOSITE_TRENDING),
        ("flag_chop", COMPOSITE_CHOP),
        ("flag_high_activity", COMPOSITE_HIGH_ACT),
        ("flag_low_activity", COMPOSITE_LOW_ACT),
        ("flag_compression", COMPOSITE_COMPRESSION),
        ("flag_expansion", COMPOSITE_EXPANSION),
    ):
        tags.append(np.where(out[flag].to_numpy(), name, ""))
    joined = []
    for i in range(n):
        parts = [t[i] for t in tags if t[i]]
        joined.append("|".join(parts) if parts else COMPOSITE_MIXED)
    out["composite_multi"] = joined

    return out

def main() -> None:
    feat_path = RESULTS / "market_state_features.parquet"
    if not feat_path.exists():
        raise FileNotFoundError(f"Missing {feat_path}; run build_market_state_features.py first")
    df = pd.read_parquet(feat_path)
    print(f"Loaded features rows={len(df):,}")
    thr = freeze_thresholds(df)
    (RESULTS / "thresholds_frozen.json").write_text(
        json.dumps(thr, indent=2), encoding="utf-8"
    )
    print("Frozen thresholds written.")
    classified = classify(df, thr)
    # Drop raw OHLC to slim state panel (keep volume + features)
    drop = [c for c in ("open", "high", "low") if c in classified.columns]
    classified = classified.drop(columns=drop)
    out_path = RESULTS / "market_states.parquet"
    classified.to_parquet(out_path, index=False)
    print(f"Wrote {out_path} eligible={int(classified['census_eligible'].sum()):,}")


if __name__ == "__main__":
    main()
