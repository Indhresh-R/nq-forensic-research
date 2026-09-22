"""Write STEP4_MATCHED_TRANSITIONS.md."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
CODE = Path(__file__).resolve().parent
STRAT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(CODE))

from constants import RESULTS
from step3_constants import PRIMARY_HORIZON


def _md_table(df: pd.DataFrame, cols: list[str]) -> str:
    use = df[[c for c in cols if c in df.columns]]
    if use.empty:
        return "_(empty)_\n"
    headers = list(use.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for _, row in use.iterrows():
        cells = []
        for h in headers:
            v = row[h]
            if isinstance(v, float):
                cells.append(f"{v:.4f}" if abs(v) < 10 else f"{v:.3f}")
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def _pp(x) -> str:
    if pd.isna(x):
        return "n/a"
    return f"{100 * float(x):+.1f} pp"


def write_report() -> Path:
    est = pd.read_csv(RESULTS / "step4_matched_estimates.csv")
    bal = pd.read_csv(RESULTS / "step4_balance.csv")
    leave = pd.read_csv(RESULTS / "step4_leave_one_in.csv")
    cuts = json.loads((RESULTS / "step4_tercile_cuts_frozen.json").read_text(encoding="utf-8"))
    verdict = json.loads((RESULTS / "step4_verdict.json").read_text(encoding="utf-8"))
    audit = json.loads((RESULTS / "step4_audit.json").read_text(encoding="utf-8"))

    lines: list[str] = []
    a = lines.append

    a("# Step 4 — Matched transition experiment")
    a("")
    a("**Status:** Complete (mechanism description only).")
    a("**Parent:** Steps 0–3 frozen.")
    a("**Question:** After making C/D (and A/B) transitions more comparable on "
      "**pre-event geometry**, does destination asymmetry remain?")
    a("")
    a("This step does **not** claim causality, continuation/reversal, or a trade.")
    a("")
    a("---")
    a("")
    a("## Matching recipe (frozen CEM)")
    a("")
    a("`wait_stratum × volatility × volume × TOD × origin_run tercile × "
      "pre_range_atr tercile × pre_er tercile × dist_mid_atr tercile`")
    a("")
    a("Geometry terciles frozen on IS within family (see `step4_tercile_cuts_frozen.json`).")
    a("")
    for fam, block in cuts.get("families", {}).items():
        a(f"- **{fam}** cuts available for: {', '.join(block.keys())}")
    a("")
    a("---")
    a("")
    a(f"## Unmatched vs CEM estimates (primary horizon {PRIMARY_HORIZON}m)")
    a("")

    for tag, title in (
        ("ExpExit_C_vs_D", "ExpExit (primary): D − C"),
        ("CompExit_A_vs_B", "CompExit (secondary): B − A"),
    ):
        a(f"### {title}")
        a("")
        sub = est[(est["contrast_tag"] == tag) & (est["horizon"] == PRIMARY_HORIZON)]
        show = sub.copy()
        show["return"] = show["return_diff"].map(_pp)
        show["opposite"] = show["opposite_diff"].map(_pp)
        a(
            _md_table(
                show,
                [
                    "design",
                    "n_a",
                    "n_b",
                    "retained_frac",
                    "n_strata",
                    "return",
                    "opposite",
                ],
            )
        )

    a("Full table incl. 60m: `results/step4_matched_estimates.csv`.")
    a("")
    a("---")
    a("")
    a("## Covariate balance (SMD, treatment − control)")
    a("")
    for tag in ("ExpExit_C_vs_D", "CompExit_A_vs_B"):
        a(f"### {tag}")
        a("")
        sub = bal[bal["contrast_tag"] == tag]
        a(_md_table(sub, ["covariate", "smd_before", "smd_after", "mean_a_before", "mean_b_before", "mean_a_after", "mean_b_after"]))

    a("---")
    a("")
    a("## Leave-one-in diagnostics (drop one geometry tercile from CEM key)")
    a("")
    for tag in ("ExpExit_C_vs_D", "CompExit_A_vs_B"):
        a(f"### {tag}")
        a("")
        sub = leave[leave["contrast_tag"] == tag]
        show = sub.copy()
        show["return"] = show["return_diff"].map(_pp)
        show["opposite"] = show["opposite_diff"].map(_pp)
        a(_md_table(show, ["dropped_factor", "n_strata", "retained_frac", "return", "opposite"]))

    a("---")
    a("")
    a("## Predeclared classification")
    a("")
    for tag, block in verdict.get("contrasts", {}).items():
        cls = block.get("classification", {})
        a(f"### {tag}")
        a("")
        a(f"- **Overall:** `{cls.get('overall')}`")
        a(f"- **Interpretation hint:** `{block.get('interpretation_hint')}`")
        a(f"- Unmatched return diff: {_pp(block.get('unmatched', {}).get('return_diff'))}")
        a(f"- Matched return diff: {_pp(block.get('matched', {}).get('return_diff'))}")
        a(f"- Unmatched opposite diff: {_pp(block.get('unmatched', {}).get('opposite_diff'))}")
        a(f"- Matched opposite diff: {_pp(block.get('matched', {}).get('opposite_diff'))}")
        a(f"- Retained fraction: {block.get('matched', {}).get('retained_frac')}")
        a(f"- Outcome-C candidate factors: {block.get('outcome_C_candidate_factors')}")
        for ep, eb in (cls.get("endpoints") or {}).items():
            a(f"- `{ep}` class=`{eb.get('class')}` "
              f"ratio={eb.get('ratio_abs_matched_over_unmatched')}")
        a("")

    a("---")
    a("")
    a("## Leakage / scope audit")
    a("")
    a("```text")
    a(f"LOOKAHEAD_CHECK = {audit.get('LOOKAHEAD_CHECK')}")
    a(f"MATCHING_USES_POST_EVENT_INFO = {audit.get('MATCHING_USES_POST_EVENT_INFO')}")
    a(f"MATCHING_RECIPE_FROZEN = {audit.get('MATCHING_RECIPE_FROZEN')}")
    a(f"OUTCOME_DATA_USED = {audit.get('OUTCOME_DATA_USED')}")
    a(f"STRATEGY_DATA_USED = {audit.get('STRATEGY_DATA_USED')}")
    a("```")
    a("")
    a("---")
    a("")
    a("## STEP 4 VERDICT")
    a("")
    exp = verdict.get("contrasts", {}).get("ExpExit_C_vs_D", {})
    comp = verdict.get("contrasts", {}).get("CompExit_A_vs_B", {})
    a(f"- **ExpExit (primary):** `{exp.get('classification', {}).get('overall')}` "
      f"/ hint `{exp.get('interpretation_hint')}`.")
    a(f"- **CompExit (secondary):** `{comp.get('classification', {}).get('overall')}` "
      f"/ hint `{comp.get('interpretation_hint')}`.")
    a("- **Wording discipline:** surviving matched differences mean the origin cell still "
      "associates with destination behavior after coarsened pre-event geometry matching — "
      "not that we have identified a causal range-recycling mechanism, and not that a side "
      "should be traded.")
    a("- **Still forbidden:** continuation/reversal trade labels; P&L; optimizing the match.")
    a("")
    a("## NEXT RESEARCH QUESTION")
    a("")
    a("Given the Step 4 classification, what is the smallest *additional* pre-event "
      "structural feature (still frozen before outcomes) needed to decide whether the "
      "residual association is better described as **directionality-at-exit** vs "
      "**geometry-not-yet-matched** — without introducing a directional trade hypothesis?")
    a("")
    a("_Do not answer by building a strategy in this step._")
    a("")

    out = STRAT / "STEP4_MATCHED_TRANSITIONS.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


if __name__ == "__main__":
    print(f"Wrote {write_report()}")
