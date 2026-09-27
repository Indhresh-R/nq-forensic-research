"""
Step 6 — ExpExit directionality decomposition at the →NORMAL transition.

No trades. Components at/before te only. No new CEM.
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

from constants import RESULTS
from step1_constants import CELL_C, CELL_D
from step1_extract_paths import build_panel
from step2_constants import FAMILY_EXP_EXIT
from step3_analyze import newcombe_diff_ci
from step3_constants import MIN_N_VALID, PRIMARY_HORIZON, SECONDARY_HORIZON
from step4_analyze import standardized_mean_diff


def _window_ok(seg: np.ndarray, ny: np.ndarray, t: int, n_back: int) -> bool:
    if t - n_back < 0:
        return False
    if seg[t] != seg[t - n_back]:
        return False
    return bool(np.all(np.diff(ny[t - n_back : t + 1]) == 1))


def compute_components(panel: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    close = panel["close"].to_numpy(np.float64)
    seg = panel["segment_id"].to_numpy(np.int64)
    ny = panel["ny_min"].to_numpy(np.int16)
    er30 = panel["er_30"].to_numpy(np.float64)
    er60 = panel["er_60"].to_numpy(np.float64)
    er120 = panel["er_120"].to_numpy(np.float64)
    dir_state = panel["directionality_state"].to_numpy(dtype=object)

    rows = []
    for ev in events.itertuples(index=False):
        if ev.family != FAMILY_EXP_EXIT:
            continue
        te = int(ev.event_panel_idx)
        tm = te - 1
        if tm < 0:
            continue

        row: dict = {
            "event_id": ev.event_id,
            "origin_cell": ev.origin_cell,
            "family": ev.family,
            "split": ev.split,
            "wait_to_event": int(ev.wait_to_event),
        }
        for t, prefix in ((te, "te"), (tm, "tm")):
            row[f"{prefix}_er_30"] = float(er30[t]) if np.isfinite(er30[t]) else np.nan
            row[f"{prefix}_er_60"] = float(er60[t]) if np.isfinite(er60[t]) else np.nan
            row[f"{prefix}_er_120"] = float(er120[t]) if np.isfinite(er120[t]) else np.nan
            row[f"{prefix}_dir_state"] = dir_state[t]
            if _window_ok(seg, ny, t, 60):
                signed = float(close[t] - close[t - 60])
                path = float(np.sum(np.abs(np.diff(close[t - 60 : t + 1]))))
                row[f"{prefix}_signed_net_60"] = signed
                row[f"{prefix}_abs_net_60"] = abs(signed)
                row[f"{prefix}_path_60"] = path
                row[f"{prefix}_er_60_check"] = abs(signed) / path if path > 0 else np.nan
            else:
                row[f"{prefix}_signed_net_60"] = np.nan
                row[f"{prefix}_abs_net_60"] = np.nan
                row[f"{prefix}_path_60"] = np.nan
                row[f"{prefix}_er_60_check"] = np.nan
            if _window_ok(seg, ny, t, 5):
                row[f"{prefix}_signed_net_5"] = float(close[t] - close[t - 5])
            else:
                row[f"{prefix}_signed_net_5"] = np.nan

        if np.isfinite(row["te_er_60"]) and np.isfinite(row["tm_er_60"]):
            row["er_60_change"] = row["te_er_60"] - row["tm_er_60"]
        else:
            row["er_60_change"] = np.nan
        row["te_signed_net_5"] = row.get("te_signed_net_5", np.nan)
        rows.append(row)

    return pd.DataFrame(rows)


def freeze_cuts(comp: pd.DataFrame) -> dict:
    cols = (
        "te_er_60",
        "te_path_60",
        "te_abs_net_60",
        "er_60_change",
        "te_signed_net_5",
    )
    is_m = comp.loc[comp["split"] == "IS"]
    out = {"source": "IS ExpExit component terciles at/near te", "features": {}}
    for c in cols:
        x = is_m[c].to_numpy(float)
        x = x[np.isfinite(x)]
        if len(x) == 0:
            q33 = q67 = np.nan
        else:
            q33 = float(np.quantile(x, 1.0 / 3.0))
            q67 = float(np.quantile(x, 2.0 / 3.0))
        out["features"][c] = {"q33": q33, "q67": q67, "n_is": int(len(x))}
    return out


def assign_tercile(v: float, q33: float, q67: float) -> str:
    if not np.isfinite(v) or not np.isfinite(q33) or not np.isfinite(q67):
        return "NA"
    if v <= q33:
        return "T1"
    if v <= q67:
        return "T2"
    return "T3"


def balance_table(comp: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "te_er_60",
        "te_er_30",
        "te_er_120",
        "te_path_60",
        "te_abs_net_60",
        "te_signed_net_60",
        "er_60_change",
        "te_signed_net_5",
        "tm_er_60",
        "tm_path_60",
        "tm_abs_net_60",
    ]
    c = comp.loc[comp["origin_cell"] == CELL_C]
    d = comp.loc[comp["origin_cell"] == CELL_D]
    rows = []
    for col in cols:
        xc = c[col].to_numpy(float)
        xd = d[col].to_numpy(float)
        rows.append(
            {
                "component": col,
                "mean_c": float(np.nanmean(xc)),
                "mean_d": float(np.nanmean(xd)),
                "smd_d_minus_c": standardized_mean_diff(xd, xc),
                "n_c_finite": int(np.isfinite(xc).sum()),
                "n_d_finite": int(np.isfinite(xd).sum()),
            }
        )
    return pd.DataFrame(rows)


def within_bin_contrasts(
    comp: pd.DataFrame, metrics: pd.DataFrame, feature: str, cuts: dict
) -> pd.DataFrame:
    q33 = cuts["features"][feature]["q33"]
    q67 = cuts["features"][feature]["q67"]
    tmp = comp.copy()
    tmp["bin"] = [assign_tercile(float(v), q33, q67) for v in tmp[feature].to_numpy(float)]

    rows = []
    for h in (PRIMARY_HORIZON, SECONDARY_HORIZON):
        m = metrics.loc[
            (metrics["family"] == FAMILY_EXP_EXIT)
            & (metrics["horizon"] == h)
            & (metrics["valid"])
        ]
        df = tmp.merge(
            m[["event_id", "returned_to_origin_range", "reached_opposite_range"]],
            on="event_id",
            how="inner",
        )
        for bval, g in df.groupby("bin", sort=True):
            gc = g.loc[g["origin_cell"] == CELL_C]
            gd = g.loc[g["origin_cell"] == CELL_D]
            nc, nd = len(gc), len(gd)
            row = {
                "feature": feature,
                "bin": bval,
                "horizon": h,
                "n_c": nc,
                "n_d": nd,
                "eligible": nc >= MIN_N_VALID and nd >= MIN_N_VALID,
                "mean_feature_c": float(gc[feature].mean()) if nc else np.nan,
                "mean_feature_d": float(gd[feature].mean()) if nd else np.nan,
            }
            for name, col in (
                ("return", "returned_to_origin_range"),
                ("opposite", "reached_opposite_range"),
            ):
                kc = int(gc[col].sum()) if nc else 0
                kd = int(gd[col].sum()) if nd else 0
                diff, lo, hi = newcombe_diff_ci(kc, nc, kd, nd)
                row[f"{name}_rate_c"] = kc / nc if nc else np.nan
                row[f"{name}_rate_d"] = kd / nd if nd else np.nan
                row[f"{name}_diff"] = diff
                row[f"{name}_diff_ci_lo"] = lo
                row[f"{name}_diff_ci_hi"] = hi
                row[f"{name}_sign"] = (
                    0
                    if not np.isfinite(diff) or abs(diff) < 1e-15
                    else (1 if diff > 0 else -1)
                )
            rows.append(row)
    return pd.DataFrame(rows)


def monotonicity_table(
    comp: pd.DataFrame, metrics: pd.DataFrame, feature: str, cuts: dict
) -> pd.DataFrame:
    """Within C and within D, destination rates by feature tercile."""
    q33 = cuts["features"][feature]["q33"]
    q67 = cuts["features"][feature]["q67"]
    tmp = comp.copy()
    tmp["bin"] = [assign_tercile(float(v), q33, q67) for v in tmp[feature].to_numpy(float)]
    m = metrics.loc[
        (metrics["family"] == FAMILY_EXP_EXIT)
        & (metrics["horizon"] == PRIMARY_HORIZON)
        & (metrics["valid"])
    ]
    df = tmp.merge(
        m[["event_id", "returned_to_origin_range", "reached_opposite_range"]],
        on="event_id",
        how="inner",
    )
    rows = []
    for cell in (CELL_C, CELL_D):
        gcell = df.loc[df["origin_cell"] == cell]
        for bval, g in gcell.groupby("bin", sort=True):
            n = len(g)
            rows.append(
                {
                    "feature": feature,
                    "origin_cell": cell,
                    "bin": bval,
                    "n": n,
                    "return_rate": float(g["returned_to_origin_range"].mean()) if n else np.nan,
                    "opposite_rate": float(g["reached_opposite_range"].mean()) if n else np.nan,
                    "mean_feature": float(g[feature].mean()) if n else np.nan,
                }
            )
    return pd.DataFrame(rows)


def classify(
    within_er: pd.DataFrame, pooled: dict, secondary: dict[str, pd.DataFrame]
) -> dict:
    u_ret = pooled["return_diff"]
    u_opp = pooled["opposite_diff"]
    ref_ret = 1 if u_ret > 0 else -1
    ref_opp = 1 if u_opp > 0 else -1

    elig = within_er.loc[
        (within_er["horizon"] == PRIMARY_HORIZON)
        & (within_er["eligible"])
        & (within_er["bin"] != "NA")
    ]
    detail = []
    for _, r in elig.iterrows():
        detail.append(
            {
                "bin": r["bin"],
                "n_c": int(r["n_c"]),
                "n_d": int(r["n_d"]),
                "return_diff": float(r["return_diff"]),
                "opposite_diff": float(r["opposite_diff"]),
                "return_keeps": int(r["return_sign"]) == ref_ret
                and abs(float(r["return_diff"])) >= 0.5 * abs(u_ret),
                "opposite_keeps": int(r["opposite_sign"]) == ref_opp
                and abs(float(r["opposite_diff"])) >= 0.5 * abs(u_opp),
            }
        )

    if not detail:
        primary = "INCONCLUSIVE"
    else:
        keep = [d for d in detail if d["return_keeps"] and d["opposite_keeps"]]
        lose = [
            d
            for d in detail
            if (not d["return_keeps"]) and (not d["opposite_keeps"])
        ]
        if len(keep) == len(detail):
            primary = "LABEL_RESIDUAL"
        elif len(lose) == len(detail):
            primary = "COMPONENT_ACCOUNTS"
        else:
            primary = "CONDITIONAL"

    # PATH_OR_NET if er doesn't account but path or abs_net does
    path_or_net = None
    if primary == "LABEL_RESIDUAL":
        for name, wdf in secondary.items():
            el = wdf.loc[
                (wdf["horizon"] == PRIMARY_HORIZON)
                & (wdf["eligible"])
                & (wdf["bin"] != "NA")
            ]
            if len(el) == 0:
                continue
            lose = 0
            for _, r in el.iterrows():
                rk = int(r["return_sign"]) == ref_ret and abs(float(r["return_diff"])) >= 0.5 * abs(
                    u_ret
                )
                ok = int(r["opposite_sign"]) == ref_opp and abs(
                    float(r["opposite_diff"])
                ) >= 0.5 * abs(u_opp)
                if (not rk) and (not ok):
                    lose += 1
            if lose == len(el):
                path_or_net = name
                break

    return {
        "classification": primary if path_or_net is None else "PATH_OR_NET",
        "primary_er60_te_class": primary,
        "path_or_net_feature": path_or_net,
        "detail": detail,
        "reference_unmatched": pooled,
    }


def main() -> None:
    print("Loading panel + ExpExit events…", flush=True)
    panel = build_panel()
    events = pd.read_parquet(RESULTS / "step2_events.parquet")
    metrics = pd.read_parquet(RESULTS / "step2_path_metrics.parquet")
    events = events.loc[events["family"] == FAMILY_EXP_EXIT].copy()

    print("Computing transition components…", flush=True)
    comp = compute_components(panel, events)
    # cleanup botched helper leftovers if any
    comp.to_parquet(RESULTS / "step6_components.parquet", index=False)

    cuts = freeze_cuts(comp)
    (RESULTS / "step6_cuts_frozen.json").write_text(
        json.dumps(cuts, indent=2), encoding="utf-8"
    )

    bal = balance_table(comp)
    bal.to_csv(RESULTS / "step6_balance.csv", index=False)

    features = (
        "te_er_60",
        "te_path_60",
        "te_abs_net_60",
        "er_60_change",
        "te_signed_net_5",
    )
    within_parts = [within_bin_contrasts(comp, metrics, f, cuts) for f in features]
    within = pd.concat(within_parts, ignore_index=True)
    within.to_csv(RESULTS / "step6_within_bin_contrasts.csv", index=False)

    mono_parts = [monotonicity_table(comp, metrics, f, cuts) for f in ("te_er_60", "te_path_60")]
    mono = pd.concat(mono_parts, ignore_index=True)
    mono.to_csv(RESULTS / "step6_monotonicity.csv", index=False)

    # pooled unmatched
    m30 = metrics.loc[
        (metrics["family"] == FAMILY_EXP_EXIT)
        & (metrics["horizon"] == PRIMARY_HORIZON)
        & (metrics["valid"])
    ]
    gc = m30.loc[m30["origin_cell"] == CELL_C]
    gd = m30.loc[m30["origin_cell"] == CELL_D]
    pooled = {"n_c": len(gc), "n_d": len(gd)}
    for name, col in (
        ("return", "returned_to_origin_range"),
        ("opposite", "reached_opposite_range"),
    ):
        diff, lo, hi = newcombe_diff_ci(
            int(gc[col].sum()), len(gc), int(gd[col].sum()), len(gd)
        )
        pooled[f"{name}_diff"] = diff
        pooled[f"{name}_ci"] = [lo, hi]

    within_er = within.loc[within["feature"] == "te_er_60"]
    secondary = {
        "te_path_60": within.loc[within["feature"] == "te_path_60"],
        "te_abs_net_60": within.loc[within["feature"] == "te_abs_net_60"],
    }
    verdict = classify(within_er, pooled, secondary)

    # document tm non-overlap (C/D ER bands at te-1 are disjoint by construction)
    tm = comp.dropna(subset=["tm_er_60"])
    verdict["tm_er60_c_min"] = float(tm.loc[tm["origin_cell"] == CELL_C, "tm_er_60"].min())
    verdict["tm_er60_d_max"] = float(tm.loc[tm["origin_cell"] == CELL_D, "tm_er_60"].max())
    verdict["tm_er60_ranges_disjoint_expected"] = True

    (RESULTS / "step6_verdict.json").write_text(
        json.dumps(verdict, indent=2, default=str), encoding="utf-8"
    )
    print(f"Verdict: {verdict['classification']}", flush=True)
    print(
        f"tm ER60: C_min={verdict['tm_er60_c_min']:.4f} D_max={verdict['tm_er60_d_max']:.4f}",
        flush=True,
    )


if __name__ == "__main__":
    main()
