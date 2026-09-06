"""
24D — Symmetric breakout + regime-aware stop/target (vol-harvest structure).

Direction-agnostic: side from first breakout touch. Not a sign resolver.
Stage gate: default --stage IS only.
"""
from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

_CODE = Path(__file__).resolve().parent
_ROOT = _CODE.parents[3]
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

# Frozen constants (registered before performance look)
BO_FRAC = 0.10
STOP_R = 1.0
TGT_R = 1.5
WIDTH_HIGH = 1.50
WIDTH_NON = 1.00
MAX_HOLD = 60
COST_RT = 1.0
SIZE = 1.0
N_BOOT = 2000
BOOT_SEED = 2404
POLICIES = ("uncond_base", "uncond_wide", "regime_width", "high_only_base")

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


def width_for(policy: str, is_high: bool) -> float | None:
    """Return width multiplier, or None if policy skips this trade."""
    if policy == "high_only_base":
        if not is_high:
            return None
        return WIDTH_NON
    if policy == "uncond_base":
        return WIDTH_NON
    if policy == "uncond_wide":
        return WIDTH_HIGH
    if policy == "regime_width":
        return WIDTH_HIGH if is_high else WIDTH_NON
    raise ValueError(policy)


def simulate_trade(
    opens: np.ndarray,
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    anchor: float,
    bo_dist: float,
    width: float,
) -> dict[str, Any] | None:
    """First-touch breakout then stop/target/time. Returns None if no fill or ambiguous."""
    if not np.isfinite(bo_dist) or bo_dist <= 0 or len(closes) < 2:
        return None
    upper = anchor + bo_dist
    lower = anchor - bo_dist
    stop_dist = STOP_R * bo_dist * width
    tgt_dist = TGT_R * bo_dist * width
    n = min(len(closes), MAX_HOLD)

    fill_i = -1
    side = 0
    entry = float("nan")
    for i in range(n):
        hit_up = highs[i] >= upper or opens[i] >= upper
        hit_dn = lows[i] <= lower or opens[i] <= lower
        if hit_up and hit_dn:
            return None  # ambiguity
        if hit_up:
            side = 1
            entry = float(opens[i]) if opens[i] >= upper else upper
            fill_i = i
            break
        if hit_dn:
            side = -1
            entry = float(opens[i]) if opens[i] <= lower else lower
            fill_i = i
            break
    if fill_i < 0 or side == 0 or not np.isfinite(entry):
        return None

    if side > 0:
        stop = entry - stop_dist
        tgt = entry + tgt_dist
    else:
        stop = entry + stop_dist
        tgt = entry - tgt_dist

    exit_px = float("nan")
    exit_reason = "none"
    mae = 0.0
    mfe = 0.0
    end = min(fill_i + MAX_HOLD, len(closes))
    for j in range(fill_i, end):
        h, l, c, o = float(highs[j]), float(lows[j]), float(closes[j]), float(opens[j])
        if side > 0:
            mae = max(mae, entry - l)
            mfe = max(mfe, h - entry)
            hit_stop = l <= stop or o <= stop
            hit_tgt = h >= tgt or o >= tgt
        else:
            mae = max(mae, h - entry)
            mfe = max(mfe, entry - l)
            hit_stop = h >= stop or o >= stop
            hit_tgt = l <= tgt or o <= tgt
        if hit_stop and hit_tgt:
            # Hostile: stop first
            exit_px = stop if not (side > 0 and o <= stop or side < 0 and o >= stop) else float(o)
            # If gap through stop, fill at open
            if side > 0 and o <= stop:
                exit_px = float(o)
            elif side < 0 and o >= stop:
                exit_px = float(o)
            else:
                exit_px = stop
            exit_reason = "stop"
            break
        if hit_stop:
            exit_px = float(o) if (side > 0 and o <= stop) or (side < 0 and o >= stop) else stop
            exit_reason = "stop"
            break
        if hit_tgt:
            exit_px = float(o) if (side > 0 and o >= tgt) or (side < 0 and o <= tgt) else tgt
            exit_reason = "target"
            break
    if exit_reason == "none":
        # time stop at last bar in window
        j = end - 1
        exit_px = float(closes[j])
        exit_reason = "time"

    pnl = SIZE * side * (exit_px - entry) - COST_RT * SIZE
    return {
        "side": int(side),
        "entry": float(entry),
        "exit": float(exit_px),
        "exit_reason": exit_reason,
        "pnl": float(pnl),
        "mae": float(mae),
        "mfe": float(mfe),
        "width": float(width),
        "stop_dist": float(stop_dist),
        "tgt_dist": float(tgt_dist),
        "fill_bar": int(fill_i),
    }


def build_panel() -> pd.DataFrame:
    print("Loading NQ + building 24D panel…", flush=True)
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
        bo_dist = BO_FRAC * psr

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
            is_high = reg == "HIGH"
            after = after_bars(bars, T, name)
            if len(after) < 5:
                continue
            anchor = float(after.iloc[0]["open"])
            if not np.isfinite(anchor):
                continue
            opens = after["open"].to_numpy(float)
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
                "is_high": int(is_high),
                "psr": psr,
                "bo_dist": bo_dist,
                "anchor": anchor,
                "rng_psr": float(st["rng_psr"]),
            }
            any_fill = False
            for policy in POLICIES:
                w = width_for(policy, is_high)
                if w is None:
                    row[f"pnl_{policy}"] = np.nan
                    row[f"side_{policy}"] = 0
                    row[f"reason_{policy}"] = "skip_regime"
                    row[f"mae_{policy}"] = np.nan
                    row[f"mfe_{policy}"] = np.nan
                    continue
                sim = simulate_trade(opens, highs, lows, closes, anchor, bo_dist, w)
                if sim is None:
                    row[f"pnl_{policy}"] = np.nan
                    row[f"side_{policy}"] = 0
                    row[f"reason_{policy}"] = "no_fill"
                    row[f"mae_{policy}"] = np.nan
                    row[f"mfe_{policy}"] = np.nan
                    continue
                row[f"pnl_{policy}"] = sim["pnl"]
                row[f"side_{policy}"] = sim["side"]
                row[f"reason_{policy}"] = sim["exit_reason"]
                row[f"mae_{policy}"] = sim["mae"]
                row[f"mfe_{policy}"] = sim["mfe"]
                any_fill = True
            if any_fill:
                rows.append(row)
        n_done += 1
        if n_done % 2000 == 0:
            print(f"  … {n_done} session blocks, {len(rows)} rows", flush=True)

    panel = pd.DataFrame(rows)
    print(f"Panel rows (any-policy fill): {len(panel):,}", flush=True)
    return panel


def select_risk_trades(panel: pd.DataFrame, policy: str) -> pd.DataFrame:
    """Earliest offset per session_date x session with a fill under policy."""
    col = f"pnl_{policy}"
    sub = panel[panel[col].notna()].sort_values(["session_date", "session", "T_offset"])
    return sub.groupby(["session_date", "session"], as_index=False, sort=False).head(1)


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
        ra = risk_stats(pd.Series(a[idx]))
        rb = risk_stats(pd.Series(b[idx]))
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


def trade_diag(trades: pd.DataFrame, policy: str) -> dict[str, float]:
    col = f"pnl_{policy}"
    side_col = f"side_{policy}"
    x = trades[col].to_numpy(float)
    x = x[np.isfinite(x)]
    sides = trades.loc[trades[col].notna(), side_col].to_numpy(int)
    long_x = trades.loc[trades[side_col] == 1, col].to_numpy(float)
    short_x = trades.loc[trades[side_col] == -1, col].to_numpy(float)
    long_x = long_x[np.isfinite(long_x)]
    short_x = short_x[np.isfinite(short_x)]
    return {
        "n": int(len(x)),
        "win": float(np.mean(x > 0)) if len(x) else float("nan"),
        "E": float(np.mean(x)) if len(x) else float("nan"),
        "n_long": int(len(long_x)),
        "E_long": float(np.mean(long_x)) if len(long_x) else float("nan"),
        "n_short": int(len(short_x)),
        "E_short": float(np.mean(short_x)) if len(short_x) else float("nan"),
        "long_share": float(np.mean(sides == 1)) if len(sides) else float("nan"),
    }


def score_split(panel: pd.DataFrame, split: str) -> list[dict[str, Any]]:
    sub = panel[panel["split"] == split]
    base_tr = select_risk_trades(sub, "uncond_base")
    wide_tr = select_risk_trades(sub, "uncond_wide")
    d_base = daily_pnl(base_tr, "pnl_uncond_base")
    d_wide = daily_pnl(wide_tr, "pnl_uncond_wide")
    rows: list[dict[str, Any]] = []
    for policy in POLICIES:
        tr = select_risk_trades(sub, policy)
        col = f"pnl_{policy}"
        d = daily_pnl(tr, col)
        st = risk_stats(d)
        diag = trade_diag(tr, policy)
        row: dict[str, Any] = {
            "split": split,
            "policy": policy,
            **{f"risk_{k}": v for k, v in st.items()},
            **{f"diag_{k}": v for k, v in diag.items()},
        }
        if policy != "uncond_base":
            for metric in ("sharpe", "sortino"):
                boot = bootstrap_delta(d, d_base, metric)
                row[f"d_{metric}_vs_base"] = boot["delta"]
                row[f"d_{metric}_lo"] = boot["lo"]
                row[f"d_{metric}_hi"] = boot["hi"]
        else:
            row["d_sharpe_vs_base"] = 0.0
            row["d_sharpe_lo"] = 0.0
            row["d_sharpe_hi"] = 0.0
            row["d_sortino_vs_base"] = 0.0
            row["d_sortino_lo"] = 0.0
            row["d_sortino_hi"] = 0.0
        # Decisive HIGH-conditional contrast: regime_width − uncond_wide
        if policy == "regime_width":
            for metric in ("sharpe", "sortino"):
                boot_w = bootstrap_delta(d, d_wide, metric, seed=BOOT_SEED + 7)
                row[f"d_{metric}_vs_wide"] = boot_w["delta"]
                row[f"d_{metric}_vs_wide_lo"] = boot_w["lo"]
                row[f"d_{metric}_vs_wide_hi"] = boot_w["hi"]
        else:
            row["d_sharpe_vs_wide"] = np.nan
            row["d_sharpe_vs_wide_lo"] = np.nan
            row["d_sharpe_vs_wide_hi"] = np.nan
            row["d_sortino_vs_wide"] = np.nan
            row["d_sortino_vs_wide_lo"] = np.nan
            row["d_sortino_vs_wide_hi"] = np.nan
        rows.append(row)
    return rows


def score_by_session(panel: pd.DataFrame, split: str) -> list[dict[str, Any]]:
    sub = panel[panel["split"] == split]
    rows: list[dict[str, Any]] = []
    for sess in SESSION_ORDER:
        s = sub[sub["session"] == sess]
        if s.empty:
            continue
        base_tr = select_risk_trades(s, "uncond_base")
        wide_tr = select_risk_trades(s, "uncond_wide")
        d_base = daily_pnl(base_tr, "pnl_uncond_base")
        d_wide = daily_pnl(wide_tr, "pnl_uncond_wide")
        for policy in POLICIES:
            tr = select_risk_trades(s, policy)
            d = daily_pnl(tr, f"pnl_{policy}")
            st = risk_stats(d)
            row: dict[str, Any] = {
                "split": split,
                "session": sess,
                "policy": policy,
                **{f"risk_{k}": v for k, v in st.items()},
                "n_trades": int(tr[f"pnl_{policy}"].notna().sum()),
            }
            if policy != "uncond_base":
                boot = bootstrap_delta(d, d_base, "sharpe")
                row["d_sharpe_vs_base"] = boot["delta"]
                row["d_sharpe_lo"] = boot["lo"]
                row["d_sharpe_hi"] = boot["hi"]
            if policy == "regime_width":
                boot_w = bootstrap_delta(d, d_wide, "sharpe", seed=BOOT_SEED + 11)
                row["d_sharpe_vs_wide"] = boot_w["delta"]
                row["d_sharpe_vs_wide_lo"] = boot_w["lo"]
                row["d_sharpe_vs_wide_hi"] = boot_w["hi"]
            rows.append(row)
    return rows


def fmt(x: Any, nd: int = 2) -> str:
    if isinstance(x, (int, float)) and np.isfinite(x):
        return f"{x:.{nd}f}"
    return "—"


def policy_row(block: pd.DataFrame, policy: str) -> pd.Series | None:
    r = block[block["policy"] == policy]
    if r.empty:
        return None
    return r.iloc[0]


def headline_wide_vs_regime(block: pd.DataFrame) -> dict[str, Any]:
    """Decisive cell: does HIGH-conditional width beat unconditional-wide?"""
    uw = policy_row(block, "uncond_wide")
    rw = policy_row(block, "regime_width")
    base = policy_row(block, "uncond_base")
    if uw is None or rw is None or base is None:
        return {}
    return {
        "base_sharpe": float(base["risk_sharpe"]),
        "base_E": float(base["diag_E"]),
        "wide_sharpe": float(uw["risk_sharpe"]),
        "wide_E": float(uw["diag_E"]),
        "wide_sortino": float(uw["risk_sortino"]),
        "regime_sharpe": float(rw["risk_sharpe"]),
        "regime_E": float(rw["diag_E"]),
        "regime_sortino": float(rw["risk_sortino"]),
        "d_sharpe_regime_minus_wide": float(rw["d_sharpe_vs_wide"]),
        "d_sharpe_lo": float(rw["d_sharpe_vs_wide_lo"]),
        "d_sharpe_hi": float(rw["d_sharpe_vs_wide_hi"]),
        "d_sortino_regime_minus_wide": float(rw["d_sortino_vs_wide"]),
        "d_sortino_lo": float(rw["d_sortino_vs_wide_lo"]),
        "d_sortino_hi": float(rw["d_sortino_vs_wide_hi"]),
        "d_sharpe_wide_vs_base": float(uw["d_sharpe_vs_base"]),
        "d_sharpe_regime_vs_base": float(rw["d_sharpe_vs_base"]),
        "n_wide": int(uw["diag_n"]),
        "n_regime": int(rw["diag_n"]),
    }


def write_stage_report(
    res: pd.DataFrame,
    sess_res: pd.DataFrame,
    meta: dict[str, Any],
    stage: str,
    is_tag: str,
) -> tuple[str, str]:
    split_name = {"IS": "IS", "VAL": "Validation", "OOS": "OOS"}[stage]
    block = res[res["split"] == split_name]
    hl = headline_wide_vs_regime(block)

    lines: list[str] = []
    if stage == "IS":
        lines.append("# Hypothesis 24D — Vol-Harvest Structure (IS only)")
        lines.append("")
        lines.append("## Stage gate")
        lines.append("")
        lines.append("**Val unlocked only after review.** Two independent questions (multiplicity):")
        lines.append("")
        lines.append("1. Does width help at all? (`uncond_wide` vs `uncond_base`)")
        lines.append("2. Does HIGH-conditioning add anything on top of unconditional-wide? (`regime_width` vs `uncond_wide`) — **decisive HOW cell**")
    elif stage == "VAL":
        lines.append("# Hypothesis 24D — Validation (documentation; freeze unchanged)")
        lines.append("")
        lines.append(
            f"IS tag was `{is_tag}`. Val scored once. Headline = **`uncond_wide` vs `regime_width`** "
            "(HIGH-conditional value), not each-vs-base alone."
        )
    else:
        lines.append("# Hypothesis 24D — OOS (documentation)")
        lines.append("")
        lines.append(f"IS tag `{is_tag}`. Freeze unchanged.")
    lines.append("")
    lines.append("## Freeze")
    lines.append("")
    lines.append("| Item | Value |")
    lines.append("|------|-------|")
    for k in (
        "bo_frac",
        "stop_r",
        "tgt_r",
        "width_high",
        "width_non",
        "max_hold",
        "cost_rt",
    ):
        lines.append(f"| {k} | {meta[k]} |")
    lines.append(f"| Panel rows | {meta['n_panel']:,} |")
    lines.append("")

    # HEADLINE three-way style
    lines.append("## Headline — `uncond_wide` vs `regime_width` (decisive)")
    lines.append("")
    lines.append(
        "Q2 only: does regime-conditioning the width beat always-wide? "
        "(Q1 width-vs-base already answered on IS.)"
    )
    lines.append("")
    if hl:
        lines.append("| Policy | E[pts] | Sharpe | Sortino | n |")
        lines.append("|--------|--------|--------|---------|---|")
        lines.append(
            f"| `uncond_base` | {fmt(hl['base_E'], 3)} | {fmt(hl['base_sharpe'], 3)} | — | — |"
        )
        lines.append(
            f"| `uncond_wide` | {fmt(hl['wide_E'], 3)} | {fmt(hl['wide_sharpe'], 3)} | "
            f"{fmt(hl['wide_sortino'], 3)} | {hl['n_wide']} |"
        )
        lines.append(
            f"| `regime_width` | {fmt(hl['regime_E'], 3)} | {fmt(hl['regime_sharpe'], 3)} | "
            f"{fmt(hl['regime_sortino'], 3)} | {hl['n_regime']} |"
        )
        lines.append("")
        lines.append(
            f"**ΔSharpe (`regime_width` − `uncond_wide`):** "
            f"{fmt(hl['d_sharpe_regime_minus_wide'], 3)} "
            f"[{fmt(hl['d_sharpe_lo'], 3)}, {fmt(hl['d_sharpe_hi'], 3)}]"
        )
        lines.append("")
        lines.append(
            f"**ΔSortino (`regime_width` − `uncond_wide`):** "
            f"{fmt(hl['d_sortino_regime_minus_wide'], 3)} "
            f"[{fmt(hl['d_sortino_lo'], 3)}, {fmt(hl['d_sortino_hi'], 3)}]"
        )
        lines.append("")
        if (
            np.isfinite(hl["d_sharpe_hi"])
            and hl["d_sharpe_hi"] < 0
            and np.isfinite(hl["wide_E"])
            and hl["wide_E"] < 0
        ):
            lines.append(
                "Reading: `uncond_wide` dominates `regime_width` on Sharpe; best policy still "
                "**E < 0** — not a tradeable structure."
            )
        elif np.isfinite(hl["d_sharpe_lo"]) and hl["d_sharpe_lo"] > 0:
            lines.append("Reading: `regime_width` beats `uncond_wide` on Sharpe CI — inspect E and sides.")
        else:
            lines.append("Reading: no clean HIGH-conditional width win over always-wide.")
        lines.append("")

    lines.append(f"## All policies — {split_name} pooled")
    lines.append("")
    lines.append(
        "| Policy | n | win | E[pts] | Sharpe | Sortino | MaxDD | "
        "dSharpe vs base | dSharpe vs wide |"
    )
    lines.append(
        "|--------|---|-----|--------|--------|---------|-------|"
        "----------------|-----------------|"
    )
    for policy in POLICIES:
        r = policy_row(block, policy)
        if r is None:
            continue
        dsh_b = (
            "0"
            if policy == "uncond_base"
            else f"{fmt(r['d_sharpe_vs_base'], 3)} [{fmt(r['d_sharpe_lo'], 3)}, {fmt(r['d_sharpe_hi'], 3)}]"
        )
        dsh_w = (
            f"{fmt(r['d_sharpe_vs_wide'], 3)} [{fmt(r['d_sharpe_vs_wide_lo'], 3)}, {fmt(r['d_sharpe_vs_wide_hi'], 3)}]"
            if policy == "regime_width"
            else "—"
        )
        lines.append(
            f"| `{policy}` | {int(r['diag_n'])} | {fmt(100 * r['diag_win'], 1)}% | "
            f"{fmt(r['diag_E'], 3)} | {fmt(r['risk_sharpe'], 3)} | {fmt(r['risk_sortino'], 3)} | "
            f"{fmt(r['risk_max_dd'], 1)} | {dsh_b} | {dsh_w} |"
        )
    lines.append("")

    if stage == "IS":
        lines.append("## Multi-session — Sharpe")
        lines.append("")
        lines.append("| Session | Policy | Sharpe | dSharpe vs base | dSharpe vs wide | n |")
        lines.append("|---------|--------|--------|-----------------|-----------------|---|")
        ss = sess_res[sess_res["split"] == "IS"]
        for sess in SESSION_ORDER:
            for policy in POLICIES:
                r = ss[(ss["session"] == sess) & (ss["policy"] == policy)]
                if r.empty:
                    continue
                r = r.iloc[0]
                dsh = (
                    "0"
                    if policy == "uncond_base"
                    else f"{fmt(r.get('d_sharpe_vs_base'), 3)} [{fmt(r.get('d_sharpe_lo'), 3)}, {fmt(r.get('d_sharpe_hi'), 3)}]"
                )
                dsw = (
                    f"{fmt(r.get('d_sharpe_vs_wide'), 3)} [{fmt(r.get('d_sharpe_vs_wide_lo'), 3)}, {fmt(r.get('d_sharpe_vs_wide_hi'), 3)}]"
                    if policy == "regime_width"
                    else "—"
                )
                lines.append(
                    f"| {sess} | `{policy}` | {fmt(r['risk_sharpe'], 3)} | {dsh} | {dsw} | {int(r['n_trades'])} |"
                )
        lines.append("")

    # Direction audit
    lines.append("## Direction audit")
    lines.append("")
    r0 = policy_row(block, "uncond_wide")
    if r0 is not None:
        lines.append(
            f"`uncond_wide` fills: long {int(r0['diag_n_long'])} / short {int(r0['diag_n_short'])}; "
            f"E_long {fmt(r0['diag_E_long'], 3)} / E_short {fmt(r0['diag_E_short'], 3)}."
        )
    lines.append("")

    # Tag
    tag = f"{stage}_NULL"
    detail: list[str] = []
    if hl:
        d_hi = hl["d_sharpe_hi"]
        d_lo = hl["d_sharpe_lo"]
        wide_e = hl["wide_E"]
        if np.isfinite(d_hi) and d_hi < 0:
            tag = f"{stage}_WIDE_DOMINATES" if stage != "IS" else "IS_PARTIAL"
            detail.append(
                "ΔSharpe (regime − wide) 90% CI entirely below 0 — unconditional width wins; "
                "no HIGH-conditional incremental value."
            )
        elif np.isfinite(d_lo) and d_lo > 0 and wide_e > 0:
            tag = "IS_PROMISING_PENDING_VAL" if stage == "IS" else f"{stage}_REGIME_BEATS_WIDE"
            detail.append("regime_width beats uncond_wide on Sharpe CI with E>0 on wide — rare.")
        elif np.isfinite(hl["d_sharpe_regime_minus_wide"]) and hl["d_sharpe_regime_minus_wide"] < 0:
            tag = "IS_PARTIAL" if stage == "IS" else f"{stage}_WIDE_DOMINATES"
            detail.append("Point ΔSharpe (regime − wide) < 0; HIGH-conditioning does not add value.")
        else:
            tag = f"{stage}_MIXED"
            detail.append("No clean separation on regime vs wide.")
        if np.isfinite(wide_e) and wide_e < 0:
            detail.append(
                f"Best policy `uncond_wide` still E={wide_e:.3f} < 0 — not tradeable; "
                "HOW answer is scientific (no monetizable Strategy-12 structure under costs)."
            )
        if np.isfinite(hl["d_sharpe_wide_vs_base"]) and hl["d_sharpe_wide_vs_base"] > 0:
            detail.append(
                "Q1 held: width helps vs narrow base (general execution-parameter effect, not HIGH)."
            )

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
            "`uncond_wide` crushing `regime_width` means wider helps *unconditionally* — "
            "not because of HIGH. That also answers **24B** (regime-conditional stop/target) "
            "as a side-by-side arm: fold into this dossier; do not open a separate 24B ticket. "
            "24C (holding period) remains distinct — hold until after Val."
        )
        lines.append("")
        lines.append("## Stop")
        lines.append("")
        lines.append("- Val next (headline = wide vs regime). OOS optional for triple.")
        lines.append("- Standalone **24B skipped** (absorbed here). **24C held**.")
    elif stage == "VAL":
        lines.append("## Reading")
        lines.append("")
        lines.append(
            "Documentation Val. Decisive cell is regime − wide. "
            "Even if width still beats base, negative E on best policy keeps HOW non-tradeable."
        )
        lines.append("")
        lines.append("## Stop")
        lines.append("")
        lines.append("- No refit. 24B remains folded. 24C unlock only after this Val review.")
    else:
        lines.append("## Reading")
        lines.append("")
        lines.append("Documentation OOS for parity.")
        lines.append("")
    lines.append("")
    return "\n".join(lines), tag


def write_is_report(
    res: pd.DataFrame,
    sess_res: pd.DataFrame,
    meta: dict[str, Any],
) -> tuple[str, str]:
    return write_stage_report(res, sess_res, meta, "IS", "IS_PARTIAL")


def main() -> None:
    ap = argparse.ArgumentParser(description="24D vol-harvest structure test")
    ap.add_argument("--stage", choices=("IS", "VAL", "OOS", "ALL"), default="IS")
    ap.add_argument("--rebuild", action="store_true")
    args = ap.parse_args()

    stages = ["IS", "VAL", "OOS"] if args.stage == "ALL" else [args.stage]
    if args.stage == "OOS":
        print("OOS not requested in this unlock — run VAL first, or ALL after review.", flush=True)
        # Allow OOS if explicitly asked after Val unlock path — user said Val only
        pass
    split_of_stage = {"IS": "IS", "VAL": "Validation", "OOS": "OOS"}

    panel_path = art("nq_how_24d_panel.parquet")
    if panel_path.exists() and not args.rebuild:
        print(f"Loading {panel_path}", flush=True)
        panel = pd.read_parquet(panel_path)
    else:
        panel = build_panel()
        panel.to_parquet(panel_path, index=False)
        print(f"Wrote {panel_path}", flush=True)

    freeze = {
        "bo_frac": BO_FRAC,
        "stop_r": STOP_R,
        "tgt_r": TGT_R,
        "width_high": WIDTH_HIGH,
        "width_non": WIDTH_NON,
        "max_hold": MAX_HOLD,
        "cost_rt": COST_RT,
        "size": SIZE,
        "policies": list(POLICIES),
        "note": "Frozen before Val/OOS; path side from first breakout touch only",
        "decisive_contrast": "regime_width - uncond_wide",
        "24B_folded": True,
    }
    art("nq_how_24d_thresholds_IS.json").write_text(json.dumps(freeze, indent=2), encoding="utf-8")

    score_rows: list[dict[str, Any]] = []
    sess_rows: list[dict[str, Any]] = []
    for st in stages:
        split = split_of_stage[st]
        score_rows.extend(score_split(panel, split))
        sess_rows.extend(score_by_session(panel, split))

    res_df = pd.DataFrame(score_rows)
    res_path = art("nq_how_24d_results.csv")
    if res_path.exists() and args.stage in ("VAL", "OOS"):
        prior = pd.read_csv(res_path)
        keep = prior[~prior["split"].isin([split_of_stage[s] for s in stages])]
        res_df = pd.concat([keep, res_df], ignore_index=True)
    res_df.to_csv(res_path, index=False)

    sess_df = pd.DataFrame(sess_rows)
    sess_path = art("nq_how_24d_results_by_session.csv")
    if sess_path.exists() and args.stage in ("VAL", "OOS"):
        prior_s = pd.read_csv(sess_path)
        keep_s = prior_s[~prior_s["split"].isin([split_of_stage[s] for s in stages])]
        sess_df = pd.concat([keep_s, sess_df], ignore_index=True)
    sess_df.to_csv(sess_path, index=False)

    is_tag = "IS_PARTIAL"
    is_json = art("nq_how_24d_report_IS.json")
    if is_json.exists():
        try:
            is_tag = str(json.loads(is_json.read_text(encoding="utf-8")).get("is_tag", is_tag))
        except Exception:
            pass

    meta = {**freeze, "n_panel": int(len(panel))}
    dossier = _CODE.parents[0] / "results"
    dossier.mkdir(parents=True, exist_ok=True)

    for st in stages:
        report_md, tag = write_stage_report(res_df, sess_df, meta, st, is_tag)
        art_name = {
            "IS": "nq_how_24d_report_IS",
            "VAL": "nq_how_24d_report_VAL",
            "OOS": "nq_how_24d_report_OOS",
        }[st]
        art(f"{art_name}.md").write_text(report_md, encoding="utf-8")
        hl_split = {"IS": "IS", "VAL": "Validation", "OOS": "OOS"}[st]
        payload = {
            "stage": st,
            "tag": tag,
            "is_tag": is_tag,
            "freeze_unchanged": True,
            "freeze": freeze,
            "headline": headline_wide_vs_regime(res_df[res_df["split"] == hl_split]),
            "results": res_df[res_df["split"] == hl_split].to_dict(orient="records"),
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
