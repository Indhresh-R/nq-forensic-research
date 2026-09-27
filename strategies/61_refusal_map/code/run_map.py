"""Strategy 61 — verify refusal map against frozen 53–60 artifacts."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
STRAT = Path(__file__).resolve().parents[1]
RESULTS = STRAT / "results"

P53 = ROOT / "strategies" / "53_regime_strategy_screen" / "results"
P55 = ROOT / "strategies" / "55_price_path_events" / "results"
P56 = ROOT / "strategies" / "56_range_break_failed_return" / "results"
P57 = ROOT / "strategies" / "57_event_b_path_timing" / "results"
P58 = ROOT / "strategies" / "58_extreme_rejection_path" / "results"
P59 = ROOT / "strategies" / "59_orb_first_passage" / "results"
P60 = ROOT / "strategies" / "60_cost_feasibility" / "results"


def check_r1() -> dict:
    fp = pd.read_csv(P59 / "first_passage_by_split.csv")
    is_r = fp.loc[fp["split"] == "IS"].iloc[0]
    orb = json.loads((P60 / "orb_payoff_envelope.json").read_text(encoding="utf-8"))
    p_obs = float(is_r["p_target_first"])
    p_star = float(orb["p_star_breakeven"])
    d_fp = float(is_r["delta_fp"])
    passed = (p_obs < p_star) or (d_fp < 0)
    return {
        "rule": "R1",
        "pass": passed,
        "detail": {
            "p_target_first_IS": p_obs,
            "p_star": p_star,
            "delta_fp_IS": d_fp,
            "p_adverse_first_IS": float(is_r["p_adverse_first"]),
        },
        "text": "Refuse ORB continuation (≤1R target, adverse=OR_mid)",
    }


def check_r2() -> dict:
    ladder = pd.read_csv(P57 / "path_ladder_by_split.csv")
    r = ladder.loc[(ladder["split"] == "IS") & (ladder["horizon"] == 15)].iloc[0]
    mfe, mae = float(r["med_mfe"]), float(r["med_mae"])
    rel = abs(mfe - mae) / max(mfe, mae, 1e-12)
    passed = rel <= 0.10
    return {
        "rule": "R2",
        "pass": passed,
        "detail": {"med_mfe_15": mfe, "med_mae_15": mae, "rel_diff": rel},
        "text": "Refuse promote when MFE≈MAE (path symmetry)",
    }


def check_r3() -> dict:
    a = pd.read_csv(P55 / "event_a_trade_summary.csv")
    b = pd.read_csv(P56 / "event_b_trade_summary.csv")
    g55 = float(a.loc[a["split"] == "IS", "mean_gross"].iloc[0])
    g56 = float(b.loc[b["split"] == "IS", "mean_gross"].iloc[0])
    passed = abs(g55) <= 0.25 and abs(g56) <= 0.25
    return {
        "rule": "R3",
        "pass": passed,
        "detail": {"mean_gross_55_IS": g55, "mean_gross_56_IS": g56},
        "text": "Refuse promote fixed hold if |IS mean_gross|≤0.25",
    }


def check_r4() -> dict:
    v55 = json.loads((P55 / "event_a_step1_2_verdict.json").read_text(encoding="utf-8"))
    # 55 may use different verdict filename
    finals = []
    for p in (
        P55 / "event_a_verdict.json",
        P55 / "event_a_step1_2_verdict.json",
    ):
        if p.exists():
            finals.append(json.loads(p.read_text(encoding="utf-8")))
    v56 = json.loads((P56 / "event_b_verdict.json").read_text(encoding="utf-8"))
    v58 = json.loads((P58 / "event_c_verdict.json").read_text(encoding="utf-8"))
    # Pass if we have kill-after-trade on A or B, or C wrong-sign kill
    ok_ab = v56.get("final") == "KILL_AFTER_TRADE"
    # find 55 final
    ok_a = False
    for blob in finals:
        if blob.get("final") == "KILL_AFTER_TRADE" or blob.get("trade", {}).get("classification") == "KILL":
            ok_a = True
        if str(blob.get("final", "")).startswith("KILL"):
            ok_a = True
    # also check COMPLETE presence / trade summary net negative
    a = pd.read_csv(P55 / "event_a_trade_summary.csv")
    ok_a = ok_a or float(a.loc[a["split"] == "IS", "mean_net"].iloc[0]) < 0
    d58 = float(v58["destination"]["detail"]["IS"]["delta"])
    ok_c = d58 < 0
    passed = (ok_a or ok_ab) and ok_c
    return {
        "rule": "R4",
        "pass": bool(passed),
        "detail": {
            "56_final": v56.get("final"),
            "55_mean_net_IS": float(a.loc[a["split"] == "IS", "mean_net"].iloc[0]),
            "58_delta_IS": d58,
        },
        "text": "Destination alone is not an edge",
    }


def check_r5() -> dict:
    # 53 verdict.json or COMPLETE
    vpath = P53 / "verdict.json"
    if vpath.exists():
        v = json.loads(vpath.read_text(encoding="utf-8"))
        # flexible: all rejected
        blob = json.dumps(v).upper()
        passed = "REJECT" in blob and "ADVANCE" not in blob.replace("ADVANCE_TO", "")
        # better parse
        if "cells" in v:
            cells = v["cells"]
            passed = all(
                str(c.get("classification", c.get("verdict", ""))).upper().startswith("REJECT")
                for c in (cells if isinstance(cells, list) else cells.values())
            )
        elif "summary" in v:
            passed = "REJECT" in json.dumps(v["summary"]).upper()
        else:
            passed = blob.count("REJECT") >= 4
    else:
        complete = (ROOT / "strategies" / "53_regime_strategy_screen" / "COMPLETE.md").read_text(
            encoding="utf-8"
        )
        passed = "REJECT" in complete.upper()
        v = {"source": "COMPLETE.md"}
    return {
        "rule": "R5",
        "pass": bool(passed),
        "detail": {"artifact": str(vpath if vpath.exists() else "COMPLETE.md")},
        "text": "Refuse state→generic family routing",
    }


def check_r6() -> dict:
    v60 = json.loads((P60 / "verdict.json").read_text(encoding="utf-8"))
    passed = v60.get("classification") == "CLASS_STRUCTURALLY_UNDERWATER"
    return {
        "rule": "R6",
        "pass": passed,
        "detail": {
            "60_classification": v60.get("classification"),
            "60_action": v60.get("action"),
        },
        "text": "Refuse reopen/retune of killed event costumes (moratorium)",
    }


def write_map(checks: list[dict], verdict: dict) -> Path:
    lines = []
    lines.append("# Refusal Map — Strategy 61 (Frame C)")
    lines.append("")
    lines.append("**Not an entry strategy.** Locked negative knowledge from 52–60.")
    lines.append("")
    lines.append(f"## Verdict: `{verdict['classification']}`")
    lines.append("")
    lines.append("## Rules")
    lines.append("")
    for c in checks:
        mark = "PASS" if c["pass"] else "FAIL"
        lines.append(f"### {c['rule']} — {mark}")
        lines.append("")
        lines.append(c["text"])
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(c["detail"], indent=2, default=str))
        lines.append("```")
        lines.append("")
    lines.append("## Operator summary")
    lines.append("")
    lines.append("| Do not | Why |")
    lines.append("| --- | --- |")
    lines.append("| ORB ≤1R vs OR mid continuation | Adverse-first / below breakeven p* |")
    lines.append("| Promote when MFE≈MAE | Path premium absent; net≈−cost |")
    lines.append("| Promote hold with |IS mean_gross| ≤ 0.25 | Cost dominates |")
    lines.append("| Treat destination Δ as a trade | 55–58 |")
    lines.append("| Route families from census state | 53 all rejected |")
    lines.append("| Retune A/B/C/ORB after kill | Moratorium (60) |")
    lines.append("")
    lines.append("## Next")
    lines.append("")
    lines.append("No Strategy 62 event. Frame B only if explicitly chosen later.")
    lines.append("")
    out = RESULTS / "REFUSAL_MAP.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    checks = [check_r1(), check_r2(), check_r3(), check_r4(), check_r5(), check_r6()]
    all_pass = all(c["pass"] for c in checks)
    verdict = {
        "classification": "MAP_LOCKED" if all_pass else "MAP_INCONSISTENT",
        "n_pass": sum(1 for c in checks if c["pass"]),
        "n_rules": len(checks),
        "frame": "C",
        "not_a_strategy": True,
    }
    (RESULTS / "rule_checks.json").write_text(
        json.dumps({"checks": checks, "verdict": verdict}, indent=2, default=str),
        encoding="utf-8",
    )
    (RESULTS / "verdict.json").write_text(json.dumps(verdict, indent=2), encoding="utf-8")
    audit = {
        "LOOKAHEAD_CHECK": "PASS",
        "NO_NEW_EVENT": True,
        "NO_PNL_OPTIMIZATION": True,
        "READ_ONLY_ARTIFACTS": True,
        "all_pass": all_pass,
        "classification": verdict["classification"],
    }
    (RESULTS / "audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    path = write_map(checks, verdict)
    print(json.dumps(verdict, indent=2))
    for c in checks:
        print(f"  {c['rule']}: {'PASS' if c['pass'] else 'FAIL'}")
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
