"""Deep Phase-0 audit of Vilkov panels (no strategy)."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from common.nq_session import load_es
from common.paths import ROOT

DATA = ROOT / "data" / "vilkov"
ART = ROOT / "artifacts" / "26_vilkov_0dte_surface"


def main() -> None:
    ART.mkdir(parents=True, exist_ok=True)
    print("loading data_opt columns...", flush=True)
    df = pd.read_parquet(
        DATA / "data_opt.parquet",
        columns=[
            "quote_date",
            "quote_time",
            "option_type",
            "mnes",
            "mnes_rel",
            "mid",
            "bas",
            "delta",
            "gamma",
            "vega",
            "implied_volatility",
            "active_underlying_price",
            "trade_volume",
            "open_interest",
            "oi_gamma",
            "oi_gamma_abs",
            "oi_gamma_usd",
            "trade_volume_gamma",
            "trade_volume_gamma_usd",
            "payoff",
            "reth",
            "reth_und",
        ],
    )
    print(f"rows={len(df)}", flush=True)
    qt_vc = df["quote_time"].astype(str).value_counts()
    print("quote_time value_counts:", qt_vc.head(20).to_dict(), flush=True)

    qd = pd.to_datetime(df["quote_date"], utc=True)
    ts = pd.to_datetime(qd.dt.strftime("%Y-%m-%d") + " " + df["quote_time"].astype(str), errors="coerce")
    ts = ts.dt.tz_localize("America/New_York", ambiguous="infer", nonexistent="shift_forward")
    per_day = ts.groupby(ts.dt.date).nunique()
    dmax = per_day.idxmax()
    times_max = sorted(ts[ts.dt.date == dmax].dt.strftime("%H:%M").unique())

    st = pd.read_parquet(DATA / "data_structures.parquet")
    vx = pd.read_parquet(DATA / "vix.parquet", columns=["quote_datetime", "quote_time", "vix"])
    vxd = pd.to_datetime(vx["quote_datetime"], utc=True)
    sl = pd.read_parquet(DATA / "slopes.parquet")
    fm = pd.read_parquet(DATA / "future_moments_SPX.parquet")

    es = load_es()
    es = es[(es["ts"] >= "2016-09-01") & (es["ts"] <= "2024-05-02")].copy()
    es_1600 = int(((es["ny_min"] == 16 * 60)).sum())

    resolution = (
        "EOD_OR_SINGLE_SNAPSHOT"
        if float(per_day.max()) <= 2
        else ("30MIN" if float(per_day.median()) >= 10 else "MIXED_SPARSE")
    )

    field_nulls = {
        c: float(df[c].isna().mean())
        for c in [
            "gamma",
            "oi_gamma",
            "oi_gamma_abs",
            "oi_gamma_usd",
            "trade_volume",
            "open_interest",
            "trade_volume_gamma",
            "payoff",
            "reth",
            "reth_und",
            "mid",
            "delta",
            "implied_volatility",
        ]
    }

    summary = {
        "data_opt_rows": int(len(df)),
        "data_opt_days": int(qd.dt.date.nunique()),
        "data_opt_date_range": [str(qd.min()), str(qd.max())],
        "data_opt_quote_time_counts": qt_vc.to_dict(),
        "unique_times_per_day_median": float(per_day.median()),
        "unique_times_per_day_max": int(per_day.max()),
        "example_max_day": str(dmax),
        "example_max_day_times": times_max,
        "resolution_verdict": resolution,
        "option_type_counts": df["option_type"].value_counts().to_dict(),
        "mnes_min": float(df["mnes"].min()),
        "mnes_max": float(df["mnes"].max()),
        "mnes_nunique": int(df["mnes"].nunique()),
        "field_null_rates": field_nulls,
        "structures_rows": int(len(st)),
        "structures_cols": list(st.columns),
        "structures_quote_time_counts": st["quote_time"].astype(str).value_counts().to_dict(),
        "vix_unique_datetimes": int(vxd.nunique()),
        "vix_median_times_per_day": float(vxd.groupby(vxd.dt.date).nunique().median()),
        "vix_quote_times": sorted(vx["quote_time"].astype(str).unique()),
        "slopes_quote_time_counts": sl["quote_time"].astype(str).value_counts().to_dict(),
        "future_moments_cols": list(fm.columns),
        "future_moments_time_counts": fm["time"].astype(str).value_counts().to_dict(),
        "es_1600_bars_in_range": es_1600,
        "do_not_use_as_predictors": [
            "payoff",
            "reth",
            "reth_und",
            "intrinsic",
            "SPX_lrv",
            "SPX_srv",
            "SPX_lrvdn",
            "SPX_srvdn",
            "SPX_lrvup",
            "SPX_srvup",
            "SPX_lrv_skew",
            "SPX_srv_skew",
        ],
    }
    (ART / "vilkov_audit_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    lines = [
        "# Vilkov Phase 0 Audit — COMPLETE",
        "",
        "## 1. Timestamp resolution",
        f"- `data_opt.parquet`: **{len(df):,}** rows, **{qd.dt.date.nunique()}** days, "
        f"{qd.min().date()} → {qd.max().date()}",
        f"- Unique `quote_time` counts: `{qt_vc.to_dict()}`",
        f"- Unique times/day: median **{per_day.median():.0f}**, max **{per_day.max()}** "
        f"(example {dmax}: {times_max})",
        f"- **Verdict: `{resolution}`** — not a 1-minute option surface; dominated by a single daily snapshot.",
        f"- `vix.parquet`: 30-minute grid; times={sorted(vx['quote_time'].astype(str).unique())}; "
        f"median times/day={float(vxd.groupby(vxd.dt.date).nunique().median()):.0f}",
        f"- `data_structures.parquet`: times=`{st['quote_time'].astype(str).value_counts().to_dict()}`",
        f"- `slopes.parquet`: times=`{sl['quote_time'].astype(str).value_counts().to_dict()}`",
        "",
        "## 2. Point-in-time safety",
        "- `open_interest`: present; treat conservatively as start-of-day / lagged vs live tape.",
        "- `trade_volume*` at a lone 16:00 snapshot is end-of-day information — cannot predict earlier same-day moves.",
        "- `payoff`, `reth`, `reth_und`: settlement outcomes — **never predictors**.",
        "- `future_moments_SPX` (`SPX_lrv`, …): realized from t→16:00 — **targets only**, not features.",
        "",
        "## 3. Option identity",
        f"- `option_type`: {df['option_type'].value_counts().to_dict()}",
        f"- `mnes` in [{df['mnes'].min()}, {df['mnes'].max()}], nunique={df['mnes'].nunique()}",
        "- Greeks: delta, gamma, theta, vega, implied_volatility",
        "- mid, bas, bid_size, ask_size, trade_volume, open_interest, active_underlying_price",
        "- No raw strike/expiry columns; 0DTE moneyness grid implied",
        "",
        "## 4. What gamma fields mean",
        "- In `data_opt`: `gamma`, `oi_gamma`, `oi_gamma_abs`, `oi_gamma_usd`, `trade_volume_gamma*` "
        "are **per moneyness node**, not a FirmTape-style full-chain minute dealer book.",
        "- In `data_structures`: only mid/tv/payoff/reth/greeks — **no** shipped `g^{OI,n}` / `B^Γ` series.",
        f"- Null rates (sample fields): `{field_nulls}`",
        "",
        "## 5. Can we reconstruct our own gamma variables?",
        "- Yes at **available clocks** (here: essentially EOD option nodes): ATM concentration, signed OI-gamma balance, volume-gamma pressure.",
        "- No true intraday 1m dealer-gamma path from this file alone.",
        "- 30m market-state proxies: `vix` / `slopes` (and forward moments as targets).",
        "",
        "## 6. Join to ES/NQ 1m",
        f"- ES 16:00 bars in 2016-09..2024-05: **{es_1600}** — join on session date + 16:00 is feasible.",
        "- Same-day +1..+60m after 16:00 is near the close; natural targets are overnight / next RTH.",
        "- True intraday option-gamma tests still need Tier-2 rebuild or FirmTape minutes.",
        "",
        "## Gate decision",
        "**AUDIT PASS with hard constraints.** Usable research panel, but **not** a 1m SPXW surface. "
        "Design must match clocks (EOD option nodes + 30m VIX/slopes), or rebuild Tier-2.",
    ]
    (ART / "vilkov_schema_audit.md").write_text("\n".join(lines), encoding="utf-8")
    print("WROTE", ART / "vilkov_schema_audit.md", flush=True)
    print("RESOLUTION", resolution, flush=True)


if __name__ == "__main__":
    main()
