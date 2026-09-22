"""Write TRANSITION_PATH_SCREEN.md."""
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
                cells.append(f"{v:.4f}" if abs(v) < 100 else f"{v:.2f}")
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def write_report() -> Path:
    contrast = pd.read_csv(RESULTS / "path_contrast_all.csv")
    verdict = json.loads((RESULTS / "verdict.json").read_text(encoding="utf-8"))
    audit = json.loads((RESULTS / "audit.json").read_text(encoding="utf-8"))

    lines: list[str] = []
    a = lines.append

    a("# Transition Path Screen")
    a("")
    a("**Strategy 54.** Path-difference screen only. No trades.")
    a("")
    a("## 1. Objective")
    a("")
    a(
        "Among census state transitions, which show subsequent path geometry "
        "sufficiently distinct from **staying in the origin state** to justify "
        "one later simple executable test?"
    )
    a("")
    a("## 2. Context")
    a("")
    a(
        "Strategy 53 froze `REJECTED` on coarse state→generic-family routing. "
        "Strategy 52 suggested interesting structure around **transitions/events**, "
        "not broad regimes alone."
    )
    a("")
    a("## 3. Frozen catalogs")
    a("")
    a("- **R:** `range_state` directed transitions")
    a("- **C:** `composite_primary` directed transitions")
    a("")
    a("## 4. Leakage audit")
    a("")
    a("```text")
    for k in (
        "LOOKAHEAD_CHECK",
        "STATE_AT_T_CAUSAL",
        "PATH_STRICTLY_AFTER_T",
        "NO_STRATEGY_PNL",
        "NO_PARAMETER_OPTIMIZATION",
        "NO_POST_HOC_TRANSITION_PICK",
    ):
        a(f"{k} = {audit.get(k)}")
    a("```")
    a("")
    a("## 5. Classification summary")
    a("")
    counts: dict[str, int] = {}
    for v in verdict["cells"].values():
        counts[v["classification"]] = counts.get(v["classification"], 0) + 1
    for k, n in sorted(counts.items()):
        a(f"- `{k}`: {n}")
    a("")
    a(f"**INTERESTING list:** {verdict.get('interesting')}")
    a("")
    a(
        f"**INTERESTING after removing definitional activity overlap:** "
        f"{verdict.get('interesting_non_definitional')}"
    )
    a("")
    a(
        "Note: `HIGH_ACTIVITY` / `LOW_ACTIVITY` are defined from volatility/volume. "
        "Larger (or smaller) post-event `hl_range` when entering those labels can be "
        "**partly compositional** with the label — not automatic evidence for a trade."
    )
    a("")
    a("## 6. INTERESTING transitions (detail)")
    a("")
    interesting = [
        v for v in verdict["cells"].values() if v["classification"] == "INTERESTING"
    ]
    if not interesting:
        a("_None._")
    else:
        for v in sorted(interesting, key=lambda x: (x["catalog"], x["transition"])):
            caution = " **OOS_CAUTION**" if v.get("oos_caution") else ""
            defn = " **DEFINITIONAL_OVERLAP**" if v.get("definitional_overlap") else ""
            a(
                f"- `{v['catalog']}:{v['transition']}`{caution}{defn} — "
                f"IS n={v['detail']['IS']['n']}, "
                f"g_IS={v['detail']['IS']['rel_gap']}, "
                f"g_Val={v['detail']['Validation']['rel_gap']}"
            )
    a("")
    a("### Catalog R highlight (range_state)")
    a("")
    a(
        "Strategy 52’s ExpExit object (`EXPANSION→NORMAL_RANGE`) is **KILL** on this "
        "magnitude screen: IS `rel_gap ≈ 0.03` vs staying in EXPANSION. Path *size* after "
        "the transition is not distinct; Strategy 52’s residual was destination "
        "*asymmetry* within ExpExit cells — a different question than this screen."
    )
    a("")
    a("## 7. Full 15m contrast table (IS)")
    a("")
    is_c = contrast.loc[contrast["split"] == "IS"].sort_values(
        ["catalog", "rel_gap"], ascending=[True, False]
    )
    a(
        _md_table(
            is_c,
            [
                "catalog",
                "transition",
                "n_transition",
                "n_stay_baseline",
                "median_hl_range_trans",
                "median_hl_range_stay",
                "delta_hl_range",
                "rel_gap",
                "median_abs_net_trans",
                "median_abs_net_stay",
            ],
        )
    )
    a("")
    a("## 8. Validation / OOS contrasts")
    a("")
    for sp in ("Validation", "OOS"):
        a(f"### {sp}")
        a("")
        sub = contrast.loc[contrast["split"] == sp].sort_values(
            ["catalog", "rel_gap"], ascending=[True, False]
        )
        a(
            _md_table(
                sub,
                [
                    "catalog",
                    "transition",
                    "n_transition",
                    "median_hl_range_trans",
                    "median_hl_range_stay",
                    "rel_gap",
                ],
            )
        )
        a("")
    a("## 9. Independent classifications")
    a("")
    for key in sorted(verdict["cells"].keys()):
        v = verdict["cells"][key]
        a(f"- `{key}`: **{v['classification']}**")
    a("")
    a("## 10. Recommended next step")
    a("")
    nondef = verdict.get("interesting_non_definitional") or []
    if nondef:
        a(
            "For each **non-definitional** INTERESTING transition, run **one** separate, "
            "preregistered simple execution test (kill/advance). Do not reopen Strategy 53."
        )
    elif interesting:
        a(
            "All INTERESTING hits are into `HIGH_ACTIVITY` / `LOW_ACTIVITY` "
            "(definitional overlap with range). **Do not** promote them to execution "
            "tests without a newly preregistered contrast that is not entangled with "
            "the activity label (e.g. destination geometry within a fixed transition, "
            "as in Strategy 52 ExpExit — but only as a short kill/advance trade test, "
            "not another long decomposition)."
        )
    else:
        a(
            "No INTERESTING transitions under the frozen path-difference bar. "
            "Do not force a trade. Revisit only with a newly preregistered screen "
            "(different state column or contrast), not silent retuning."
        )
    a("")
    a("## Final research question")
    a("")
    a(
        "> Among census state transitions, which show sufficiently distinct subsequent "
        "path geometry to justify one simple executable test?"
    )
    a("")
    if nondef:
        a(
            f"**Answer:** {len(nondef)} non-definitional INTERESTING type(s): {nondef}."
        )
    elif interesting:
        a(
            f"**Answer:** {len(interesting)} INTERESTING type(s), but **all** are "
            "activity-label transitions with definitional overlap — not clean "
            "graduation candidates for a trade test."
        )
    else:
        a("**Answer:** None under this frozen screen.")
    a("")

    out = RESULTS / "TRANSITION_PATH_SCREEN.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


if __name__ == "__main__":
    print(f"Wrote {write_report()}")
