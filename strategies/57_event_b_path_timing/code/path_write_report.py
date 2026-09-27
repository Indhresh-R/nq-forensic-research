"""Write Strategy 57 path-timing report."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(CODE))

from constants import HORIZONS, RESULTS


def write_report() -> Path:
    ladder = pd.read_csv(RESULTS / "path_ladder_by_split.csv")
    fr = pd.read_csv(RESULTS / "first_rebreak_timing.csv")
    verdict = json.loads((RESULTS / "path_verdict.json").read_text(encoding="utf-8"))
    audit = json.loads((RESULTS / "audit.json").read_text(encoding="utf-8"))

    lines: list[str] = []
    lines.append("# Path Timing Report — Event B (Strategy 57)")
    lines.append("")
    lines.append("**Path/timing only.** No P&L. No horizon shopping. Not a monetization rescue.")
    lines.append("")
    lines.append("## Freeze / audit")
    lines.append("")
    lines.append("```text")
    lines.append(f"LOOKAHEAD_CHECK = {audit.get('LOOKAHEAD_CHECK')}")
    lines.append(f"EVENT_DEFINITION_FROZEN = {audit.get('EVENT_DEFINITION_FROZEN')}")
    lines.append(f"NO_PARAMETER_RETUNE = {audit.get('NO_PARAMETER_RETUNE')}")
    lines.append(f"NO_HORIZON_PNL_SHOP = {audit.get('NO_HORIZON_PNL_SHOP')}")
    lines.append(f"NO_TRADE_IN_THIS_RUN = {audit.get('NO_TRADE_IN_THIS_RUN')}")
    lines.append("```")
    lines.append("")
    lines.append(f"Predicted side (inherited): `{verdict.get('predicted_side_rule')}`")
    lines.append("")
    lines.append("## Primary ladder — `prog_close[H] = side × (close[t+H] − close[t]) / R`")
    lines.append("")
    lines.append("| split | horizon | n | med | mean | p_pos | p_hit_rebreak | med_mfe | med_mae |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for _, r in ladder.iterrows():
        lines.append(
            "| {split} | {horizon} | {n} | {med:.4f} | {mean:.4f} | {p_pos:.4f} | "
            "{p_hit_rebreak:.4f} | {med_mfe:.4f} | {med_mae:.4f} |".format(
                split=r["split"],
                horizon=int(r["horizon"]),
                n=int(r["n"]),
                med=float(r["med"]),
                mean=float(r["mean"]),
                p_pos=float(r["p_pos"]),
                p_hit_rebreak=float(r["p_hit_rebreak"]),
                med_mfe=float(r["med_mfe"]),
                med_mae=float(r["med_mae"]),
            )
        )
    lines.append("")
    lines.append("## First rebreak timing (descriptive)")
    lines.append("")
    lines.append(
        "| split | n_h60_valid | n_hit_by_60 | med_first_bars | p25 | p75 |"
    )
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for _, r in fr.iterrows():
        lines.append(
            "| {split} | {n_valid} | {n_hit} | {med:.1f} | {p25:.1f} | {p75:.1f} |".format(
                split=r["split"],
                n_valid=int(r["n_events_h60_valid"]),
                n_hit=int(r["n_hit_rebreak_by_60"]),
                med=float(r["med_first_rebreak_bars"]),
                p25=float(r["p25_first_rebreak_bars"]),
                p75=float(r["p75_first_rebreak_bars"]),
            )
        )
    lines.append("")
    lines.append("## Gate detail")
    lines.append("")
    for split in ("IS", "Validation", "OOS"):
        d = verdict["detail"][split]
        meds = " → ".join(f"{h}:{d['med'][str(h)]:.4f}" for h in HORIZONS)
        lines.append(
            f"- **{split}**: n_ok={d['n_ok']}, mono={d['mono']}, "
            f"med60_pos={d['med60_pos']}, mid_ladder_pos={d.get('mid_ladder_pos', 'n/a')}; "
            f"medians [{meds}]"
        )
    lines.append("")
    lines.append("## Verdict")
    lines.append("")
    lines.append(f"- **Classification:** `{verdict['classification']}`")
    lines.append(f"- **Stage:** `{verdict['stage']}`")
    lines.append(f"- **Reason:** `{verdict['reason']}`")
    lines.append("")
    if verdict["classification"] == "PATH_ADVANCE":
        lines.append(
            "Path ADVANCE only. **Do not trade yet.** Monetization requires a separate prereg."
        )
    else:
        lines.append(
            "Path KILL. **Do not shop horizons for P&L.** Do not retune Event B. "
            "Do not open Family 3/4 as a rescue."
        )
    lines.append("")

    out = RESULTS / "PATH_TIMING_REPORT.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


if __name__ == "__main__":
    print(write_report())
