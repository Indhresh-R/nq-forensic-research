"""Write STEP5_SIGNED_EXIT_POSITION.md."""
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
    cuts = json.loads((RESULTS / "step5_s_cuts_frozen.json").read_text(encoding="utf-8"))
    within = pd.read_csv(RESULTS / "step5_within_bin_contrasts.csv")
    comp = pd.read_csv(RESULTS / "step5_composition.csv")
    verdict = json.loads((RESULTS / "step5_verdict.json").read_text(encoding="utf-8"))
    audit = json.loads((RESULTS / "step5_audit.json").read_text(encoding="utf-8"))

    lines: list[str] = []
    a = lines.append

    a("# Step 5 — Signed exit position (ExpExit diagnostic)")
    a("")
    a("**Status:** Complete (single-feature mechanism diagnostic).")
    a("**Scope:** ExpExit C vs D only. Not a trade. Not a new CEM.")
    a("")
    a("## Feature")
    a("")
    a(r"$S = (P_{\mathrm{event}} - P_{\mathrm{mid}}) / R$")
    a("")
    a("with `P_event = close[te]`, and `P_mid`, `R` from the pre-event envelope `[i0, te)`.")
    a("")
    a(f"IS-frozen terciles: q33={cuts.get('q33')}, q67={cuts.get('q67')} "
      f"(n_IS={cuts.get('n_is')}).")
    a("")
    a("---")
    a("")
    a("## Composition (where C vs D sit in S)")
    a("")
    a("### Terciles")
    a("")
    a(_md_table(comp[comp["bin_col"] == "s_tercile"], ["origin_cell", "bin", "n", "pct_of_cell", "mean_S"]))
    a("")
    a("### Sign")
    a("")
    a(_md_table(comp[comp["bin_col"] == "sign_bin"], ["origin_cell", "bin", "n", "pct_of_cell", "mean_S"]))
    a("")
    a("---")
    a("")
    a(f"## Within-bin destination contrasts (D − C), horizon {PRIMARY_HORIZON}m")
    a("")
    a("### S terciles")
    a("")
    sub = within[
        (within["bin_col"] == "s_tercile") & (within["horizon"] == PRIMARY_HORIZON)
    ].copy()
    sub["return"] = sub["return_diff"].map(_pp)
    sub["opposite"] = sub["opposite_diff"].map(_pp)
    a(_md_table(sub, ["bin", "n_c", "n_d", "eligible", "mean_S_c", "mean_S_d", "return", "opposite"]))
    a("")
    a("### Sign bins")
    a("")
    sub2 = within[
        (within["bin_col"] == "sign_bin") & (within["horizon"] == PRIMARY_HORIZON)
    ].copy()
    sub2["return"] = sub2["return_diff"].map(_pp)
    sub2["opposite"] = sub2["opposite_diff"].map(_pp)
    a(_md_table(sub2, ["bin", "n_c", "n_d", "eligible", "return", "opposite"]))
    a("")
    a("60m and CIs: `results/step5_within_bin_contrasts.csv`.")
    a("")
    a("---")
    a("")
    a("## Predeclared classification")
    a("")
    a(f"- **Classification:** `{verdict.get('classification')}`")
    a(f"- Eligible tercile bins: {verdict.get('n_eligible_bins')}")
    a(f"- Bins keeping both endpoints: {verdict.get('n_keep_both_endpoints')}")
    a(f"- Bins losing both endpoints: {verdict.get('n_lose_both_endpoints')}")
    a("")
    a("### Eligible-bin detail")
    a("")
    for d in verdict.get("detail") or []:
        a(
            f"- `{d.get('bin')}`: return={_pp(d.get('return_diff'))}, "
            f"opposite={_pp(d.get('opposite_diff'))}, "
            f"keep_signs=({d.get('return_keeps_sign')},{d.get('opposite_keeps_sign')}), "
            f"ge_half=({d.get('return_ge_half')},{d.get('opposite_ge_half')})"
        )
    a("")
    a("---")
    a("")
    a("## Leakage / scope audit")
    a("")
    a("```text")
    a(f"LOOKAHEAD_CHECK = {audit.get('LOOKAHEAD_CHECK')}")
    a(f"POST_EVENT_INFO_IN_FEATURE = {audit.get('POST_EVENT_INFO_IN_FEATURE')}")
    a(f"SCOPE_EXPEXIT_ONLY = {audit.get('SCOPE_EXPEXIT_ONLY')}")
    a(f"OUTCOME_DATA_USED = {audit.get('OUTCOME_DATA_USED')}")
    a(f"STRATEGY_DATA_USED = {audit.get('STRATEGY_DATA_USED')}")
    a("```")
    a("")
    a("---")
    a("")
    a("## STEP 5 VERDICT")
    a("")
    cls = verdict.get("classification")
    if cls == "REMAIN":
        a("- Within comparable signed-position terciles, the ExpExit C/D destination "
          "asymmetry **remains**. This is more consistent with **directionality-at-exit** "
          "as an associative description — still not a causal proof, and not a trade.")
    elif cls == "DISAPPEAR":
        a("- Within comparable signed-position terciles, the ExpExit C/D destination "
          "asymmetry **disappears / collapses**. The Step-4 residual was likely "
          "**geometry not yet matched** (unsigned distance missed side/location).")
    elif cls == "CONDITIONAL":
        a("- The ExpExit C/D destination asymmetry is **conditional on signed exit "
          "location**: it remains in some S regions and not others. That requires a "
          "location-conditioned mechanism decomposition — still not a trade.")
    else:
        a(f"- Classification `{cls}`: see detail tables.")
    a("- CompExit was intentionally not re-tested.")
    a("")
    a("## NEXT RESEARCH QUESTION")
    a("")
    if cls == "REMAIN":
        a("Given that signed exit location does not remove the ExpExit destination "
          "asymmetry, what is the smallest *non-directional-label* pre-event state "
          "descriptor (still frozen before outcomes) that could falsify "
          "directionality-at-exit — without constructing a trade?")
    elif cls == "DISAPPEAR":
        a("Given that signed exit location absorbs the residual ExpExit asymmetry, "
          "is the operative object better defined as **signed exit geometry** itself "
          "(rather than C vs D directionality labels) for subsequent mechanism work?")
    else:
        a("Given location-conditional ExpExit asymmetry, which signed-position region "
          "should be isolated next for a focused mechanism contrast — still without "
          "a directional trade hypothesis?")
    a("")
    a("_Do not answer by building a strategy in this step._")
    a("")

    out = STRAT / "STEP5_SIGNED_EXIT_POSITION.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


if __name__ == "__main__":
    print(f"Wrote {write_report()}")
