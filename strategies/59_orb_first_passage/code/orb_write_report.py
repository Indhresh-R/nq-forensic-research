"""Write Strategy 59 ORB first-passage report."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(CODE))

from constants import RESULTS


def write_report() -> Path:
    funnel = json.loads((RESULTS / "funnel.json").read_text(encoding="utf-8"))
    fp = pd.read_csv(RESULTS / "first_passage_by_split.csv")
    timing = pd.read_csv(RESULTS / "time_to_resolve.csv")
    verdict = json.loads((RESULTS / "verdict.json").read_text(encoding="utf-8"))
    audit = json.loads((RESULTS / "audit.json").read_text(encoding="utf-8"))

    lines: list[str] = []
    lines.append("# ORB First-Passage Report — Strategy 59")
    lines.append("")
    lines.append(
        "**Target + adverse co-defined.** Not Event D. No 52–58 reopen. No horizon shopping."
    )
    lines.append("")
    lines.append("## Funnel")
    lines.append("")
    for k, v in funnel.items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## Freeze / audit")
    lines.append("")
    lines.append("```text")
    lines.append(f"LOOKAHEAD_CHECK = {audit.get('LOOKAHEAD_CHECK')}")
    lines.append(f"TARGET_ADVERSE_CO_DEFINED = {audit.get('TARGET_ADVERSE_CO_DEFINED')}")
    lines.append(f"NO_PARAMETER_RETUNE = {audit.get('NO_PARAMETER_RETUNE')}")
    lines.append(f"NO_52_58_REOPEN = {audit.get('NO_52_58_REOPEN')}")
    lines.append("```")
    lines.append("")
    lines.append("## Step 1 — First-passage")
    lines.append("")
    lines.append(
        "| split | n | p_target_first | p_adverse_first | p_unresolved | delta_fp |"
    )
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for _, r in fp.iterrows():
        lines.append(
            "| {split} | {n} | {pt:.4f} | {pa:.4f} | {pu:.4f} | {d:.4f} |".format(
                split=r["split"],
                n=int(r["n"]),
                pt=float(r["p_target_first"]),
                pa=float(r["p_adverse_first"]),
                pu=float(r["p_unresolved"]),
                d=float(r["delta_fp"]),
            )
        )
    s1 = verdict["step1"]
    lines.append("")
    lines.append(f"- **Classification:** `{s1.get('classification')}`")
    lines.append(f"- **Reason:** `{s1.get('reason')}`")
    lines.append("")

    s2 = verdict.get("step2")
    if s2:
        mae = pd.read_csv(RESULTS / "mae_before_target_by_split.csv")
        lines.append("## Step 2 — MAE before target")
        lines.append("")
        lines.append(
            "| split | n_target_first | med_mae | med_mae/R | p75_mae | pass_R | pass_pts |"
        )
        lines.append("| --- | --- | --- | --- | --- | --- | --- |")
        for _, r in mae.iterrows():
            lines.append(
                "| {split} | {n} | {m:.4f} | {mr:.4f} | {p75:.4f} | {pr} | {pp} |".format(
                    split=r["split"],
                    n=int(r["n_target_first"]),
                    m=float(r["med_mae"]),
                    mr=float(r["med_mae_over_R"]),
                    p75=float(r["p75_mae"]),
                    pr=bool(r["pass_mae_r"]),
                    pp=bool(r["pass_mae_pts"]),
                )
            )
        lines.append("")
        lines.append(f"- **Classification:** `{s2.get('classification')}`")
        lines.append(f"- **Reason:** `{s2.get('reason')}`")
        lines.append("")
    else:
        lines.append("## Step 2 — MAE")
        lines.append("")
        lines.append("Not run (Step 1 did not advance).")
        lines.append("")

    lines.append("## Step 3 — Time to resolve (descriptive)")
    lines.append("")
    lines.append("| split | outcome | n | med_bars | p25 | p75 |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for _, r in timing.iterrows():
        lines.append(
            "| {split} | {outcome} | {n} | {med:.1f} | {p25:.1f} | {p75:.1f} |".format(
                split=r["split"],
                outcome=r["outcome"],
                n=int(r["n"]),
                med=float(r["med_bars"]) if pd.notna(r["med_bars"]) else float("nan"),
                p25=float(r["p25"]) if pd.notna(r["p25"]) else float("nan"),
                p75=float(r["p75"]) if pd.notna(r["p75"]) else float("nan"),
            )
        )
    lines.append("")

    tv = verdict.get("trade")
    if tv:
        ts = pd.read_csv(RESULTS / "trade_summary.csv")
        lines.append("## Step 4 — Trade")
        lines.append("")
        lines.append(
            "Entry `open[t+1]`; exit first target/adverse (same-bar → adverse); else `close[t+H_cap]`; cost 1.0 pt RT."
        )
        lines.append("")
        lines.append(
            "| split | n_trades | mean_gross | mean_net | median_net | hit_rate | eligible |"
        )
        lines.append("| --- | --- | --- | --- | --- | --- | --- |")
        for _, r in ts.iterrows():
            lines.append(
                "| {split} | {n} | {g:.4f} | {net:.4f} | {med:.4f} | {hr:.4f} | {el} |".format(
                    split=r["split"],
                    n=int(r["n_trades"]),
                    g=float(r["mean_gross"]),
                    net=float(r["mean_net"]),
                    med=float(r["median_net"]),
                    hr=float(r["hit_rate"]),
                    el=bool(r["eligible"]),
                )
            )
        lines.append("")
        lines.append(f"**Trade classification:** `{tv.get('classification')}`")
        lines.append("")
    else:
        lines.append("## Step 4 — Trade")
        lines.append("")
        lines.append("Not run.")
        lines.append("")

    lines.append("## STRATEGY 59 FINAL")
    lines.append("")
    lines.append(
        f"**{verdict.get('final')}**. Do not retune W_or / target / adverse. Do not reopen 52–58."
    )
    lines.append("")

    out = RESULTS / "ORB_FIRST_PASSAGE_REPORT.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


if __name__ == "__main__":
    print(write_report())
