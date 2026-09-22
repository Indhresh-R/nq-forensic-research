"""
Step 3: frozen leave-range outcome join for Strategy 50.

No grammar changes. No threshold search. No trading rules.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact, norm

ROOT = Path(__file__).resolve().parents[3]
CODE = Path(__file__).resolve().parent
OUT = Path(__file__).resolve().parents[1] / "results"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(CODE))

from constants import W_CONFIRM

HORIZONS = (8, 16, 32)


def _outcome_t0(row: pd.Series) -> int:
    """Sequence-declaration index for outcome start (exclusive → next bar)."""
    cls = row["event_class"]
    if cls == "C":
        return int(row["t_sequence_complete"])
    if cls == "A":
        return int(row["t_return"])
    # B
    if pd.notna(row.get("t_confirm")) and row.get("fail_reason") in {
        "test_fail_hl_or_vol",
        "test_fail_lh_or_vol",
    }:
        return int(row["t_confirm"])
    if row.get("fail_reason") == "window_expire":
        return int(row["t_return"]) + W_CONFIRM
    # adverse close during confirm window
    if pd.notna(row.get("t_confirm")):
        return int(row["t_confirm"])
    return int(row["t_return"])


def attach_outcomes(events: pd.DataFrame, bars: pd.DataFrame) -> pd.DataFrame:
    close_t = bars["close_ticks"].to_numpy(np.int64)
    low_t = bars["low_ticks"].to_numpy(np.int64)
    high_t = bars["high_ticks"].to_numpy(np.int64)
    n = len(bars)
    rows = []
    for _, d in events.iterrows():
        t0 = _outcome_t0(d)
        start = t0 + 1
        kind = d["kind"]
        tr_low_t = int(d["tr_low_ticks"])
        tr_high_t = int(d["tr_high_ticks"])
        height = max(1, tr_high_t - tr_low_t)
        e_ticks = int(d["E_ticks"])
        for H in HORIZONS:
            end = start + H
            if start >= n or end > n:
                leave = np.nan
                extent = np.nan
                fail_back = np.nan
                usable = False
            else:
                usable = True
                path_close = close_t[start:end]
                if kind == "spring":
                    leave = float(np.any(path_close > tr_high_t))
                    max_c = int(path_close.max())
                    extent = float(max(0, max_c - tr_high_t) / height)
                    fail_back = float(np.any(low_t[start:end] < e_ticks))
                else:
                    leave = float(np.any(path_close < tr_low_t))
                    min_c = int(path_close.min())
                    extent = float(max(0, tr_low_t - min_c) / height)
                    fail_back = float(np.any(high_t[start:end] > e_ticks))
            rows.append(
                {
                    "event_class": d["event_class"],
                    "kind": kind,
                    "tr_id": d["tr_id"],
                    "year": d["year"],
                    "split": d["split"],
                    "t_return": d["t_return"],
                    "t_sequence_complete": d["t_sequence_complete"],
                    "fail_reason": d["fail_reason"],
                    "outcome_t0": t0,
                    "horizon": H,
                    "usable": usable,
                    "LEAVE_IMPLIED": leave,
                    "EXTENT": extent,
                    "FAIL_BACK": fail_back,
                }
            )
    return pd.DataFrame(rows)


def _two_prop(p1: float, n1: int, p2: float, n2: int) -> tuple[float, float]:
    """Return (delta, two-sided p). Fisher if any expected < 5."""
    if n1 == 0 or n2 == 0:
        return float("nan"), float("nan")
    x1 = int(round(p1 * n1))
    x2 = int(round(p2 * n2))
    # clamp
    x1 = min(max(x1, 0), n1)
    x2 = min(max(x2, 0), n2)
    table = np.array([[x1, n1 - x1], [x2, n2 - x2]])
    # expected counts
    exp_ok = True
    total = table.sum()
    if total == 0:
        return float("nan"), float("nan")
    for i in range(2):
        for j in range(2):
            e = table[i, :].sum() * table[:, j].sum() / total
            if e < 5:
                exp_ok = False
    delta = p1 - p2
    if not exp_ok:
        _, p = fisher_exact(table)
        return delta, float(p)
    p_pool = (x1 + x2) / (n1 + n2)
    se = np.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
    if se == 0:
        return delta, 1.0
    z = delta / se
    p = 2 * (1 - norm.cdf(abs(z)))
    return float(delta), float(p)


def contrast_table(out: pd.DataFrame, left: str, right: str) -> pd.DataFrame:
    rows = []
    for split in ("IS", "Validation", "OOS"):
        for H in HORIZONS:
            a = out[(out["split"] == split) & (out["horizon"] == H) & (out["event_class"] == left) & (out["usable"])]
            b = out[(out["split"] == split) & (out["horizon"] == H) & (out["event_class"] == right) & (out["usable"])]
            n_a, n_b = len(a), len(b)
            p_a = float(a["LEAVE_IMPLIED"].mean()) if n_a else float("nan")
            p_b = float(b["LEAVE_IMPLIED"].mean()) if n_b else float("nan")
            # primary: left - right with C as left typically
            delta, pval = _two_prop(p_a, n_a, p_b, n_b)
            rows.append(
                {
                    "contrast": f"{left}_vs_{right}",
                    "split": split,
                    "horizon": H,
                    f"n_{left}": n_a,
                    f"n_{right}": n_b,
                    f"p_{left}": p_a,
                    f"p_{right}": p_b,
                    "delta": delta,
                    "p_value": pval,
                }
            )
    return pd.DataFrame(rows)


def apply_gate(c_vs_a: pd.DataFrame, events: pd.DataFrame) -> dict:
    """Preregistered SUPPORTED / NOT SUPPORTED / INCONCLUSIVE."""
    # Sample floors on C and A (event counts, not horizon-duplicated): use unique events
    def n_class(split: str, cls: str) -> int:
        return int(((events["split"] == split) & (events["event_class"] == cls)).sum())

    n_c_is, n_a_is = n_class("IS", "C"), n_class("IS", "A")
    n_c_oos, n_a_oos = n_class("OOS", "C"), n_class("OOS", "A")

    underpowered = n_c_is < 30 or n_a_is < 30 or n_c_oos < 20 or n_a_oos < 20

    # For each H, check IS p<=0.05 and same sign across IS/Val/OOS
    stable_horizons = []
    detail = {}
    for H in HORIZONS:
        sub = c_vs_a[c_vs_a["horizon"] == H].set_index("split")
        if not {"IS", "Validation", "OOS"}.issubset(sub.index):
            detail[H] = {"stable": False, "reason": "missing_split"}
            continue
        signs = [np.sign(sub.loc[s, "delta"]) for s in ("IS", "Validation", "OOS")]
        same = len(set(signs)) == 1 and signs[0] != 0 and np.isfinite(sub.loc["IS", "delta"])
        is_sig = bool(sub.loc["IS", "p_value"] <= 0.05) if np.isfinite(sub.loc["IS", "p_value"]) else False
        ok = same and is_sig
        detail[H] = {
            "stable_sign": bool(same),
            "is_p": float(sub.loc["IS", "p_value"]) if np.isfinite(sub.loc["IS", "p_value"]) else None,
            "is_significant": is_sig,
            "deltas": {s: float(sub.loc[s, "delta"]) if np.isfinite(sub.loc[s, "delta"]) else None for s in ("IS", "Validation", "OOS")},
            "passes_horizon_rule": ok,
        }
        if ok:
            stable_horizons.append(H)

    if underpowered:
        label = "INCONCLUSIVE"
        reason = (
            f"Sample floors not met: IS C={n_c_is} A={n_a_is} (need >=30 each); "
            f"OOS C={n_c_oos} A={n_a_oos} (need >=20 each)."
        )
    elif len(stable_horizons) >= 2:
        label = "SUPPORTED"
        reason = f"Stable significant horizons: {stable_horizons}"
    else:
        label = "NOT SUPPORTED"
        reason = f"Fewer than two horizons passed the multi-split gate; passed={stable_horizons}"

    return {
        "verdict": label,
        "reason": reason,
        "n_C_IS": n_c_is,
        "n_A_IS": n_a_is,
        "n_C_OOS": n_c_oos,
        "n_A_OOS": n_a_oos,
        "underpowered": underpowered,
        "horizon_detail": {str(k): v for k, v in detail.items()},
        "stable_horizons": stable_horizons,
    }


def confirmation_label(c_vs_b: pd.DataFrame, events: pd.DataFrame) -> dict:
    """Descriptive only; cannot rescue primary verdict."""
    n_c_is = int(((events["split"] == "IS") & (events["event_class"] == "C")).sum())
    n_b_is = int(((events["split"] == "IS") & (events["event_class"] == "B")).sum())
    n_c_oos = int(((events["split"] == "OOS") & (events["event_class"] == "C")).sum())
    n_b_oos = int(((events["split"] == "OOS") & (events["event_class"] == "B")).sum())
    under = n_c_is < 30 or n_b_is < 30 or n_c_oos < 20 or n_b_oos < 20
    stable = []
    for H in HORIZONS:
        sub = c_vs_b[c_vs_b["horizon"] == H].set_index("split")
        if not {"IS", "Validation", "OOS"}.issubset(sub.index):
            continue
        signs = [np.sign(sub.loc[s, "delta"]) for s in ("IS", "Validation", "OOS")]
        same = len(set(signs)) == 1 and signs[0] != 0
        is_sig = bool(sub.loc["IS", "p_value"] <= 0.05) if np.isfinite(sub.loc["IS", "p_value"]) else False
        if same and is_sig:
            stable.append(H)
    if under:
        lab = "INCONCLUSIVE"
    elif len(stable) >= 2:
        lab = "CONFIRMATION ADDS"
    else:
        lab = "CONFIRMATION DOES NOT ADD"
    return {
        "label": lab,
        "underpowered": under,
        "stable_horizons": stable,
        "n_C_IS": n_c_is,
        "n_B_IS": n_b_is,
        "n_C_OOS": n_c_oos,
        "n_B_OOS": n_b_oos,
    }


def main() -> None:
    events = pd.read_parquet(OUT / "events.parquet")
    bars = pd.read_parquet(OUT / "bars_15m.parquet")
    print(f"events={len(events)} bars={len(bars)}", flush=True)

    out = attach_outcomes(events, bars)
    out.to_parquet(OUT / "outcomes.parquet", index=False)

    c_vs_a = contrast_table(out, "C", "A")
    c_vs_b = contrast_table(out, "C", "B")
    # rename delta to mean C - A
    c_vs_a.to_csv(OUT / "contrast_C_vs_A.csv", index=False)
    c_vs_b.to_csv(OUT / "contrast_C_vs_B.csv", index=False)

    gate = apply_gate(c_vs_a, events)
    conf = confirmation_label(c_vs_b, events)
    summary = {"primary_C_vs_A": gate, "secondary_C_vs_B": conf}
    (OUT / "step3_verdict.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)
    print(c_vs_a.to_string(index=False), flush=True)
    print(c_vs_b.to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
