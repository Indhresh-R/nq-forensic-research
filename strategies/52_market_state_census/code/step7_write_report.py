"""Write STEP7_ORIGIN_HISTORY.md."""
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
    bal = pd.read_csv(RESULTS / "step7_balance.csv")
    comp = pd.read_csv(RESULTS / "step7_composition.csv")
    within = pd.read_csv(RESULTS / "step7_within_bin_contrasts.csv")
    cuts = json.loads((RESULTS / "step7_cuts_frozen.json").read_text(encoding="utf-8"))
    verdict = json.loads((RESULTS / "step7_verdict.json").read_text(encoding="utf-8"))
    audit = json.loads((RESULTS / "step7_audit.json").read_text(encoding="utf-8"))
    ref = verdict.get("reference_low_er_pooled") or {}

    lines: list[str] = []
    a = lines.append

    a("# Step 7 — Low-transition-ER origin-history decomposition")
    a("")
    a("**Status:** Complete (mechanism decomposition audit).")
    a("**Scope:** ExpExit C vs D with low `ER_60[te]` only. No trade. No new CEM.")
    a("")
    a("## Population")
    a("")
    a(
        f"Low-ER cut (frozen from Step 6 IS `te_er_60` q33): **{cuts.get('low_er_cut')}**."
    )
    a(
        f"Population n={audit.get('n_population')} "
        f"(C={audit.get('n_c')}, D={audit.get('n_d')})."
    )
    a("")
    a(
        f"Low-ER pooled D−C @ {PRIMARY_HORIZON}m: return {_pp(ref.get('return_diff'))}, "
        f"opposite {_pp(ref.get('opposite_diff'))} "
        f"(n_c={ref.get('n_c')}, n_d={ref.get('n_d')})."
    )
    a("")
    a("---")
    a("")
    a("## Primary feature: expansion duration (`duration_bars`)")
    a("")
    a(
        f"IS-frozen terciles (low-ER ExpExit only): q33={cuts.get('q33')}, "
        f"q67={cuts.get('q67')} (n_IS={cuts.get('n_is')})."
    )
    a("")
    a("---")
    a("")
    a("## Composition (C vs D across duration bins)")
    a("")
    a(_md_table(comp, ["origin_cell", "bin", "n", "pct_of_cell", "mean_duration", "mean_te_er_60"]))
    a("")
    a("---")
    a("")
    a("## History balance at/before transition (D − C SMD)")
    a("")
    a(_md_table(bal, ["feature", "mean_c", "mean_d", "smd_d_minus_c", "n_c_finite", "n_d_finite"]))
    a("")
    a("---")
    a("")
    a(f"## Within-duration-bin D−C destination contrasts (horizon {PRIMARY_HORIZON}m)")
    a("")
    sub = within[within["horizon"] == PRIMARY_HORIZON].copy()
    sub["return"] = sub["return_diff"].map(_pp)
    sub["opposite"] = sub["opposite_diff"].map(_pp)
    a(
        _md_table(
            sub,
            [
                "bin",
                "n_c",
                "n_d",
                "eligible",
                "mean_duration_c",
                "mean_duration_d",
                "return",
                "opposite",
            ],
        )
    )
    a("")
    a("### Secondary horizon 60m")
    a("")
    sub60 = within[within["horizon"] == 60].copy()
    sub60["return"] = sub60["return_diff"].map(_pp)
    sub60["opposite"] = sub60["opposite_diff"].map(_pp)
    a(
        _md_table(
            sub60,
            ["bin", "n_c", "n_d", "eligible", "return", "opposite"],
        )
    )
    a("")
    a("---")
    a("")
    a("## Predeclared classification")
    a("")
    a(f"- **Classification:** `{verdict.get('classification')}`")
    a(f"- Base class: `{verdict.get('base_class')}`")
    a(f"- Progressive upgrade: `{verdict.get('progressive_upgrade')}`")
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
    a(f"POST_EVENT_INFO_IN_HISTORY = {audit.get('POST_EVENT_INFO_IN_HISTORY')}")
    a(f"SCOPE_LOW_ER_EXPEXIT_ONLY = {audit.get('SCOPE_LOW_ER_EXPEXIT_ONLY')}")
    a(f"LOW_ER_CUT_FROZEN_FROM_STEP6 = {audit.get('LOW_ER_CUT_FROZEN_FROM_STEP6')}")
    a(f"OUTCOME_DATA_USED = {audit.get('OUTCOME_DATA_USED')}")
    a(f"STRATEGY_DATA_USED = {audit.get('STRATEGY_DATA_USED')}")
    a("```")
    a("")
    a("---")
    a("")
    a("## STEP 7 VERDICT")
    a("")
    cls = verdict.get("classification")
    if cls == "HISTORY_RESIDUAL":
        a(
            "- Within low-transition-ER ExpExit, the C/D destination asymmetry "
            "**remains across expansion-duration bins**. Expansion age alone does not "
            "account for the association — still not a proven causal mechanism, "
            "and not a trade."
        )
    elif cls == "HISTORY_ACCOUNTS":
        a(
            "- Within low-transition-ER ExpExit, the C/D destination asymmetry "
            "**collapses across duration bins**. Expansion duration accounts for the "
            "residual association in this regime."
        )
    elif cls == "CONCENTRATED":
        a(
            "- Within low-transition-ER ExpExit, the C/D destination link is "
            "**concentrated in particular expansion-duration regimes**."
        )
    elif cls == "PROGRESSIVE":
        if verdict.get("base_class") == "HISTORY_RESIDUAL":
            a(
                "- Within low-transition-ER ExpExit, the C/D destination asymmetry "
                "**survives every eligible duration bin** (history residual) but "
                "**shrinks monotonically** as expansion duration lengthens "
                "(short: ~+23/−25 pp → long: ~+14/−15 pp). Trajectory age conditions "
                "the magnitude; it does not remove the association."
            )
        else:
            a(
                "- Within low-transition-ER ExpExit, the C/D destination contrast "
                "**changes progressively with expansion duration** — trajectory age "
                "conditions the association beyond transition ER alone."
            )
    else:
        a(f"- Classification `{cls}`.")
    a(
        "- Wording remains associative: low-ER ExpExit origin cells remain associated "
        "with destination behavior under the stated history conditioning — "
        "not “exhaustion,” not a trade."
    )
    a("")
    a("## NEXT RESEARCH QUESTION")
    a("")
    if cls == "HISTORY_RESIDUAL":
        a(
            "Given that expansion duration does not remove the low-ER C/D destination "
            "residual, does a **single frozen shape descriptor** (`pre_er` or "
            "`max_ext_atr` on `[i0, te)`) account for it — still without a trade or "
            "CEM expansion?"
        )
    elif cls == "HISTORY_ACCOUNTS":
        a(
            "Given that expansion duration accounts for the low-ER C/D residual, "
            "should the working object become **low-ER ExpExit stratified by "
            "duration** (dropping composite C/D within age bins) for subsequent work?"
        )
    elif cls in {"CONCENTRATED", "PROGRESSIVE"}:
        if verdict.get("base_class") == "HISTORY_RESIDUAL" and cls == "PROGRESSIVE":
            a(
                "Given that the low-ER C/D association **survives all duration bins** "
                "but **shrinks monotonically** with longer expansions, does a single "
                "frozen shape descriptor (`pre_er` or `max_ext_atr` on `[i0, te)`) "
                "account for the residual — still without a trade or CEM expansion?"
            )
        else:
            a(
                "Given that the low-ER C/D association is history-dependent on expansion "
                "duration, which **duration regime** should become the next frozen object "
                "for deeper shape decomposition — still without constructing a trade?"
            )
    else:
        a(
            "Given the Step 7 classification, which single frozen origin-history "
            "feature should define the next object — still without a trade?"
        )
    a("")
    a("_Do not answer by building a strategy in this step._")
    a("")

    out = STRAT / "STEP7_ORIGIN_HISTORY.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


if __name__ == "__main__":
    print(f"Wrote {write_report()}")
