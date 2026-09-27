"""Strategy 60 — cost/feasibility (read-only over 55–59 artifacts)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
STRAT = Path(__file__).resolve().parents[1]
RESULTS = STRAT / "results"
COST = 1.0

P55 = ROOT / "strategies" / "55_price_path_events" / "results"
P56 = ROOT / "strategies" / "56_range_break_failed_return" / "results"
P57 = ROOT / "strategies" / "57_event_b_path_timing" / "results"
P58 = ROOT / "strategies" / "58_extreme_rejection_path" / "results"
P59 = ROOT / "strategies" / "59_orb_first_passage" / "results"


def breakeven_grid() -> pd.DataFrame:
    sizes = [2, 4, 6, 8, 10, 15, 20]
    rows = []
    for W in sizes:
        for L in sizes:
            p_star = (L + COST) / (W + L)
            e_gross_at_55 = 0.55 * W - 0.45 * L
            rows.append(
                {
                    "W": W,
                    "L": L,
                    "p_star": p_star,
                    "E_gross_at_p55": e_gross_at_55,
                    "E_net_at_p55": e_gross_at_55 - COST,
                    "clears_cost_at_p55": e_gross_at_55 > COST,
                }
            )
    return pd.DataFrame(rows)


def inventory() -> pd.DataFrame:
    rows = []

    def trade_row(sid: str, path: Path, name: str):
        t = pd.read_csv(path)
        is_r = t.loc[t["split"] == "IS"].iloc[0]
        rows.append(
            {
                "strategy": sid,
                "name": name,
                "kind": "fixed_hold_trade",
                "n_is": int(is_r["n_trades"]),
                "mean_gross_is": float(is_r["mean_gross"]),
                "mean_net_is": float(is_r["mean_net"]),
                "hit_rate_is": float(is_r["hit_rate"]),
                "abs_gross_le_0_25": abs(float(is_r["mean_gross"])) <= 0.25,
                "note": "gross~0 → net~-cost",
            }
        )

    trade_row("55", P55 / "event_a_trade_summary.csv", "Event A hold")
    trade_row("56", P56 / "event_b_trade_summary.csv", "Event B hold")

    ladder = pd.read_csv(P57 / "path_ladder_by_split.csv")
    r = ladder.loc[(ladder["split"] == "IS") & (ladder["horizon"] == 15)].iloc[0]
    mfe, mae = float(r["med_mfe"]), float(r["med_mae"])
    sym = abs(mfe - mae) / max(mfe, mae, 1e-9) <= 0.10
    rows.append(
        {
            "strategy": "57",
            "name": "Event B path",
            "kind": "path_mfe_mae",
            "n_is": int(r["n"]),
            "mean_gross_is": np.nan,
            "mean_net_is": np.nan,
            "hit_rate_is": float(r["p_pos"]),
            "abs_gross_le_0_25": True,  # N/A; path symmetry flag used instead
            "note": f"med_mfe={mfe:.4f} med_mae={mae:.4f} symmetric={sym}",
            "med_mfe_15": mfe,
            "med_mae_15": mae,
            "mfe_mae_symmetric": sym,
            "med_prog_close_15": float(r["med"]),
        }
    )

    v58 = json.loads((P58 / "event_c_verdict.json").read_text(encoding="utf-8"))
    d = v58["destination"]["detail"]["IS"]
    rows.append(
        {
            "strategy": "58",
            "name": "Event C destination",
            "kind": "destination_delta",
            "n_is": int(d["n_valid"]),
            "mean_gross_is": np.nan,
            "mean_net_is": np.nan,
            "hit_rate_is": np.nan,
            "abs_gross_le_0_25": True,
            "note": f"delta={d['delta']:.4f} wrong_sign",
            "delta": float(d["delta"]),
        }
    )

    fp = pd.read_csv(P59 / "first_passage_by_split.csv")
    f = fp.loc[fp["split"] == "IS"].iloc[0]
    rows.append(
        {
            "strategy": "59",
            "name": "ORB first-passage",
            "kind": "first_passage",
            "n_is": int(f["n"]),
            "mean_gross_is": np.nan,
            "mean_net_is": np.nan,
            "hit_rate_is": float(f["p_target_first"]),
            "abs_gross_le_0_25": True,
            "note": f"p_tgt={f['p_target_first']:.4f} p_adv={f['p_adverse_first']:.4f} dfp={f['delta_fp']:.4f}",
            "p_target_first": float(f["p_target_first"]),
            "p_adverse_first": float(f["p_adverse_first"]),
            "delta_fp": float(f["delta_fp"]),
        }
    )
    return pd.DataFrame(rows)


def orb_payoff_envelope() -> dict:
    events = pd.read_parquet(P59 / "orb_events.parquet")
    fp_paths = pd.read_parquet(P59 / "first_passage_paths.parquet")
    fp = pd.read_csv(P59 / "first_passage_by_split.csv")
    is_fp = fp.loc[fp["split"] == "IS"].iloc[0]

    # Approximate distances from event close to barriers using panel not available —
    # use geometry: up break close just above OR_high; target=OR_high+R → ~R;
    # adverse=OR_mid → ~0.5R from OR_high, slightly more from close outside.
    # Use R-based model: W = 1.0*R, L = 0.5*R (mid from high).
    R = events["R"].to_numpy(np.float64)
    med_R = float(np.median(R))
    W = 1.0 * med_R
    L = 0.5 * med_R
    p_star = (L + COST) / (W + L)
    p_obs = float(is_fp["p_target_first"])

    # Also resolve-only expectancy if we ignore unresolved (optimistic):
    # among resolved, p_tgt_res = p_tgt / (p_tgt+p_adv)
    p_t = float(is_fp["p_target_first"])
    p_a = float(is_fp["p_adverse_first"])
    p_res = p_t + p_a
    p_tgt_given_res = p_t / p_res if p_res > 0 else np.nan
    e_gross_model = p_t * W - p_a * L  # unresolved ~0 contribution if flat exit ~0
    # unresolved: model as 0 gross (time stop at entry+noise); already ~0 in 55/56

    # Empirical MAE on target-first from paths
    tgt = fp_paths.loc[fp_paths["hit_target_first"] & (fp_paths["split"] == "IS")]
    med_mae_tgt = float(tgt["mae_before_resolve"].median()) if len(tgt) else np.nan

    return {
        "med_R": med_R,
        "model_W": W,
        "model_L": L,
        "p_star_breakeven": p_star,
        "p_target_first_obs_IS": p_obs,
        "p_star_minus_obs": p_star - p_obs,
        "obs_below_breakeven": bool(p_obs < p_star),
        "p_target_given_resolved": p_tgt_given_res,
        "E_gross_model_IS_rates": e_gross_model,
        "E_net_model_IS_rates": e_gross_model - COST,
        "med_mae_on_target_first_IS": med_mae_tgt,
        "n_events_IS": int(is_fp["n"]),
        "note": "W=1R, L=0.5R from OR mid geometry; unresolved treated as ~0 gross",
    }


def classify(inv: pd.DataFrame, orb: dict, ladder_sym: bool) -> dict:
    r55 = inv.loc[inv["strategy"] == "55"].iloc[0]
    r56 = inv.loc[inv["strategy"] == "56"].iloc[0]
    r57 = inv.loc[inv["strategy"] == "57"].iloc[0]

    cond_gross = bool(r55["abs_gross_le_0_25"]) and bool(r56["abs_gross_le_0_25"])
    cond_sym = bool(r57.get("mfe_mae_symmetric", ladder_sym))
    cond_orb = bool(orb["obs_below_breakeven"])

    if cond_gross and cond_sym and cond_orb:
        verdict = "CLASS_STRUCTURALLY_UNDERWATER"
        reason = "55_56_gross_near_0+57_mfe_approx_mae+59_p_below_breakeven"
    elif (not cond_sym) and any(
        breakeven_grid().loc[
            (breakeven_grid()["W"] >= 6) & (breakeven_grid()["L"] <= 6),
            "clears_cost_at_p55",
        ]
    ):
        verdict = "NARROW_FEASIBLE_REGION"
        reason = "asymmetric_path_with_reachable_breakeven"
    else:
        verdict = "MIXED"
        reason = f"gross={cond_gross} sym={cond_sym} orb_under={cond_orb}"

    return {
        "classification": verdict,
        "reason": reason,
        "cost_rt": COST,
        "checks": {
            "55_56_abs_gross_le_0_25": cond_gross,
            "57_mfe_mae_symmetric_10pct": cond_sym,
            "59_p_target_below_p_star": cond_orb,
        },
        "action": (
            "MORATORIUM_simple_event_hold_and_1R_extension_mechanisms"
            if verdict == "CLASS_STRUCTURALLY_UNDERWATER"
            else "SEE_REPORT"
        ),
        "orb": orb,
    }


def write_report(grid: pd.DataFrame, inv: pd.DataFrame, orb: dict, verdict: dict) -> Path:
    lines = []
    lines.append("# Feasibility Report — Strategy 60 (Frame A)")
    lines.append("")
    lines.append("**Not a strategy.** Read-only over 55–59. Cost = 1.0 pt RT.")
    lines.append("")
    lines.append("## Verdict")
    lines.append("")
    lines.append(f"**`{verdict['classification']}`** — `{verdict['reason']}`")
    lines.append("")
    lines.append(f"**Action:** `{verdict['action']}`")
    lines.append("")
    lines.append("## Break-even intuition")
    lines.append("")
    lines.append("```text")
    lines.append("E[net] = p·W − (1−p)·L − 1.0")
    lines.append("p* = (L + 1) / (W + L)")
    lines.append("```")
    lines.append("")
    lines.append("If path is symmetric (MFE ≈ MAE, signed progress ≈ 0):")
    lines.append("")
    lines.append("```text")
    lines.append("E[gross] ≈ 0  ⇒  E[net] ≈ −1.0")
    lines.append("```")
    lines.append("")
    lines.append("### Grid excerpt (need E_net > 0 at p=55%)")
    lines.append("")
    sub = grid.loc[grid["clears_cost_at_p55"]]
    lines.append(f"Cells with p=55% clearing cost: **{len(sub)}** / {len(grid)}")
    lines.append("")
    if len(sub):
        lines.append("| W | L | p* | E_net@55% |")
        lines.append("| --- | --- | --- | --- |")
        for _, r in sub.head(12).iterrows():
            lines.append(
                f"| {int(r['W'])} | {int(r['L'])} | {r['p_star']:.3f} | {r['E_net_at_p55']:.2f} |"
            )
        lines.append("")
    else:
        lines.append("No grid cell with W,L≤20 clears +1pt at only 55% win rate unless W≫L.")
        lines.append("")

    # show a few instructive cells
    lines.append("### Instructive p*")
    lines.append("")
    lines.append("| W | L | p* (breakeven) |")
    lines.append("| --- | --- | --- |")
    for W, L in ((4, 4), (8, 8), (10, 5), (20, 10), (8, 4)):
        p = (L + COST) / (W + L)
        lines.append(f"| {W} | {L} | {p:.3f} |")
    lines.append("")

    lines.append("## Inventory 55–59")
    lines.append("")
    lines.append("| ID | name | kind | n_IS | mean_gross | mean_net | note |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for _, r in inv.iterrows():
        g = r["mean_gross_is"]
        n_ = r["mean_net_is"]
        gs = f"{g:.3f}" if pd.notna(g) else "—"
        ns = f"{n_:.3f}" if pd.notna(n_) else "—"
        lines.append(
            f"| {r['strategy']} | {r['name']} | {r['kind']} | {int(r['n_is'])} | {gs} | {ns} | {r['note']} |"
        )
    lines.append("")

    lines.append("## ORB-class payoff envelope (59 geometry)")
    lines.append("")
    lines.append(f"- Median R: **{orb['med_R']:.2f}**")
    lines.append(f"- Model W=1R, L=0.5R → W={orb['model_W']:.2f}, L={orb['model_L']:.2f}")
    lines.append(f"- Break-even p*: **{orb['p_star_breakeven']:.3f}**")
    lines.append(f"- Observed p_target_first (IS): **{orb['p_target_first_obs_IS']:.3f}**")
    lines.append(f"- Gap (p* − obs): **{orb['p_star_minus_obs']:.3f}**")
    lines.append(f"- Model E[net] at observed rates: **{orb['E_net_model_IS_rates']:.2f}**")
    lines.append("")
    lines.append("## Implication")
    lines.append("")
    if verdict["classification"] == "CLASS_STRUCTURALLY_UNDERWATER":
        lines.append(
            "The simple **event → fixed hold / 1R extension** class sits **below water** "
            "under 1.0 pt RT given measured path symmetry and first-passage rates."
        )
        lines.append("")
        lines.append("**Moratorium:** do not start another Strategy-61 event costume.")
        lines.append("Next allowed moves: Frame **B** (payoff-defined risk unit) or Frame **C** (refusal map) — only after explicit choice.")
    lines.append("")

    out = RESULTS / "FEASIBILITY_REPORT.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    grid = breakeven_grid()
    grid.to_csv(RESULTS / "breakeven_grid.csv", index=False)

    inv = inventory()
    # ensure mfe_mae column for classify
    r57 = inv.loc[inv["strategy"] == "57"].iloc[0]
    sym = bool(r57.get("mfe_mae_symmetric", False))
    if "mfe_mae_symmetric" not in inv.columns:
        inv["mfe_mae_symmetric"] = np.nan
        inv.loc[inv["strategy"] == "57", "mfe_mae_symmetric"] = sym

    inv.to_csv(RESULTS / "inventory_55_59.csv", index=False)

    orb = orb_payoff_envelope()
    (RESULTS / "orb_payoff_envelope.json").write_text(
        json.dumps(orb, indent=2), encoding="utf-8"
    )

    verdict = classify(inv, orb, sym)
    (RESULTS / "verdict.json").write_text(
        json.dumps(verdict, indent=2, default=str), encoding="utf-8"
    )

    path = write_report(grid, inv, orb, verdict)
    print(json.dumps({"classification": verdict["classification"], "action": verdict["action"], "orb_p_star": orb["p_star_breakeven"], "orb_p_obs": orb["p_target_first_obs_IS"]}, indent=2))
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
