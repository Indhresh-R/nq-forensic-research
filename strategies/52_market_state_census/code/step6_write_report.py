"""Write STEP6_DIRECTIONALITY_DECOMPOSITION.md."""
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
                cells.append(f"{v:.4f}" if abs(v) < 100 else f"{v:.3f}")
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def _pp(x) -> str:
    if pd.isna(x):
        return "n/a"
    return f"{100 * float(x):+.1f} pp"


def write_report() -> Path:
    bal = pd.read_csv(RESULTS / "step6_balance.csv")
    within = pd.read_csv(RESULTS / "step6_within_bin_contrasts.csv")
    mono = pd.read_csv(RESULTS / "step6_monotonicity.csv")
    cuts = json.loads((RESULTS / "step6_cuts_frozen.json").read_text(encoding="utf-8"))
    verdict = json.loads((RESULTS / "step6_verdict.json").read_text(encoding="utf-8"))
    audit = json.loads((RESULTS / "step6_audit.json").read_text(encoding="utf-8"))

    lines: list[str] = []
    a = lines.append

    a("# Step 6 — Directionality mechanism decomposition (ExpExit)")
    a("")
    a("**Status:** Complete (mechanism decomposition audit).")
    a("**Scope:** ExpExit C vs D only. No trade. No new CEM.")
    a("")
    a("Primary measurements at the **event bar `te`** (first NORMAL), where C/D are not "
      "forced into disjoint ER bands by construction.")
    a("")
    a(f"Sanity: `tm_er60` C_min={verdict.get('tm_er60_c_min')}, "
      f"D_max={verdict.get('tm_er60_d_max')} (pre-event bands expected disjoint).")
    a("")
    a("---")
    a("")
    a("## Component balance at transition (D − C SMD)")
    a("")
    a(_md_table(bal, ["component", "mean_c", "mean_d", "smd_d_minus_c", "n_c_finite", "n_d_finite"]))
    a("")
    a("---")
    a("")
    a(f"## Within-bin D−C destination contrasts (horizon {PRIMARY_HORIZON}m)")
    a("")
    for feat in ("te_er_60", "te_path_60", "te_abs_net_60", "er_60_change", "te_signed_net_5"):
        a(f"### {feat}")
        a("")
        q = cuts.get("features", {}).get(feat, {})
        a(f"IS cuts: q33={q.get('q33')}, q67={q.get('q67')}")
        a("")
        sub = within[
            (within["feature"] == feat) & (within["horizon"] == PRIMARY_HORIZON)
        ].copy()
        sub["return"] = sub["return_diff"].map(_pp)
        sub["opposite"] = sub["opposite_diff"].map(_pp)
        a(_md_table(sub, ["bin", "n_c", "n_d", "eligible", "mean_feature_c", "mean_feature_d", "return", "opposite"]))
        a("")

    a("---")
    a("")
    a("## Within-cell monotonicity (descriptive)")
    a("")
    a(_md_table(mono[mono["feature"] == "te_er_60"], ["origin_cell", "bin", "n", "mean_feature", "return_rate", "opposite_rate"]))
    a("")
    a("---")
    a("")
    a("## Predeclared classification")
    a("")
    a(f"- **Classification:** `{verdict.get('classification')}`")
    a(f"- Primary `te_er_60` class: `{verdict.get('primary_er60_te_class')}`")
    a(f"- PATH_OR_NET feature (if any): `{verdict.get('path_or_net_feature')}`")
    a("")
    for d in verdict.get("detail") or []:
        a(
            f"- `{d.get('bin')}`: return={_pp(d.get('return_diff'))}, "
            f"opposite={_pp(d.get('opposite_diff'))}, "
            f"keeps=({d.get('return_keeps')},{d.get('opposite_keeps')})"
        )
    a("")
    a("---")
    a("")
    a("## Leakage / scope audit")
    a("")
    a("```text")
    a(f"LOOKAHEAD_CHECK = {audit.get('LOOKAHEAD_CHECK')}")
    a(f"POST_EVENT_INFO_IN_COMPONENTS = {audit.get('POST_EVENT_INFO_IN_COMPONENTS')}")
    a(f"SCOPE_EXPEXIT_ONLY = {audit.get('SCOPE_EXPEXIT_ONLY')}")
    a(f"OUTCOME_DATA_USED = {audit.get('OUTCOME_DATA_USED')}")
    a(f"STRATEGY_DATA_USED = {audit.get('STRATEGY_DATA_USED')}")
    a("```")
    a("")
    a("---")
    a("")
    a("## STEP 6 VERDICT")
    a("")
    cls = verdict.get("classification")
    if cls == "LABEL_RESIDUAL":
        a("- Within comparable `ER_60` at the NORMAL bar, the ExpExit C/D destination "
          "asymmetry **remains**. The origin cell still **associates** with destination "
          "beyond contemporaneous transition ER — still not a proven causal mechanism, "
          "and not a trade.")
    elif cls == "COMPONENT_ACCOUNTS":
        a("- Within comparable `ER_60` at the NORMAL bar, the ExpExit C/D destination "
          "asymmetry **collapses**. The residual association is largely the "
          "**transition ER level**, not an extra composite-label effect.")
    elif cls == "CONDITIONAL":
        a("- The ExpExit C/D destination link is **conditional on transition-ER regime**: "
          "it remains in the low-`ER_60[te]` band and collapses in the mid-overlap band "
          "(high band typically underpowered for D).")
    elif cls == "PATH_OR_NET":
        a(f"- Primary ER strata do not remove the label residual, but "
          f"`{verdict.get('path_or_net_feature')}` strata do — pointing to a "
          "numerator/denominator channel of ER rather than the composite alone.")
    else:
        a(f"- Classification `{cls}`.")
    a("- Wording remains associative, not “we discovered the directional mechanism.”")
    a("")
    a("## NEXT RESEARCH QUESTION")
    a("")
    if cls == "LABEL_RESIDUAL":
        a("Given a residual C/D association after conditioning on transition `ER_60`, "
          "is the remaining information better described by **origin-episode history** "
          "(how the expansion was labeled before `te`) than by any contemporaneous "
          "transition scalar — still without a trade?")
    elif cls == "COMPONENT_ACCOUNTS":
        a("Given that transition `ER_60` accounts for the C/D destination residual, "
          "should the working object be redefined as **ER_60 at expansion→NORMAL** "
          "(dropping the composite C/D label) for subsequent mechanism work?")
    elif cls == "CONDITIONAL":
        a("Given that the destination asymmetry is concentrated in the "
          "**low `ER_60[te]` regime** and collapses where C and D overlap at mid ER, "
          "should the next object be **low-transition-ER ExpExit events**, asking "
          "whether origin-episode history still separates destinations *within* that "
          "regime — still without constructing a trade?")
    else:
        a("Given the Step 6 classification, which single frozen transition component "
          "should define the next event object — still without constructing a trade?")
    a("")
    a("_Do not answer by building a strategy in this step._")
    a("")

    out = STRAT / "STEP6_DIRECTIONALITY_DECOMPOSITION.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


if __name__ == "__main__":
    print(f"Wrote {write_report()}")
