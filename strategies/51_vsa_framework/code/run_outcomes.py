"""
Step 3: frozen mechanism outcome join for Strategy 51 VSA.

No grammar changes. No threshold search. No trading rules.
Primary outcome: DOWN_CLOSE(H). Companion: FAIL_CLEAR_ND(H).
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

HORIZONS = (4, 8, 16)


def _path_usable(seg: np.ndarray, t_conf: int, H: int) -> bool:
    """All bars t_conf .. t_conf+H must exist and share segment."""
    end = t_conf + H
    if t_conf < 0 or end >= len(seg):
        return False
    s0 = int(seg[t_conf])
    return bool(np.all(seg[t_conf : end + 1] == s0))


def attach_outcomes(events: pd.DataFrame, bars: pd.DataFrame) -> pd.DataFrame:
    close = bars["close"].to_numpy(np.float64)
    high = bars["high"].to_numpy(np.float64)
    seg = bars["segment_id"].to_numpy(np.int64)
    n = len(bars)
    rows: list[dict] = []

    for _, d in events.iterrows():
        t_conf = int(d["t_confirmation"])
        t_event = int(d["t_event"])
        high_event = float(d["high_event"])
        close_conf = float(close[t_conf]) if 0 <= t_conf < n else float("nan")

        for H in HORIZONS:
            usable = _path_usable(seg, t_conf, H)
            down_close = float("nan")
            fail_clear = float("nan")
            if usable:
                # DOWN_CLOSE: close[t_conf + H] < close[t_conf]
                down_close = float(close[t_conf + H] < close_conf)
                # FAIL_CLEAR_ND: max high on (t_conf+1 .. t_conf+H) <= high[t_event]
                path_high = high[t_conf + 1 : t_conf + H + 1]
                fail_clear = float(float(np.max(path_high)) <= high_event)

            rows.append(
                {
                    "event_class": d["event_class"],
                    "kind": d["kind"],
                    "year": int(d["year"]),
                    "split": d["split"],
                    "t_event": t_event,
                    "t_confirmation": t_conf,
                    "t_sequence_complete": int(d["t_sequence_complete"]),
                    "horizon": H,
                    "usable": usable,
                    "DOWN_CLOSE": down_close,
                    "FAIL_CLEAR_ND": fail_clear,
                }
            )
    return pd.DataFrame(rows)


def _two_prop(p1: float, n1: int, p2: float, n2: int) -> tuple[float, float]:
    """Return (delta=p1-p2, two-sided p). Fisher if any expected < 5."""
    if n1 == 0 or n2 == 0 or not np.isfinite(p1) or not np.isfinite(p2):
        return float("nan"), float("nan")
    x1 = int(round(p1 * n1))
    x2 = int(round(p2 * n2))
    x1 = min(max(x1, 0), n1)
    x2 = min(max(x2, 0), n2)
    table = np.array([[x1, n1 - x1], [x2, n2 - x2]])
    total = table.sum()
    if total == 0:
        return float("nan"), float("nan")
    exp_ok = True
    for i in range(2):
        for j in range(2):
            e = table[i, :].sum() * table[:, j].sum() / total
            if e < 5:
                exp_ok = False
    delta = p1 - p2
    if not exp_ok:
        _, p = fisher_exact(table)
        return float(delta), float(p)
    p_pool = (x1 + x2) / (n1 + n2)
    se = np.sqrt(p_pool * (1.0 - p_pool) * (1.0 / n1 + 1.0 / n2))
    if se == 0:
        return float(delta), 1.0
    z = delta / se
    p = 2.0 * (1.0 - norm.cdf(abs(z)))
    return float(delta), float(p)


def contrast_table(out: pd.DataFrame, left: str, right: str, metric: str) -> pd.DataFrame:
    rows = []
    for split in ("IS", "Validation", "OOS"):
        for H in HORIZONS:
            a = out[
                (out["split"] == split)
                & (out["horizon"] == H)
                & (out["event_class"] == left)
                & (out["usable"])
            ]
            b = out[
                (out["split"] == split)
                & (out["horizon"] == H)
                & (out["event_class"] == right)
                & (out["usable"])
            ]
            n_a, n_b = len(a), len(b)
            p_a = float(a[metric].mean()) if n_a else float("nan")
            p_b = float(b[metric].mean()) if n_b else float("nan")
            delta, pval = _two_prop(p_a, n_a, p_b, n_b)
            rows.append(
                {
                    "metric": metric,
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


def apply_primary_gate(c_vs_a: pd.DataFrame, events: pd.DataFrame) -> dict:
    """Preregistered SUPPORTED / NOT SUPPORTED / INCONCLUSIVE on DOWN_CLOSE C vs A."""

    def n_class(split: str, cls: str) -> int:
        return int(((events["split"] == split) & (events["event_class"] == cls)).sum())

    n_c_is, n_a_is = n_class("IS", "C"), n_class("IS", "A")
    n_c_oos, n_a_oos = n_class("OOS", "C"), n_class("OOS", "A")
    underpowered = n_c_is < 30 or n_a_is < 30 or n_c_oos < 20 or n_a_oos < 20

    stable_horizons: list[int] = []
    detail: dict = {}
    for H in HORIZONS:
        sub = c_vs_a[c_vs_a["horizon"] == H].set_index("split")
        if not {"IS", "Validation", "OOS"}.issubset(sub.index):
            detail[H] = {"stable": False, "reason": "missing_split"}
            continue
        signs = [np.sign(sub.loc[s, "delta"]) for s in ("IS", "Validation", "OOS")]
        same = len(set(float(s) for s in signs)) == 1 and signs[0] != 0 and np.isfinite(
            sub.loc["IS", "delta"]
        )
        is_sig = (
            bool(sub.loc["IS", "p_value"] <= 0.05)
            if np.isfinite(sub.loc["IS", "p_value"])
            else False
        )
        ok = bool(same and is_sig)
        detail[H] = {
            "stable_sign": bool(same),
            "is_p": float(sub.loc["IS", "p_value"]) if np.isfinite(sub.loc["IS", "p_value"]) else None,
            "is_significant": is_sig,
            "deltas": {
                s: float(sub.loc[s, "delta"]) if np.isfinite(sub.loc[s, "delta"]) else None
                for s in ("IS", "Validation", "OOS")
            },
            "passes_horizon_rule": ok,
        }
        if ok:
            stable_horizons.append(int(H))

    # Separate reporting layers
    mechanism_note = {
        "stable_significant_horizons_ignoring_floors": stable_horizons,
        "n_stable_ignoring_floors": len(stable_horizons),
    }

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
        "n_C_Validation": n_class("Validation", "C"),
        "n_A_Validation": n_class("Validation", "A"),
        "n_C_OOS": n_c_oos,
        "n_A_OOS": n_a_oos,
        "underpowered": underpowered,
        "oos_floor_met": n_c_oos >= 20 and n_a_oos >= 20,
        "is_floor_met": n_c_is >= 30 and n_a_is >= 30,
        "horizon_detail": {str(k): v for k, v in detail.items()},
        "stable_horizons": stable_horizons,
        "mechanism_evidence_ignoring_sample_floors": mechanism_note,
    }


def secondary_nd_signature_label(c_vs_b: pd.DataFrame, events: pd.DataFrame) -> dict:
    """Descriptive only; cannot rescue primary verdict."""

    def n_class(split: str, cls: str) -> int:
        return int(((events["split"] == split) & (events["event_class"] == cls)).sum())

    n_c_is, n_b_is = n_class("IS", "C"), n_class("IS", "B")
    n_c_oos, n_b_oos = n_class("OOS", "C"), n_class("OOS", "B")
    under = n_c_is < 30 or n_b_is < 30 or n_c_oos < 20 or n_b_oos < 20

    stable: list[int] = []
    detail: dict = {}
    for H in HORIZONS:
        sub = c_vs_b[c_vs_b["horizon"] == H].set_index("split")
        if not {"IS", "Validation", "OOS"}.issubset(sub.index):
            continue
        signs = [np.sign(sub.loc[s, "delta"]) for s in ("IS", "Validation", "OOS")]
        same = len(set(float(s) for s in signs)) == 1 and signs[0] != 0
        is_sig = (
            bool(sub.loc["IS", "p_value"] <= 0.05)
            if np.isfinite(sub.loc["IS", "p_value"])
            else False
        )
        detail[str(H)] = {
            "stable_sign": bool(same),
            "is_significant": is_sig,
            "deltas": {
                s: float(sub.loc[s, "delta"]) if np.isfinite(sub.loc[s, "delta"]) else None
                for s in ("IS", "Validation", "OOS")
            },
        }
        if same and is_sig:
            stable.append(int(H))

    if under:
        lab = "INCONCLUSIVE"
    elif len(stable) >= 2:
        lab = "ND_SIGNATURE_ADDS"
    else:
        lab = "ND_SIGNATURE_DOES_NOT_ADD"

    return {
        "label": lab,
        "underpowered": under,
        "stable_horizons": stable,
        "horizon_detail": detail,
        "n_C_IS": n_c_is,
        "n_B_IS": n_b_is,
        "n_C_OOS": n_c_oos,
        "n_B_OOS": n_b_oos,
        "oos_floor_met": n_c_oos >= 20 and n_b_oos >= 20,
    }


def main() -> None:
    events = pd.read_parquet(OUT / "events.parquet")
    bars = pd.read_parquet(OUT / "bars_15m.parquet")
    print(f"events={len(events)} bars={len(bars)}", flush=True)

    out = attach_outcomes(events, bars)
    out.to_parquet(OUT / "outcomes.parquet", index=False)

    c_vs_a = contrast_table(out, "C", "A", "DOWN_CLOSE")
    c_vs_b = contrast_table(out, "C", "B", "DOWN_CLOSE")
    fail_c_vs_a = contrast_table(out, "C", "A", "FAIL_CLEAR_ND")
    fail_c_vs_b = contrast_table(out, "C", "B", "FAIL_CLEAR_ND")

    c_vs_a.to_csv(OUT / "contrast_C_vs_A.csv", index=False)
    c_vs_b.to_csv(OUT / "contrast_C_vs_B.csv", index=False)
    fail_c_vs_a.to_csv(OUT / "contrast_FAIL_CLEAR_C_vs_A.csv", index=False)
    fail_c_vs_b.to_csv(OUT / "contrast_FAIL_CLEAR_C_vs_B.csv", index=False)

    gate = apply_primary_gate(c_vs_a, events)
    secondary = secondary_nd_signature_label(c_vs_b, events)
    summary = {
        "primary_metric": "DOWN_CLOSE",
        "primary_contrast": "C_vs_A",
        "primary_C_vs_A": gate,
        "secondary_C_vs_B_DOWN_CLOSE": secondary,
        "companion_FAIL_CLEAR_ND": {
            "note": "Descriptive only; cannot award SUPPORTED alone.",
            "C_vs_A_file": "contrast_FAIL_CLEAR_C_vs_A.csv",
            "C_vs_B_file": "contrast_FAIL_CLEAR_C_vs_B.csv",
        },
        "horizons": list(HORIZONS),
        "usable_rates": {
            cls: float(out.loc[out["event_class"] == cls, "usable"].mean())
            if (out["event_class"] == cls).any()
            else None
            for cls in ("A", "B", "C")
        },
    }
    (OUT / "step3_verdict.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)
    print("\n=== C vs A DOWN_CLOSE ===", flush=True)
    print(c_vs_a.to_string(index=False), flush=True)
    print("\n=== C vs B DOWN_CLOSE ===", flush=True)
    print(c_vs_b.to_string(index=False), flush=True)
    print("\n=== C vs A FAIL_CLEAR_ND ===", flush=True)
    print(fail_c_vs_a.to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
