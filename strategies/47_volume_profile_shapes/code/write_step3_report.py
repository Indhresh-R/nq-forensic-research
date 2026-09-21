"""Write the Step 3 report from the stored tables.

Does not recompute interactions and does not add a cutoff.
"""

from __future__ import annotations

import json

import pandas as pd

from frozen import RESULTS

ROOT = RESULTS.parents[0]
REPORT = ROOT / "STEP3_BOUNDARY_INTERACTION_REPORT.md"
APPROACH_ORDER = (
    "lower_region",
    "upper_region",
    "outside_below",
    "outside_above",
    "other_inside",
    "open_in_band",
)


def _fmt(value: float, digits: int = 3) -> str:
    if value != value:
        return ""
    return f"{value:.{digits}f}"


def _pct(count: int, n: int) -> str:
    if n == 0:
        return ""
    return f"{count / n:.1%}"


def _qrow(series: pd.Series) -> str:
    return " | ".join(_fmt(float(series.quantile(p))) for p in (0.0, 0.25, 0.50, 0.75, 1.0))


def _approach_table(frame: pd.DataFrame, title: str) -> list[str]:
    lines = [
        f"### {title}",
        "",
        f"Touches in this slice: {len(frame)}.",
        "",
        "| Approach | Touches | Share of touches | Later opposite HVN |",
        "| --- | ---: | ---: | ---: |",
    ]
    n = len(frame)
    for name in APPROACH_ORDER:
        part = frame.loc[frame["approach"] == name]
        if part.empty:
            continue
        opp = float(part["reached_opposite_side"].mean()) if len(part) else float("nan")
        lines.append(f"| {name} | {len(part)} | {_pct(len(part), n)} | {_fmt(opp)} |")
    present = set(frame["approach"].astype(str))
    missing = [name for name in APPROACH_ORDER if name not in present]
    if missing:
        lines.append("")
        lines.append("Approaches with zero touches in this slice: " + ", ".join(missing) + ".")
    if n:
        lines.append("")
        lines.append(
            f"Median minutes to first touch: {_fmt(float(frame['minutes_to_touch'].median()), 1)}. "
            f"Quartiles: {_fmt(float(frame['minutes_to_touch'].quantile(0.25)), 1)}, "
            f"{_fmt(float(frame['minutes_to_touch'].median()), 1)}, "
            f"{_fmt(float(frame['minutes_to_touch'].quantile(0.75)), 1)}."
        )
    return lines


def write() -> None:
    boundaries = pd.read_csv(RESULTS / "step3_boundaries.csv")
    sample = pd.read_csv(RESULTS / "step3_interactions_sample.csv")
    all_rows = pd.read_csv(RESULTS / "step3_interactions.csv")
    verification = json.loads((RESULTS / "step3_interaction_verification.json").read_text(encoding="utf-8"))
    touched = sample.loc[sample["touched"]].copy()
    no_touch = sample.loc[~sample["touched"]].copy()
    sized = touched.loc[touched["both_regions_sized"]]
    clean = touched.loc[touched["clean"]]

    open_lines = ["| Open zone | Sessions | Share |", "| --- | ---: | ---: |"]
    for name, count in sample["open_zone"].value_counts().items():
        open_lines.append(f"| {name} | {int(count)} | {_pct(int(count), len(sample))} |")

    no_touch_open = ["| Open zone among no-touch | Sessions |", "| --- | ---: |"]
    for name, count in no_touch["open_zone"].value_counts().items():
        no_touch_open.append(f"| {name} | {int(count)} |")

    exclude = all_rows["exclude_reason"].fillna("").value_counts().to_dict()
    body = []
    body.extend(
        [
            "# Step 3 — Prior-session structural boundaries",
            "",
            "This report does not test profitability, entries, exits, or forward returns. Boundaries and interactions use the rules in `STEP3_PREREGISTRATION.md`. Those rules were not changed after the tables were seen. An LVN-band touch is not a trade.",
            "",
            "## A. Dataset verification",
            "",
            "- Prior material gaps: "
            f"{len(boundaries)} from Step 2.",
            f"- With a later analysis session: {int(boundaries['has_next_session'].sum())}.",
            f"- Without a later analysis session: {int((~boundaries['has_next_session']).sum())}.",
            f"- Interaction sample after completeness and sync checks: {len(sample)}.",
            f"- Exclusions: {exclude}.",
            "- Next-session path: one-minute OHLC built from the same `trades_24h` files as Step 1. The continuous adjusted 1-minute file is not used.",
            "- Trade-bar high/low matches the stored next-session profile high/low within 1.0 point on every interaction-sample row.",
            f"- Detail: `results/step3_boundary_verification.json`, `results/step3_interaction_verification.json`.",
            "",
            "The 0.20 separation cut, the 0.30 depth cut, the 0.25 size label, and the 0.70 width threshold stay frozen.",
            "",
            "## B. Boundary objects",
            "",
            "One row is one prior material gap. Valley depth is stored only as an audit field. Boundaries are not ranked by depth.",
            "",
            f"| Measure | Min | p25 | Median | p75 | Max |",
            f"| --- | ---: | ---: | ---: | ---: | ---: |",
            f"| Separation | {_qrow(boundaries['separation'])} |",
            f"| Valley width | {_qrow(boundaries['valley_width'])} |",
            f"| Lower region share | {_qrow(boundaries['lower_share'])} |",
            f"| Upper region share | {_qrow(boundaries['upper_share'])} |",
            "",
            f"`both_regions_sized` (min share ≥ 0.25): {int(boundaries['both_regions_sized'].sum())} of {len(boundaries)}.",
            f"`clean` (no other detected peak in the gap): {int(boundaries['clean'].sum())} of {len(boundaries)}.",
            "",
            "Median valley width is "
            f"{_fmt(float(boundaries['valley_width'].median()))} of the prior range. "
            "That is a spatial band, not a single tick. Median separation remains "
            f"{_fmt(float(boundaries['separation'].median()))}.",
            "",
            "## C. Touch rate",
            "",
            f"| Outcome | Boundaries | Share of interaction sample |",
            f"| --- | ---: | ---: |",
            f"| First LVN-band touch | {int(sample['touched'].sum())} | {_pct(int(sample['touched'].sum()), len(sample))} |",
            f"| No touch | {int((~sample['touched']).sum())} | {_pct(int((~sample['touched']).sum()), len(sample))} |",
            "",
            "A prior separated structure is often revisited. It is not automatic: "
            f"{int((~sample['touched']).sum())} of {len(sample)} next sessions never print into that band.",
            "",
            "## D. Where the next session opens",
            "",
            *open_lines,
            "",
            "Opens already in an accepted region are common. Opens outside the prior profile happen, but they account for most of the no-touch cases:",
            "",
            *no_touch_open,
            "",
            "## E. Approach into the first touch",
            "",
            "Approach is the zone of the previous bar's close, or the open zone when the first bar is the touch. `lvn_band` is checked before the region labels, so a close already inside the band cannot be labeled as a region approach.",
            "",
        ]
    )
    body.extend(_approach_table(touched, "All touches"))
    body.append("")
    body.extend(_approach_table(sized, "Touches with both regions sized"))
    body.append("")
    body.extend(_approach_table(clean, "Touches with a clean gap"))
    body.extend(
        [
            "",
            "No touch in the full sample approached from `outside_below`, `outside_above`, or `other_inside`. Those open locations either never reached the band or, in the `other_inside` case, were rare among touches.",
            "",
            "Upper-region approaches outnumber lower-region approaches "
            f"({int((touched['approach'] == 'upper_region').sum())} vs "
            f"{int((touched['approach'] == 'lower_region').sum())}). "
            "That matches the open-zone mix: the next session more often starts already in the prior upper region.",
            "",
            "## F. Path after the touch",
            "",
            "Later opposite-HVN rates are in the tables above. On the full touch sample, "
            f"{_fmt(float(touched.loc[touched['approach'] == 'lower_region', 'reached_opposite_side'].mean()) if (touched['approach'] == 'lower_region').any() else float('nan'))} "
            "of lower-region approaches later reach the upper HVN, and "
            f"{_fmt(float(touched.loc[touched['approach'] == 'upper_region', 'reached_opposite_side'].mean()) if (touched['approach'] == 'upper_region').any() else float('nan'))} "
            "of upper-region approaches later reach the lower HVN.",
            "",
            "`returned_to_approach` is 1.00 for every lower-region and upper-region touch in this sample. That is not evidence of mean reversion. The LVN band overlaps the edges of both regions by construction, so a bar that stays near the band still intersects the approach region. The flag is retained only because it was preregistered. It is not used in the verdict.",
            "",
            "## G. What this does and does not show",
            "",
            "1. The Step 2 separated-region object is real enough that the next session often prints into its low-volume band.",
            "2. When it does, the path is usually from one of the two prior accepted regions, not from outside the prior structure.",
            "3. Outside opens often never interact with that particular band.",
            "4. Clean gaps and sized pairs do not create a different approach vocabulary. They shrink the count. They do not invent outside approaches.",
            "5. Nothing here is a return, a directional edge, or an entry rule.",
            "",
            "## Conclusion",
            "",
            "The useful object is the prior-session HVN–LVN–HVN boundary under the frozen 0.20 separation rule, not a P/b/D/B label and not a valley-depth ranking.",
            "",
            "Next-session price does interact with that boundary often enough to study. The first interaction is typically an approach from the upper or lower accepted region, or an open already in the band. Approaches from outside the prior profile are not the common touch path in this sample.",
            "",
            "Forward returns are still not tested.",
            "",
            f"Verification snapshot: touched={verification['touched']}, no_touch={verification['no_touch']}, approach_counts={verification['approach_counts']}.",
        ]
    )
    REPORT.write_text("\n".join(body) + "\n", encoding="utf-8")
    print(f"[step3] wrote {REPORT}", flush=True)


if __name__ == "__main__":
    write()
