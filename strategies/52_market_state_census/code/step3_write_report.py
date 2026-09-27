"""Write STEP3_DESTINATION_STABILITY.md."""
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
from step3_constants import MIN_N_VALID, PRIMARY_HORIZON, SECONDARY_HORIZON


def _md_table(df: pd.DataFrame, cols: list[str]) -> str:
    use = df[[c for c in cols if c in df.columns]].copy()
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
                if abs(v) <= 1.5:
                    cells.append(f"{v:.4f}")
                else:
                    cells.append(f"{v:.3f}")
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def _pct(x) -> str:
    if pd.isna(x):
        return "n/a"
    return f"{100 * float(x):.1f}%"


def write_report() -> Path:
    cuts = json.loads((RESULTS / "step3_wait_cuts_frozen.json").read_text(encoding="utf-8"))
    split = pd.read_csv(RESULTS / "step3_split_stability.csv")
    wait = pd.read_csv(RESULTS / "step3_wait_strata.csv")
    orth = pd.read_csv(RESULTS / "step3_orthogonal.csv")
    verdict = json.loads((RESULTS / "step3_verdict.json").read_text(encoding="utf-8"))
    audit = json.loads((RESULTS / "step3_audit.json").read_text(encoding="utf-8"))

    lines: list[str] = []
    a = lines.append

    a("# Step 3 — Destination asymmetry: stability + orthogonal conditioning")
    a("")
    a("**Status:** Complete (mechanism description only).")
    a("**Parent:** Steps 0–2 frozen.")
    a("**Focus:** destination / recycling after →NORMAL — **not** magnitude, **not** trading.")
    a("")
    a(f"Primary horizon: **{PRIMARY_HORIZON}m**. Secondary: **{SECONDARY_HORIZON}m**. "
      f"Minimum n per origin cell for eligible claims: **{MIN_N_VALID}**.")
    a("")
    a("---")
    a("")
    a("## Frozen wait terciles (IS only, before destination stratification)")
    a("")
    for fam, block in cuts.get("families", {}).items():
        a(f"- **{fam}**: n_IS={block.get('n_is')}, "
          f"q33={block.get('q33')}, q67={block.get('q67')}")
    a("")
    a("---")
    a("")
    a("## 1. Chronological split stability")
    a("")
    a("Differences are B−A for CompExit and D−C for ExpExit.")
    a("")

    for tag, title in (
        ("CompExit_A_vs_B", "CompExit: A→NORMAL vs B→NORMAL"),
        ("ExpExit_C_vs_D", "ExpExit: C→NORMAL vs D→NORMAL"),
    ):
        a(f"### {title}")
        a("")
        sub = split[(split["contrast_tag"] == tag) & (split["horizon"] == PRIMARY_HORIZON)]
        show = sub.copy()
        show["return_a"] = show["return_rate_a"].map(_pct)
        show["return_b"] = show["return_rate_b"].map(_pct)
        show["return_diff_pp"] = (show["return_diff"] * 100).map(
            lambda x: f"{x:+.1f}" if pd.notna(x) else "n/a"
        )
        show["opp_a"] = show["opposite_rate_a"].map(_pct)
        show["opp_b"] = show["opposite_rate_b"].map(_pct)
        show["opp_diff_pp"] = (show["opposite_diff"] * 100).map(
            lambda x: f"{x:+.1f}" if pd.notna(x) else "n/a"
        )
        a(
            _md_table(
                show,
                [
                    "slice",
                    "n_a",
                    "n_b",
                    "eligible",
                    "return_a",
                    "return_b",
                    "return_diff_pp",
                    "opp_a",
                    "opp_b",
                    "opp_diff_pp",
                ],
            )
        )

    a("Secondary horizon tables: `results/step3_split_stability.csv`.")
    a("")
    a("---")
    a("")
    a("## 2. Wait-to-NORMAL stratification (confounder diagnostic)")
    a("")
    for tag, title in (
        ("CompExit_A_vs_B", "CompExit"),
        ("ExpExit_C_vs_D", "ExpExit"),
    ):
        a(f"### {title}")
        a("")
        sub = wait[(wait["contrast_tag"] == tag) & (wait["horizon"] == PRIMARY_HORIZON)]
        show = sub.copy()
        show["return_diff_pp"] = (show["return_diff"] * 100).map(
            lambda x: f"{x:+.1f}" if pd.notna(x) else "n/a"
        )
        show["opp_diff_pp"] = (show["opposite_diff"] * 100).map(
            lambda x: f"{x:+.1f}" if pd.notna(x) else "n/a"
        )
        a(
            _md_table(
                show,
                [
                    "wait_stratum",
                    "n_a",
                    "n_b",
                    "eligible",
                    "return_diff_pp",
                    "opp_diff_pp",
                    "return_rate_a",
                    "return_rate_b",
                    "opposite_rate_a",
                    "opposite_rate_b",
                ],
            )
        )

    a("---")
    a("")
    a("## 3. Orthogonal conditioning (one covariate at a time)")
    a("")
    a("Event-bar only. No crossed combinations.")
    a("")
    for tag, title in (
        ("CompExit_A_vs_B", "CompExit"),
        ("ExpExit_C_vs_D", "ExpExit"),
    ):
        a(f"### {title}")
        a("")
        for cov in ("volatility_state", "volume_state", "tod_block"):
            a(f"#### {cov}")
            a("")
            sub = orth[
                (orth["contrast_tag"] == tag)
                & (orth["covariate"] == cov)
                & (orth["horizon"] == PRIMARY_HORIZON)
            ]
            show = sub.copy()
            show["return_diff_pp"] = (show["return_diff"] * 100).map(
                lambda x: f"{x:+.1f}" if pd.notna(x) else "n/a"
            )
            show["opp_diff_pp"] = (show["opposite_diff"] * 100).map(
                lambda x: f"{x:+.1f}" if pd.notna(x) else "n/a"
            )
            a(
                _md_table(
                    show,
                    [
                        "level",
                        "n_a",
                        "n_b",
                        "eligible",
                        "return_diff_pp",
                        "opp_diff_pp",
                    ],
                )
            )

    a("---")
    a("")
    a("## Predeclared criteria checklist")
    a("")
    for tag, block in verdict.get("contrasts", {}).items():
        a(f"### {tag}")
        a("")
        a(f"- **Interesting (either endpoint):** {block.get('interesting')}")
        for ep in ("return_to_origin", "reach_opposite"):
            b = block.get(ep) or {}
            a(f"- **{ep}:** pass={b.get('pass')}; "
              f"pooled={b.get('present_pooled')}; "
              f"same_sign_splits={b.get('same_sign_across_splits')}; "
              f"not_wait_only={b.get('not_wait_confound_only')}; "
              f"not_tiny_only={b.get('not_tiny_subgroup_only')}; "
              f"pooled_diff={b.get('pooled_diff')}")
        a("")

    a("---")
    a("")
    a("## Leakage / scope audit")
    a("")
    a("```text")
    a(f"LOOKAHEAD_CHECK = {audit.get('LOOKAHEAD_CHECK')}")
    a(f"WAIT_CUTS_FROZEN_BEFORE_DESTINATION_CLAIMS = {audit.get('WAIT_CUTS_FROZEN_BEFORE_DESTINATION_CLAIMS')}")
    a(f"COVARIATES_AT_EVENT_BAR_ONLY = {audit.get('COVARIATES_AT_EVENT_BAR_ONLY')}")
    a(f"OUTCOME_DATA_USED = {audit.get('OUTCOME_DATA_USED')}")
    a(f"STRATEGY_DATA_USED = {audit.get('STRATEGY_DATA_USED')}")
    a("```")
    a("")
    a("---")
    a("")
    a("## STEP 3 VERDICT")
    a("")

    comp = verdict.get("contrasts", {}).get("CompExit_A_vs_B", {})
    exp = verdict.get("contrasts", {}).get("ExpExit_C_vs_D", {})

    a(f"- **CompExit destination asymmetry:** interesting={comp.get('interesting')} "
      f"(return pass={comp.get('return_to_origin', {}).get('pass')}, "
      f"opposite pass={comp.get('reach_opposite', {}).get('pass')}).")
    a(f"- **ExpExit destination asymmetry:** interesting={exp.get('interesting')} "
      f"(return pass={exp.get('return_to_origin', {}).get('pass')}, "
      f"opposite pass={exp.get('reach_opposite', {}).get('pass')}).")
    a("- Criteria require pooled presence, same sign across eligible chronological splits, "
      "breadth beyond a single tiny subgroup, and survival under wait stratification.")
    a("- Orthogonal tables are descriptive supports for the same question — not a search "
      "for the largest cell.")
    a("- **Still not a strategy.** Surviving asymmetries are mechanism leads only.")
    a("")
    a("## NEXT RESEARCH QUESTION")
    a("")
    a("If any Step 3 destination asymmetry is marked interesting, is it best understood as "
      "a **range-recycling mechanism** that should next be tested with a *matched* wait "
      "design (or wait-conditioned event definition) before any directional trade hypothesis? "
      "If none survive, which frozen orthogonal dimension at the event bar shows the most "
      "*stable* within-family destination separation — still without constructing a trade?")
    a("")
    a("_Do not answer by building a strategy in this step._")
    a("")

    out = STRAT / "STEP3_DESTINATION_STABILITY.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


if __name__ == "__main__":
    print(f"Wrote {write_report()}")
