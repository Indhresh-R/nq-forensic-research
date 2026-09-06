"""
24A — Volatility-scaled position sizing under Strategy-12 HIGH.

Direction-agnostic: coin-flip side (frozen hash). Audit long/short books.
Stage gate: default --stage IS only (Val/OOS deferred until IS review).

Policies (same trade set):
  fixed | invvol | invvol_high_aware
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

_CODE = Path(__file__).resolve().parent
_ROOT = _CODE.parents[3]  # code -> 24A -> 24_HOW -> strategies -> root
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from common.nq_session import art, load_nq
from common.sessions import (
    SESSION_DECISION_OFFSETS,
    SESSION_ORDER,
    SESSION_START,
    bars_in_session,
    build_session_facts,
    decision_ny_min,
    state_at_T_session,
)

warnings.filterwarnings("ignore", category=FutureWarning)

# ---- Frozen constants (registered before performance look) ----
HOLD_HS = (30, 60)
PRIMARY_H = 30
VOL_LOOKBACK = 30
SIZE_CLIP = (0.25, 4.0)
S_HIGH = 0.70
S_NON = 1.00
COST_RT = 1.0  # mid scenario, points
HASH_SEED = 24
N_BOOT = 2000
BOOT_SEED = 2401
POLICIES = ("fixed", "invvol", "invvol_high_aware")
BOOKS = ("coinflip", "long", "short")

THRESH = json.loads(art("nq_multi_sess_opp_thresholds_IS.json").read_text(encoding="utf-8"))
STATE_TH = THRESH["state_terciles"]


def th_rng(session: str, off: int) -> dict[str, float] | None:
    d = STATE_TH.get(session, {}).get(str(off)) or STATE_TH.get(session, {}).get(off)
    if not d:
        return None
    return d.get("rng_psr")


def regime_of(session: str, off: int, rng_psr: float) -> str:
    t = th_rng(session, off)
    if not t:
        return "MID"
    if float(rng_psr) >= float(t["p66"]):
        return "HIGH"
    if float(rng_psr) <= float(t["p33"]):
        return "LOW"
    return "MID"


def after_bars(sess: pd.DataFrame, T_ny: int, session: str) -> pd.DataFrame:
    if session == "ASIA":
        ord_T = T_ny if T_ny >= SESSION_START else T_ny + 24 * 60
        ord_key = np.where(
            sess["ny_min"].to_numpy(np.int64) >= SESSION_START,
            sess["ny_min"].to_numpy(np.int64),
            sess["ny_min"].to_numpy(np.int64) + 24 * 60,
        )
        return sess.loc[ord_key > ord_T].reset_index(drop=True)
    return sess[sess["ny_min"] > T_ny].reset_index(drop=True)


def bars_through_T(sess: pd.DataFrame, T_ny: int, session: str) -> pd.DataFrame:
    if session == "ASIA":
        ord_T = T_ny if T_ny >= SESSION_START else T_ny + 24 * 60
        ord_key = np.where(
            sess["ny_min"].to_numpy(np.int64) >= SESSION_START,
            sess["ny_min"].to_numpy(np.int64),
            sess["ny_min"].to_numpy(np.int64) + 24 * 60,
        )
        return sess.loc[ord_key <= ord_T].reset_index(drop=True)
    return sess[sess["ny_min"] <= T_ny].reset_index(drop=True)


def realized_vol(closes: np.ndarray, w: int = VOL_LOOKBACK) -> float:
    if len(closes) < w + 1:
        return float("nan")
    r = np.diff(closes[-(w + 1) :].astype(float))
    if len(r) < w or not np.all(np.isfinite(r)):
        return float("nan")
    sd = float(np.std(r, ddof=1))
    return sd if sd > 1e-12 else float("nan")


def coin_side(session_date: Any, session: str, t_offset: int) -> int:
    key = f"{HASH_SEED}|{session_date}|{session}|{t_offset}".encode()
    h = hashlib.sha256(key).digest()
    return 1 if h[0] % 2 == 0 else -1


def size_for(policy: str, rv: float, rv_ref: float, regime: str) -> float:
    lo, hi = SIZE_CLIP
    if policy == "fixed":
        return 1.0
    inv = float(np.clip(rv_ref / rv, lo, hi))
    if policy == "invvol":
        return inv
    if policy == "invvol_high_aware":
        k = S_HIGH if regime == "HIGH" else S_NON
        return inv * k
    raise ValueError(policy)


def path_mae_mfe(entry: float, highs: np.ndarray, lows: np.ndarray, side: int) -> tuple[float, float]:
    """Signed-path MAE (adverse) and MFE (favorable) in points."""
    if side > 0:
        mfe = float(np.max(highs) - entry)
        mae = float(entry - np.min(lows))
    else:
        mfe = float(entry - np.min(lows))
        mae = float(np.max(highs) - entry)
    return mae, mfe


def build_panel() -> pd.DataFrame:
    print("Loading NQ + building 24A panel…", flush=True)
    df = load_nq()
    facts = build_session_facts(df)
    facts_map = {(r["session_date"], r["session"]): r for _, r in facts.iterrows()}

    sess_bars: dict[tuple, pd.DataFrame] = {}
    for sd, g in df.groupby("session_date", sort=False):
        for name in SESSION_ORDER:
            key = (sd, name)
            if key not in facts_map:
                continue
            b = bars_in_session(g, name)
            if len(b) >= 40:
                sess_bars[key] = b

    rows: list[dict[str, Any]] = []
    n_done = 0
    for (sd, name), bars in sess_bars.items():
        fr = facts_map[(sd, name)]
        psr = float(fr["psr"])
        if not np.isfinite(psr) or psr <= 0:
            continue
        session_open = float(fr["open"])
        year = int(fr["year"])
        split = str(fr["split"])

        for off in SESSION_DECISION_OFFSETS[name]:
            T = decision_ny_min(name, off)
            if T not in set(bars["ny_min"].astype(int).tolist()):
                continue
            st = state_at_T_session(
                bars, session=name, T_ny=T, session_open=session_open, psr=psr
            )
            if st is None:
                continue
            reg = regime_of(name, off, float(st["rng_psr"]))
            thru = bars_through_T(bars, T, name)
            rv = realized_vol(thru["close"].to_numpy(float), VOL_LOOKBACK)
            if not np.isfinite(rv):
                continue
            after = after_bars(bars, T, name)
            if len(after) < min(HOLD_HS):
                continue
            entry = float(after.iloc[0]["open"])
            if not np.isfinite(entry):
                continue
            side_cf = coin_side(sd, name, off)
            highs = after["high"].to_numpy(float)
            lows = after["low"].to_numpy(float)
            closes = after["close"].to_numpy(float)

            row: dict[str, Any] = {
                "session_date": str(sd),
                "session": name,
                "year": year,
                "split": split,
                "T_offset": int(off),
                "regime": reg,
                "is_high": int(reg == "HIGH"),
                "rng_psr": float(st["rng_psr"]),
                "rv": float(rv),
                "entry": entry,
                "side_coinflip": int(side_cf),
            }
            any_h = False
            for H in HOLD_HS:
                if len(closes) < H:
                    row[f"px_{H}"] = np.nan
                    row[f"raw_long_{H}"] = np.nan
                    row[f"raw_short_{H}"] = np.nan
                    row[f"raw_coinflip_{H}"] = np.nan
                    row[f"mae_long_{H}"] = np.nan
                    row[f"mfe_long_{H}"] = np.nan
                    row[f"mae_short_{H}"] = np.nan
                    row[f"mfe_short_{H}"] = np.nan
                    row[f"mae_coinflip_{H}"] = np.nan
                    row[f"mfe_coinflip_{H}"] = np.nan
                    continue
                px = float(closes[H - 1])
                dpx = px - entry
                row[f"px_{H}"] = px
                row[f"raw_long_{H}"] = dpx
                row[f"raw_short_{H}"] = -dpx
                row[f"raw_coinflip_{H}"] = side_cf * dpx
                mae_l, mfe_l = path_mae_mfe(entry, highs[:H], lows[:H], 1)
                mae_s, mfe_s = path_mae_mfe(entry, highs[:H], lows[:H], -1)
                mae_c, mfe_c = path_mae_mfe(entry, highs[:H], lows[:H], side_cf)
                row[f"mae_long_{H}"] = mae_l
                row[f"mfe_long_{H}"] = mfe_l
                row[f"mae_short_{H}"] = mae_s
                row[f"mfe_short_{H}"] = mfe_s
                row[f"mae_coinflip_{H}"] = mae_c
                row[f"mfe_coinflip_{H}"] = mfe_c
                any_h = True
            if any_h:
                rows.append(row)
        n_done += 1
        if n_done % 2000 == 0:
            print(f"  … {n_done} session blocks, {len(rows)} rows", flush=True)

    panel = pd.DataFrame(rows)
    print(f"Panel rows: {len(panel):,}", flush=True)
    return panel


def freeze_rv_ref(panel: pd.DataFrame) -> float:
    is_rv = panel.loc[panel["split"] == "IS", "rv"].to_numpy(float)
    is_rv = is_rv[np.isfinite(is_rv)]
    if len(is_rv) == 0:
        raise RuntimeError("No IS rv to freeze rv_ref")
    return float(np.median(is_rv))


def select_risk_trades(panel: pd.DataFrame) -> pd.DataFrame:
    """One trade per session_date × session: earliest eligible T_offset."""
    p = panel.sort_values(["session_date", "session", "T_offset"])
    return p.groupby(["session_date", "session"], as_index=False, sort=False).head(1)


def apply_sizes(trades: pd.DataFrame, rv_ref: float) -> pd.DataFrame:
    out = trades.copy()
    for policy in POLICIES:
        sizes = [
            size_for(policy, float(r.rv), rv_ref, str(r.regime))
            for r in out.itertuples(index=False)
        ]
        out[f"size_{policy}"] = sizes
        for H in HOLD_HS:
            for book in BOOKS:
                raw = out[f"raw_{book}_{H}"].to_numpy(float)
                sz = out[f"size_{policy}"].to_numpy(float)
                # Cost scales with |size|
                out[f"pnl_{policy}_{book}_{H}"] = sz * raw - COST_RT * np.abs(sz)
    return out


def daily_pnl(trades: pd.DataFrame, col: str) -> pd.Series:
    sub = trades[["session_date", col]].dropna()
    if sub.empty:
        return pd.Series(dtype=float)
    return sub.groupby("session_date", sort=True)[col].sum()


def risk_stats(daily: pd.Series) -> dict[str, float]:
    x = daily.to_numpy(float)
    x = x[np.isfinite(x)]
    n = len(x)
    if n < 5:
        return {
            "n_days": int(n),
            "mean": float("nan"),
            "std": float("nan"),
            "sharpe": float("nan"),
            "sortino": float("nan"),
            "max_dd": float("nan"),
            "total": float("nan"),
        }
    mu = float(np.mean(x))
    sd = float(np.std(x, ddof=1))
    downside = x[x < 0]
    dsd = float(np.std(downside, ddof=1)) if len(downside) >= 2 else float("nan")
    sharpe = mu / sd * np.sqrt(252) if sd > 1e-12 else float("nan")
    sortino = mu / dsd * np.sqrt(252) if np.isfinite(dsd) and dsd > 1e-12 else float("nan")
    equity = np.cumsum(x)
    peak = np.maximum.accumulate(equity)
    dd = equity - peak
    return {
        "n_days": int(n),
        "mean": mu,
        "std": sd,
        "sharpe": float(sharpe),
        "sortino": float(sortino),
        "max_dd": float(np.min(dd)),
        "total": float(np.sum(x)),
    }


def bootstrap_delta(
    daily_a: pd.Series,
    daily_b: pd.Series,
    metric: str,
    n_boot: int = N_BOOT,
    seed: int = BOOT_SEED,
) -> dict[str, float]:
    """Bootstrap CI for metric(A) - metric(B) on aligned calendar days (inner join)."""
    joined = pd.concat([daily_a.rename("a"), daily_b.rename("b")], axis=1, join="inner").dropna()
    if len(joined) < 20:
        return {"delta": float("nan"), "lo": float("nan"), "hi": float("nan"), "n": len(joined)}
    a = joined["a"].to_numpy(float)
    b = joined["b"].to_numpy(float)
    rng = np.random.default_rng(seed)
    deltas = np.empty(n_boot, dtype=float)
    n = len(a)
    for i in range(n_boot):
        idx = rng.integers(0, n, size=n)
        sa = pd.Series(a[idx])
        sb = pd.Series(b[idx])
        ra = risk_stats(sa)
        rb = risk_stats(sb)
        deltas[i] = ra[metric] - rb[metric]
    deltas = deltas[np.isfinite(deltas)]
    if len(deltas) == 0:
        return {"delta": float("nan"), "lo": float("nan"), "hi": float("nan"), "n": n}
    point_a = risk_stats(pd.Series(a))
    point_b = risk_stats(pd.Series(b))
    return {
        "delta": float(point_a[metric] - point_b[metric]),
        "lo": float(np.percentile(deltas, 5)),
        "hi": float(np.percentile(deltas, 95)),
        "n": int(n),
    }


def score_split(
    trades: pd.DataFrame,
    split: str,
    H: int = PRIMARY_H,
) -> list[dict[str, Any]]:
    sub = trades[trades["split"] == split]
    rows: list[dict[str, Any]] = []
    for book in BOOKS:
        fixed_col = f"pnl_fixed_{book}_{H}"
        d_fixed = daily_pnl(sub, fixed_col)
        st_fixed = risk_stats(d_fixed)
        for policy in POLICIES:
            col = f"pnl_{policy}_{book}_{H}"
            d = daily_pnl(sub, col)
            st = risk_stats(d)
            row: dict[str, Any] = {
                "split": split,
                "horizon": H,
                "book": book,
                "policy": policy,
                **{f"risk_{k}": v for k, v in st.items()},
                "n_trades": int(sub[col].notna().sum()),
                "n_high": int(sub.loc[sub[col].notna(), "is_high"].sum()),
                "mean_size": float(np.mean(np.abs(sub[f"size_{policy}"].to_numpy(float)))),
            }
            if policy != "fixed":
                for metric in ("sharpe", "sortino"):
                    boot = bootstrap_delta(d, d_fixed, metric)
                    row[f"d_{metric}_vs_fixed"] = boot["delta"]
                    row[f"d_{metric}_lo"] = boot["lo"]
                    row[f"d_{metric}_hi"] = boot["hi"]
            else:
                row["d_sharpe_vs_fixed"] = 0.0
                row["d_sharpe_lo"] = 0.0
                row["d_sharpe_hi"] = 0.0
                row["d_sortino_vs_fixed"] = 0.0
                row["d_sortino_lo"] = 0.0
                row["d_sortino_hi"] = 0.0
            rows.append(row)
    return rows


def score_by_session(
    trades: pd.DataFrame,
    split: str,
    H: int = PRIMARY_H,
    book: str = "coinflip",
) -> list[dict[str, Any]]:
    sub = trades[trades["split"] == split]
    rows: list[dict[str, Any]] = []
    for sess in SESSION_ORDER:
        s = sub[sub["session"] == sess]
        if s.empty:
            continue
        d_fixed = daily_pnl(s, f"pnl_fixed_{book}_{H}")
        for policy in POLICIES:
            d = daily_pnl(s, f"pnl_{policy}_{book}_{H}")
            st = risk_stats(d)
            row: dict[str, Any] = {
                "split": split,
                "session": sess,
                "horizon": H,
                "book": book,
                "policy": policy,
                **{f"risk_{k}": v for k, v in st.items()},
                "n_trades": int(s[f"pnl_{policy}_{book}_{H}"].notna().sum()),
            }
            if policy != "fixed":
                boot = bootstrap_delta(d, d_fixed, "sharpe")
                row["d_sharpe_vs_fixed"] = boot["delta"]
                row["d_sharpe_lo"] = boot["lo"]
                row["d_sharpe_hi"] = boot["hi"]
            rows.append(row)
    return rows


def mae_mfe_by_regime(panel_all_clocks: pd.DataFrame, split: str, H: int = PRIMARY_H) -> pd.DataFrame:
    """Distributional MAE/MFE on all clocks (diagnostic; not for Sharpe)."""
    sub = panel_all_clocks[panel_all_clocks["split"] == split]
    rows = []
    for regime_label, mask in (
        ("HIGH", sub["is_high"] == 1),
        ("nonHIGH", sub["is_high"] == 0),
        ("ALL", pd.Series(True, index=sub.index)),
    ):
        s = sub.loc[mask]
        for book in ("coinflip",):
            mae = s[f"mae_{book}_{H}"].to_numpy(float)
            mfe = s[f"mfe_{book}_{H}"].to_numpy(float)
            mae = mae[np.isfinite(mae)]
            mfe = mfe[np.isfinite(mfe)]
            rows.append(
                {
                    "split": split,
                    "regime": regime_label,
                    "horizon": H,
                    "book": book,
                    "n": int(len(mae)),
                    "mae_mean": float(np.mean(mae)) if len(mae) else np.nan,
                    "mae_p50": float(np.median(mae)) if len(mae) else np.nan,
                    "mae_p90": float(np.percentile(mae, 90)) if len(mae) else np.nan,
                    "mfe_mean": float(np.mean(mfe)) if len(mfe) else np.nan,
                    "mfe_p50": float(np.median(mfe)) if len(mfe) else np.nan,
                    "mfe_p90": float(np.percentile(mfe, 90)) if len(mfe) else np.nan,
                }
            )
    return pd.DataFrame(rows)


def fmt(x: Any, nd: int = 2) -> str:
    if isinstance(x, (int, float)) and np.isfinite(x):
        return f"{x:.{nd}f}"
    return "—"


def write_stage_report(
    res: pd.DataFrame,
    sess_res: pd.DataFrame,
    mae_df: pd.DataFrame,
    meta: dict[str, Any],
    stage: str,
    is_tag: str,
    H: int = PRIMARY_H,
) -> tuple[str, str]:
    """Write IS / Validation / OOS report. Returns (markdown, stage_tag)."""
    split_name = {"IS": "IS", "VAL": "Validation", "OOS": "OOS"}[stage]
    cf = res[(res["book"] == "coinflip") & (res["horizon"] == H) & (res["split"] == split_name)]
    long_b = res[(res["book"] == "long") & (res["horizon"] == H) & (res["split"] == split_name)]
    short_b = res[(res["book"] == "short") & (res["horizon"] == H) & (res["split"] == split_name)]

    lines: list[str] = []
    if stage == "IS":
        lines.append("# Hypothesis 24A — Vol-Scaled Sizing (IS only)")
        lines.append("")
        lines.append("## Stage gate")
        lines.append("")
        lines.append("**Val / OOS not scored in this artifact.** (Unlock separately.)")
    elif stage == "VAL":
        lines.append("# Hypothesis 24A — Validation (documentation; freeze unchanged)")
        lines.append("")
        lines.append(
            f"IS provisional tag was `{is_tag}`. Val scored once with **zero** parameter adjustment."
        )
    else:
        lines.append("# Hypothesis 24A — OOS (documentation triple; not a rescue)")
        lines.append("")
        lines.append(
            f"IS tag `{is_tag}`. OOS recorded for IS/Val/OOS parity — **not** to promote a sizing claim."
        )
    lines.append("")
    lines.append("## Freeze")
    lines.append("")
    lines.append("| Item | Value |")
    lines.append("|------|-------|")
    lines.append(f"| Vol lookback W | {meta['vol_lookback']} |")
    lines.append(f"| rv_ref (IS median) | {meta['rv_ref']:.6f} |")
    lines.append(f"| Size clips | {meta['size_clip']} |")
    lines.append(f"| HIGH multiplier | {meta['s_high']} (non-HIGH {meta['s_non']}) |")
    lines.append(f"| Cost RT | {meta['cost_rt']} pt x |size| |")
    n_key = {"IS": "n_risk_is", "VAL": "n_risk_val", "OOS": "n_risk_oos"}[stage]
    lines.append(f"| Risk-trade rows ({split_name}) | {meta.get(n_key, 0):,} |")
    if stage == "IS":
        lines.append(f"| Panel rows (all clocks) | {meta['n_panel']:,} |")
        lines.append(f"| HIGH share (risk IS) | {meta['high_share_is']:.1%} |")
    lines.append("")
    lines.append("## Direction audit")
    lines.append("")
    lines.append(
        "Primary book = **coin-flip**. Long/short audit under identical sizing."
    )
    lines.append("")

    def table_for(block: pd.DataFrame, title: str) -> None:
        lines.append(f"## {title} — H={H}")
        lines.append("")
        lines.append(
            "| Policy | n_tr | n_days | Sharpe | Sortino | MaxDD | "
            "dSharpe vs fixed [90% CI] | dSortino vs fixed [90% CI] | mean|size| |"
        )
        lines.append(
            "|--------|------|--------|--------|---------|-------|"
            "---------------------------|----------------------------|-----------|"
        )
        for policy in POLICIES:
            r = block[block["policy"] == policy]
            if r.empty:
                continue
            r = r.iloc[0]
            dsh = (
                f"{fmt(r['d_sharpe_vs_fixed'], 3)} [{fmt(r['d_sharpe_lo'], 3)}, {fmt(r['d_sharpe_hi'], 3)}]"
                if policy != "fixed"
                else "0"
            )
            dso = (
                f"{fmt(r['d_sortino_vs_fixed'], 3)} [{fmt(r['d_sortino_lo'], 3)}, {fmt(r['d_sortino_hi'], 3)}]"
                if policy != "fixed"
                else "0"
            )
            lines.append(
                f"| `{policy}` | {int(r['n_trades'])} | {int(r['risk_n_days'])} | "
                f"{fmt(r['risk_sharpe'], 3)} | {fmt(r['risk_sortino'], 3)} | {fmt(r['risk_max_dd'], 1)} | "
                f"{dsh} | {dso} | {fmt(r['mean_size'], 3)} |"
            )
        lines.append("")

    table_for(cf, "Primary book (coin-flip)")
    table_for(long_b, "Audit book (always long)")
    table_for(short_b, "Audit book (always short)")

    if stage == "IS":
        lines.append("## Multi-session (coin-flip, H=30) — Sharpe vs fixed")
        lines.append("")
        lines.append("| Session | Policy | Sharpe | dSharpe vs fixed [90% CI] | n_tr |")
        lines.append("|---------|--------|--------|---------------------------|------|")
        ss = sess_res[(sess_res["split"] == "IS") & (sess_res["horizon"] == H)]
        for sess in SESSION_ORDER:
            for policy in POLICIES:
                r = ss[(ss["session"] == sess) & (ss["policy"] == policy)]
                if r.empty:
                    continue
                r = r.iloc[0]
                if policy == "fixed":
                    dsh = "0"
                else:
                    dsh = (
                        f"{fmt(r.get('d_sharpe_vs_fixed'), 3)} "
                        f"[{fmt(r.get('d_sharpe_lo'), 3)}, {fmt(r.get('d_sharpe_hi'), 3)}]"
                    )
                lines.append(
                    f"| {sess} | `{policy}` | {fmt(r['risk_sharpe'], 3)} | {dsh} | {int(r['n_trades'])} |"
                )
        lines.append("")
        lines.append("## Multi-horizon coin-flip (pooled sessions)")
        lines.append("")
        lines.append("| H | Policy | Sharpe | Sortino | MaxDD | dSharpe vs fixed |")
        lines.append("|---|--------|--------|---------|-------|------------------|")
        for H2 in HOLD_HS:
            block = res[(res["book"] == "coinflip") & (res["horizon"] == H2) & (res["split"] == "IS")]
            for policy in POLICIES:
                r = block[block["policy"] == policy]
                if r.empty:
                    continue
                r = r.iloc[0]
                dsh = fmt(r["d_sharpe_vs_fixed"], 3) if policy != "fixed" else "0"
                lines.append(
                    f"| {H2} | `{policy}` | {fmt(r['risk_sharpe'], 3)} | {fmt(r['risk_sortino'], 3)} | "
                    f"{fmt(r['risk_max_dd'], 1)} | {dsh} |"
                )
        lines.append("")
        lines.append("## MAE / MFE by regime (all clocks, coin-flip side, diagnostic)")
        lines.append("")
        lines.append("| Regime | n | MAE mean | MAE p50 | MAE p90 | MFE mean | MFE p50 | MFE p90 |")
        lines.append("|--------|---|----------|---------|---------|----------|---------|---------|")
        for _, r in mae_df[mae_df["split"] == "IS"].iterrows():
            lines.append(
                f"| {r['regime']} | {int(r['n'])} | {fmt(r['mae_mean'], 2)} | {fmt(r['mae_p50'], 2)} | "
                f"{fmt(r['mae_p90'], 2)} | {fmt(r['mfe_mean'], 2)} | {fmt(r['mfe_p50'], 2)} | "
                f"{fmt(r['mfe_p90'], 2)} |"
            )
        lines.append("")

    # Stage tag from coin-flip deltas
    tag = f"{stage}_NULL"
    detail: list[str] = []
    inv = cf[cf["policy"] == "invvol"]
    haw = cf[cf["policy"] == "invvol_high_aware"]
    if not inv.empty and not haw.empty:
        inv_r, haw_r = inv.iloc[0], haw.iloc[0]
        both_worse = (
            np.isfinite(inv_r["d_sharpe_hi"])
            and inv_r["d_sharpe_hi"] < 0
            and np.isfinite(haw_r["d_sharpe_hi"])
            and haw_r["d_sharpe_hi"] < 0
        )
        if both_worse:
            tag = f"{stage}_CONFIRMS_NULL" if stage != "IS" else "IS_NULL"
            detail.append(
                "Bootstrap 90% CI for dSharpe vs fixed entirely below 0 for both sizing policies."
            )
        elif inv_r["d_sharpe_vs_fixed"] > 0 or haw_r["d_sharpe_vs_fixed"] > 0:
            tag = f"{stage}_PARTIAL_OR_FLIP"
            detail.append("Point dSharpe > 0 on at least one policy — inspect CI / audit books.")
        else:
            tag = f"{stage}_NULL"
            detail.append("No Sharpe lift vs fixed.")

    lines.append(f"## {split_name} tag")
    lines.append("")
    lines.append(f"**`{tag}`**")
    lines.append("")
    for d in detail:
        lines.append(f"- {d}")
    lines.append("")
    if stage == "IS":
        lines.append("## Hostile IS reading")
        lines.append("")
        lines.append(
            "Zero-edge coin-flip + proportional costs: inv-vol upsizes quiet clocks and "
            "increases cost drag. Mechanical null — does **not** kill 24D (different mechanism)."
        )
        lines.append("")
    elif stage == "VAL":
        lines.append("## Reading")
        lines.append("")
        lines.append(
            "Documentation Val after IS_NULL. Expect same mechanical cost-drag pattern. "
            "Not a promote path. OOS optional for triple parity."
        )
        lines.append("")
    else:
        lines.append("## Reading")
        lines.append("")
        lines.append(
            "Documentation OOS. Sizing claim remains null. 24D is a separate ticket."
        )
        lines.append("")
    lines.append("## Stop")
    lines.append("")
    if stage == "IS":
        lines.append("- Val / OOS unlocked only after review.")
    elif stage == "VAL":
        lines.append("- No refit. OOS documentation may follow.")
    else:
        lines.append("- Triple complete for 24A. No sizing promote.")
    lines.append("")
    return "\n".join(lines), tag


def write_is_report(
    res: pd.DataFrame,
    sess_res: pd.DataFrame,
    mae_df: pd.DataFrame,
    meta: dict[str, Any],
    H: int = PRIMARY_H,
) -> tuple[str, str]:
    return write_stage_report(res, sess_res, mae_df, meta, "IS", "IS_NULL", H=H)


def main() -> None:
    ap = argparse.ArgumentParser(description="24A vol-scaled sizing test")
    ap.add_argument("--stage", choices=("IS", "VAL", "OOS", "ALL"), default="IS")
    ap.add_argument("--rebuild", action="store_true", help="Rebuild panel even if parquet exists")
    args = ap.parse_args()

    stages = ["IS", "VAL", "OOS"] if args.stage == "ALL" else [args.stage]
    # Map CLI stage names to split labels in panel
    split_of_stage = {"IS": "IS", "VAL": "Validation", "OOS": "OOS"}

    panel_path = art("nq_how_24a_panel.parquet")
    if panel_path.exists() and not args.rebuild:
        print(f"Loading panel {panel_path}", flush=True)
        panel = pd.read_parquet(panel_path)
    else:
        panel = build_panel()
        panel.to_parquet(panel_path, index=False)
        print(f"Wrote {panel_path}", flush=True)

    # Always freeze rv_ref from IS only
    if art("nq_how_24a_thresholds_IS.json").exists() and not args.rebuild:
        freeze = json.loads(art("nq_how_24a_thresholds_IS.json").read_text(encoding="utf-8"))
        rv_ref = float(freeze["rv_ref"])
        print(f"Loaded frozen rv_ref={rv_ref:.6f}", flush=True)
    else:
        rv_ref = freeze_rv_ref(panel)
        freeze = {
            "vol_lookback": VOL_LOOKBACK,
            "rv_ref": rv_ref,
            "size_clip": list(SIZE_CLIP),
            "s_high": S_HIGH,
            "s_non": S_NON,
            "cost_rt": COST_RT,
            "hash_seed": HASH_SEED,
            "hold_hs": list(HOLD_HS),
            "primary_h": PRIMARY_H,
            "policies": list(POLICIES),
            "note": "rv_ref = IS median of causal return-std; frozen before Val/OOS",
        }
        art("nq_how_24a_thresholds_IS.json").write_text(
            json.dumps(freeze, indent=2), encoding="utf-8"
        )
        print(f"Frozen rv_ref={rv_ref:.6f}", flush=True)

    risk_trades = select_risk_trades(panel)
    risk_trades = apply_sizes(risk_trades, rv_ref)
    risk_trades.to_parquet(art("nq_how_24a_risk_trades.parquet"), index=False)

    # Score all requested splits into one results table (append across stages run)
    score_rows: list[dict[str, Any]] = []
    sess_rows: list[dict[str, Any]] = []
    for st in stages:
        split = split_of_stage[st]
        for H in HOLD_HS:
            score_rows.extend(score_split(risk_trades, split, H=H))
        sess_rows.extend(score_by_session(risk_trades, split, H=PRIMARY_H, book="coinflip"))

    res_df = pd.DataFrame(score_rows)
    # Merge with prior stage CSVs if running a single later stage
    res_path = art("nq_how_24a_results.csv")
    if res_path.exists() and args.stage in ("VAL", "OOS"):
        prior = pd.read_csv(res_path)
        keep = prior[~prior["split"].isin([split_of_stage[s] for s in stages])]
        res_df = pd.concat([keep, res_df], ignore_index=True)
    res_df.to_csv(res_path, index=False)

    sess_df = pd.DataFrame(sess_rows)
    sess_path = art("nq_how_24a_results_by_session.csv")
    if sess_path.exists() and args.stage in ("VAL", "OOS"):
        prior_s = pd.read_csv(sess_path)
        keep_s = prior_s[~prior_s["split"].isin([split_of_stage[s] for s in stages])]
        sess_df = pd.concat([keep_s, sess_df], ignore_index=True)
    sess_df.to_csv(sess_path, index=False)

    is_tag = "IS_NULL"
    is_json = art("nq_how_24a_report_IS.json")
    if is_json.exists():
        try:
            is_tag = str(json.loads(is_json.read_text(encoding="utf-8")).get("is_tag", is_tag))
        except Exception:
            pass

    dossier = _CODE.parents[0] / "results"
    dossier.mkdir(parents=True, exist_ok=True)

    for st in stages:
        split = split_of_stage[st]
        mae_df = mae_mfe_by_regime(panel, split, H=PRIMARY_H)
        if st == "IS":
            mae_df.to_csv(art("nq_how_24a_mae_mfe_IS.csv"), index=False)
        elif st == "VAL":
            mae_df.to_csv(art("nq_how_24a_mae_mfe_VAL.csv"), index=False)
        else:
            mae_df.to_csv(art("nq_how_24a_mae_mfe_OOS.csv"), index=False)

        sub = risk_trades[risk_trades["split"] == split]
        meta = {
            **freeze,
            "n_panel": int(len(panel)),
            "n_risk_is": int(len(risk_trades[risk_trades["split"] == "IS"])),
            "n_risk_val": int(len(risk_trades[risk_trades["split"] == "Validation"])),
            "n_risk_oos": int(len(risk_trades[risk_trades["split"] == "OOS"])),
            "high_share_is": float(
                risk_trades.loc[risk_trades["split"] == "IS", "is_high"].mean()
            ),
        }
        report_md, tag = write_stage_report(
            res_df, sess_df, mae_df, meta, st, is_tag, H=PRIMARY_H
        )
        art_name = {"IS": "nq_how_24a_report_IS", "VAL": "nq_how_24a_report_VAL", "OOS": "nq_how_24a_report_OOS"}[st]
        art(f"{art_name}.md").write_text(report_md, encoding="utf-8")
        payload = {
            "stage": st,
            "tag": tag,
            "is_tag": is_tag,
            "freeze_unchanged": True,
            "freeze": freeze,
            "meta": meta,
            "results_primary_H": res_df[
                (res_df["split"] == split) & (res_df["horizon"] == PRIMARY_H)
            ].to_dict(orient="records"),
        }
        art(f"{art_name}.json").write_text(
            json.dumps(payload, indent=2, default=str), encoding="utf-8"
        )
        dossier_name = {"IS": "IS.md", "VAL": "validation.md", "OOS": "OOS.md"}[st]
        (dossier / dossier_name).write_text(report_md, encoding="utf-8")
        print(f"{st} tag: {tag}", flush=True)
        print(f"Report: {art(f'{art_name}.md')}", flush=True)


if __name__ == "__main__":
    main()
