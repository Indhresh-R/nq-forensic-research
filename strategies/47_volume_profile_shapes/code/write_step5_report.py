"""Write the Step 5 rejection-null report from stored tables."""

from __future__ import annotations

import pandas as pd

from frozen import RESULTS

ROOT = RESULTS.parents[0]
REPORT = ROOT / "STEP5_REJECTION_NULL_REPORT.md"
HORIZONS = ("H30", "H60", "H120", "session_end")
PRIMARY = ("H60", "H120")
TESTS = (
    "A_decided",
    "B_unconditional",
    "C_delayed_decided",
    "D_no_touch_hit_unconditional",
)


def _fmt(value: float, digits: int = 3) -> str:
    if value != value:
        return ""
    return f"{value:.{digits}f}"


def _pick(summary: pd.DataFrame, horizon: str, test: str) -> pd.Series:
    rows = summary.loc[(summary["horizon"] == horizon) & (summary["test"] == test)]
    if len(rows) != 1:
        raise SystemExit(f"Missing summary row {horizon} {test}")
    return rows.iloc[0]


def write() -> None:
    summary = pd.read_csv(RESULTS / "step5_null_summary.csv")
    locations = pd.read_csv(RESULTS / "step5_reject_locations.csv")
    frame = pd.read_csv(RESULTS / "step5_rejections.csv")

    lines = [
        "# Step 5 — Null-calibrated LVN rejection",
        "",
        "This report does not test profitability, entries, exits, or forward returns. Tests use `STEP5_PREREGISTRATION.md`. Those rules were not changed after the tables were seen. A reject is not a trade.",
        "",
        "`Traversal failed` is already established in Step 4. This step asks whether **rejection works** as a structural effect.",
        "",
        "## A. Sample",
        "",
        "- Primary rows: 34 per horizon (12 lower→upper, 22 upper→lower), inherited from Step 4.",
        "- `null_reject_prob = 1 - null_traverse_prob` from the touch-bar open distances.",
        "- Null A is the complementary decided test. It is not independent of Step 4.",
        "- Null B is unconditional: remain and traverse count against rejection.",
        "- Null C/D remove same-minute / touch-bar approach-HVN hits.",
        "",
        "## B. Same-minute vs delayed rejects",
        "",
        "| Horizon | Rejects | Same-minute | Delayed |",
        "| --- | ---: | ---: | ---: |",
    ]
    for horizon in HORIZONS:
        row = _pick(summary, horizon, "same_minute_vs_delayed")
        same_n = int(row["same_minute_n"]) if "same_minute_n" in row and row["same_minute_n"] == row["same_minute_n"] else int(row["null_n"])
        delayed_n = int(row["delayed_n"]) if "delayed_n" in row and row["delayed_n"] == row["delayed_n"] else int(row["reject_n"])
        lines.append(f"| {horizon} | {int(row['n'])} | {same_n} | {delayed_n} |")

    lines.extend(
        [
            "",
            "## C. Null comparisons",
            "",
            "| Horizon | Test | N | Null N | Reject N | Observed reject | Mean null reject | Observed − null |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for horizon in HORIZONS:
        for test in TESTS:
            row = _pick(summary, horizon, test)
            lines.append(
                f"| {horizon} | {test} | {int(row['n'])} | {int(row['null_n'])} | {int(row['reject_n'])} | "
                f"{_fmt(float(row['observed_reject']))} | {_fmt(float(row['mean_null_reject']))} | "
                f"{_fmt(float(row['mean_reject_minus_null']))} |"
            )

    lines.extend(["", "## D. Primary horizons in words", ""])
    for horizon in PRIMARY:
        a = _pick(summary, horizon, "A_decided")
        b = _pick(summary, horizon, "B_unconditional")
        c = _pick(summary, horizon, "C_delayed_decided")
        d = _pick(summary, horizon, "D_no_touch_hit_unconditional")
        lines.append(f"### {horizon}")
        lines.append("")
        lines.append(
            f"- Null A (decided, complementary): observed {_fmt(float(a['observed_reject']))} vs null "
            f"{_fmt(float(a['mean_null_reject']))} (difference {_fmt(float(a['mean_reject_minus_null']))})."
        )
        lines.append(
            f"- Null B (unconditional): observed {_fmt(float(b['observed_reject']))} vs null "
            f"{_fmt(float(b['mean_null_reject']))} (difference {_fmt(float(b['mean_reject_minus_null']))})."
        )
        lines.append(
            f"- Null C (delayed decided): N={int(c['n'])}, observed {_fmt(float(c['observed_reject']))} vs null "
            f"{_fmt(float(c['mean_null_reject']))} (difference {_fmt(float(c['mean_reject_minus_null']))})."
        )
        lines.append(
            f"- Null D (no touch-bar approach hit): N={int(d['n'])}, observed {_fmt(float(d['observed_reject']))} vs null "
            f"{_fmt(float(d['mean_null_reject']))} (difference {_fmt(float(d['mean_reject_minus_null']))})."
        )
        lines.append("")

    lines.extend(
        [
            "## E. Reject location and path extent",
            "",
            "| Horizon | Location | N | Share | Med minutes | Med LVN pen. | Med opp. excursion |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for horizon in HORIZONS:
        part = locations.loc[locations["horizon"] == horizon]
        for _, row in part.iterrows():
            lines.append(
                f"| {horizon} | {row['reject_location']} | {int(row['n'])} | {_fmt(float(row['share']))} | "
                f"{_fmt(float(row['med_minutes']), 1)} | {_fmt(float(row['med_lvn_pen']))} | "
                f"{_fmt(float(row['med_opp_exc']))} |"
            )

    lines.extend(["", "## F. Slices on Null B (unconditional)", ""])
    lines.append("| Horizon | Slice | N | Observed reject | Mean null | Observed − null |")
    lines.append("| --- | --- | ---: | ---: | ---: | ---: |")
    for horizon in PRIMARY:
        for slice_name in ("lower_to_upper", "upper_to_lower", "clean", "both_regions_sized"):
            row = _pick(summary, horizon, f"B_unconditional__{slice_name}")
            lines.append(
                f"| {horizon} | {slice_name} | {int(row['n'])} | {_fmt(float(row['observed_reject']))} | "
                f"{_fmt(float(row['mean_null_reject']))} | {_fmt(float(row['mean_reject_minus_null']))} |"
            )

    b60 = _pick(summary, "H60", "B_unconditional")
    b120 = _pick(summary, "H120", "B_unconditional")
    d60 = _pick(summary, "H60", "D_no_touch_hit_unconditional")
    d120 = _pick(summary, "H120", "D_no_touch_hit_unconditional")
    c60 = _pick(summary, "H60", "C_delayed_decided")
    same60 = _pick(summary, "H60", "same_minute_vs_delayed")

    lines.extend(
        [
            "",
            "## G. Interpretation",
            "",
            "1. Null A must match the opposite of Step 4's decided traverse gap. If it does, that only restates the killed traverse result.",
            "2. Null B is the claim that matters for a rejection mechanism inside a fixed horizon.",
            "3. A large same-minute share means many “rejects” are the first LVN minute also printing the nearby approach HVN, not a later reaction.",
            "4. Null C/D ask whether any rejection effect remains after removing that same-minute geometry.",
            "",
            "## Conclusion",
            "",
            f"At H60, same-minute rejects are {int(same60['null_n'])} of {int(same60['n'])} rejects; delayed are {int(same60['reject_n'])}.",
            "",
            f"Null B at H60: observed reject rate {_fmt(float(b60['observed_reject']))} vs mean null "
            f"{_fmt(float(b60['mean_null_reject']))} (difference {_fmt(float(b60['mean_reject_minus_null']))}).",
            "",
            f"Null B at H120: observed {_fmt(float(b120['observed_reject']))} vs null "
            f"{_fmt(float(b120['mean_null_reject']))} (difference {_fmt(float(b120['mean_reject_minus_null']))}).",
            "",
            f"Null D at H60: observed {_fmt(float(d60['observed_reject']))} vs null "
            f"{_fmt(float(d60['mean_null_reject']))} (difference {_fmt(float(d60['mean_reject_minus_null']))}), N={int(d60['n'])}.",
            "",
            f"Null D at H120: observed {_fmt(float(d120['observed_reject']))} vs null "
            f"{_fmt(float(d120['mean_null_reject']))} (difference {_fmt(float(d120['mean_reject_minus_null']))}), N={int(d120['n'])}.",
            "",
            f"Null C at H60 (delayed decided): observed {_fmt(float(c60['observed_reject']))} vs null "
            f"{_fmt(float(c60['mean_null_reject']))} (difference {_fmt(float(c60['mean_reject_minus_null']))}), N={int(c60['n'])}.",
            "",
        ]
    )

    # Verdict language from the actual B/D signs — filled after we know numbers; regenerate uses real values
    b60_diff = float(b60["mean_reject_minus_null"])
    d60_diff = float(d60["mean_reject_minus_null"])
    if b60_diff <= 0 and d60_diff <= 0:
        verdict = (
            "The short-horizon rejection claim does not clear the geometric null once remain outcomes "
            "and same-minute barrier hits are treated honestly. Rejects are common among decided paths, "
            "but that is largely the mirror of the killed traverse plus nearby approach-HVN geometry."
        )
    elif b60_diff > 0 and d60_diff <= 0:
        verdict = (
            "Unconditional rejection can look elevated only while same-minute touch-bar hits remain in "
            "the sample. After removing those hits, the rejection claim does not clear the null."
        )
    elif b60_diff <= 0 and d60_diff > 0:
        verdict = (
            "Unconditional rejection is not above the eventual geometric null, but the delayed/no-touch-hit "
            "subset shows a positive gap. That subset is small and is not a trading rule."
        )
    else:
        verdict = (
            "Rejection shows a positive gap versus the geometric null on the unconditional and "
            "no-touch-hit tests at the primary horizons. That is still not a return edge and not an entry."
        )
    lines.append(verdict)
    lines.append("")
    lines.append("No forward return is computed here. No entry is defined.")
    # silence unused
    _ = frame

    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[step5] wrote {REPORT}", flush=True)


if __name__ == "__main__":
    write()
