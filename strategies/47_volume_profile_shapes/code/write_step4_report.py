"""Write the Step 4 path-reaction report from stored tables."""

from __future__ import annotations

import json

import pandas as pd

from frozen import RESULTS

ROOT = RESULTS.parents[0]
REPORT = ROOT / "STEP4_PATH_REACTION_REPORT.md"
HORIZON_ORDER = ("H30", "H60", "H120", "session_end")
SLICES = (
    ("all", None),
    ("lower_to_upper", "lower_region"),
    ("upper_to_lower", "upper_region"),
    ("clean", "clean"),
    ("both_regions_sized", "both_regions_sized"),
)


def _fmt(value: float, digits: int = 3) -> str:
    if value != value:
        return ""
    return f"{value:.{digits}f}"


def _slice_frame(paths: pd.DataFrame, horizon: str, slice_name: str, rule: str | None) -> pd.DataFrame:
    part = paths.loc[paths["horizon"] == horizon].copy()
    if rule == "lower_region":
        return part.loc[part["approach"] == "lower_region"]
    if rule == "upper_region":
        return part.loc[part["approach"] == "upper_region"]
    if rule == "clean":
        return part.loc[part["clean"]]
    if rule == "both_regions_sized":
        return part.loc[part["both_regions_sized"]]
    return part


def _stats(part: pd.DataFrame) -> dict:
    counts = part["outcome"].value_counts().to_dict()
    decided = part.loc[part["outcome"].isin(["traverse", "reject"])]
    null_ok = decided.loc[decided["null_defined"]]
    obs = float((null_ok["outcome"] == "traverse").mean()) if len(null_ok) else float("nan")
    null_mean = float(null_ok["null_traverse_prob"].mean()) if len(null_ok) else float("nan")
    diff = (
        float(((null_ok["outcome"] == "traverse").astype(float) - null_ok["null_traverse_prob"]).mean())
        if len(null_ok)
        else float("nan")
    )
    trav = part.loc[part["outcome"] == "traverse", "minutes_to_event"]
    rej = part.loc[part["outcome"] == "reject", "minutes_to_event"]
    return {
        "n": len(part),
        "traverse": int(counts.get("traverse", 0)),
        "reject": int(counts.get("reject", 0)),
        "remain": int(counts.get("remain", 0)),
        "ambiguous": int(counts.get("ambiguous_same_bar", 0)),
        "decided_n": len(decided),
        "null_n": len(null_ok),
        "obs": obs,
        "null": null_mean,
        "diff": diff,
        "med_trav_min": float(trav.median()) if len(trav) else float("nan"),
        "med_rej_min": float(rej.median()) if len(rej) else float("nan"),
        "med_lvn": float(part["max_lvn_penetration"].median()) if "max_lvn_penetration" in part else float("nan"),
        "med_opp": float(part["max_opposite_excursion"].median()) if "max_opposite_excursion" in part else float("nan"),
    }


def write() -> None:
    paths = pd.read_csv(RESULTS / "step4_paths.csv")
    opens = pd.read_csv(RESULTS / "step4_open_in_band.csv")
    summary = pd.read_csv(RESULTS / "step4_summary.csv")
    verification = json.loads((RESULTS / "step4_verification.json").read_text(encoding="utf-8"))

    lines = [
        "# Step 4 — LVN reaction path",
        "",
        "This report does not test profitability, entries, exits, or forward returns. Competing events use the rules in `STEP4_PREREGISTRATION.md`. Those rules were not changed after the tables were seen. A traverse is not a trade.",
        "",
        "## A. Sample",
        "",
        f"- Primary rows: {verification['primary_rows']} "
        f"({verification['lower_region']} lower→upper, {verification['upper_region']} upper→lower).",
        f"- `open_in_band` side table: {verification['open_in_band']} touches.",
        "- Path events use the approach and opposite HVN prices, not the full accepted-region spans.",
        "- Geometric null: `dist_to_approach / (dist_to_approach + dist_to_opposite)` from the touch-bar open.",
        "- Primary horizons: H60 and H120. H30 and session_end are reported.",
        "",
        "## B. Outcome counts by horizon (all primary approaches)",
        "",
        "| Horizon | N | Traverse | Reject | Remain | Ambiguous same bar |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for horizon in HORIZON_ORDER:
        row = summary.loc[summary["horizon"] == horizon].iloc[0]
        lines.append(
            f"| {horizon} | {int(row['n'])} | {int(row['traverse'])} | {int(row['reject'])} | "
            f"{int(row['remain'])} | {int(row['ambiguous_same_bar'])} |"
        )

    lines.extend(
        [
            "",
            "## C. Traverse vs reject against the geometric null",
            "",
            "The observed traverse share uses only rows that decided traverse or reject and have a defined null. Remain and ambiguous rows are excluded from that ratio.",
            "",
            "| Horizon | Decided N | Null N | Observed traverse share | Mean null | Observed − null |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for horizon in HORIZON_ORDER:
        row = summary.loc[summary["horizon"] == horizon].iloc[0]
        lines.append(
            f"| {horizon} | {int(row['decided_n'])} | {int(row['null_compare_n'])} | "
            f"{_fmt(float(row['observed_traverse_share_decided']))} | "
            f"{_fmt(float(row['mean_null_traverse_prob']))} | "
            f"{_fmt(float(row['mean_traverse_minus_null']))} |"
        )

    lines.extend(["", "## D. Slices on the primary horizons", ""])
    for horizon in ("H60", "H120"):
        lines.append(f"### {horizon}")
        lines.append("")
        lines.append(
            "| Slice | N | Trav | Rej | Rem | Amb | Decided | Obs trav | Null | Obs − null | Med min to trav | Med min to rej | Med LVN pen. | Med opp. excursion |"
        )
        lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
        for slice_name, rule in SLICES:
            part = _slice_frame(paths, horizon, slice_name, rule)
            st = _stats(part)
            lines.append(
                f"| {slice_name} | {st['n']} | {st['traverse']} | {st['reject']} | {st['remain']} | "
                f"{st['ambiguous']} | {st['decided_n']} | {_fmt(st['obs'])} | {_fmt(st['null'])} | "
                f"{_fmt(st['diff'])} | {_fmt(st['med_trav_min'], 1)} | {_fmt(st['med_rej_min'], 1)} | "
                f"{_fmt(st['med_lvn'])} | {_fmt(st['med_opp'])} |"
            )
        lines.append("")

    lines.extend(
        [
            "## E. `open_in_band` side table",
            "",
            "These touches have no approach side. The table is first HVN printed within the horizon.",
            "",
            "| Horizon | N | Lower HVN first | Upper HVN first | Both same bar | Neither |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for horizon in HORIZON_ORDER:
        part = opens.loc[opens["horizon"] == horizon]
        counts = part["outcome"].value_counts().to_dict()
        lines.append(
            f"| {horizon} | {len(part)} | {int(counts.get('lower_hvn_first', 0))} | "
            f"{int(counts.get('upper_hvn_first', 0))} | {int(counts.get('both_same_bar', 0))} | "
            f"{int(counts.get('neither', 0))} |"
        )

    # Pull key H60/H120 numbers for conclusion text
    h60 = summary.loc[summary["horizon"] == "H60"].iloc[0]
    h120 = summary.loc[summary["horizon"] == "H120"].iloc[0]
    lines.extend(
        [
            "",
            "## F. Interpretation",
            "",
            "1. Competing events are HVN-to-HVN. They do not reuse Step 3's region-span return flag.",
            "2. The geometric null already expects some traverses when the measurement price sits closer to the approach HVN than to the opposite HVN.",
            "3. The mechanism claim needs observed traverse share above that null on the decided subset, not merely a raw opposite-HVN hit rate from Step 3.",
            "4. Remain rates matter: a large remain share means the boundary often does not resolve into either story inside the horizon.",
            "",
            "## Conclusion",
            "",
            f"At H60: traverse {int(h60['traverse'])}, reject {int(h60['reject'])}, remain {int(h60['remain'])} "
            f"(N={int(h60['n'])}). Among decided rows, observed traverse share "
            f"{_fmt(float(h60['observed_traverse_share_decided']))} vs mean null "
            f"{_fmt(float(h60['mean_null_traverse_prob']))} "
            f"(difference {_fmt(float(h60['mean_traverse_minus_null']))}).",
            "",
            f"At H120: traverse {int(h120['traverse'])}, reject {int(h120['reject'])}, remain {int(h120['remain'])}. "
            f"Observed traverse share {_fmt(float(h120['observed_traverse_share_decided']))} vs mean null "
            f"{_fmt(float(h120['mean_null_traverse_prob']))} "
            f"(difference {_fmt(float(h120['mean_traverse_minus_null']))}).",
            "",
            "The preferential-traverse story does not hold on this sample. After an accepted-region approach into the prior LVN band, the first HVN event is usually a return through the approach HVN, not a cross to the opposite HVN. Observed traverse shares sit at or below the geometric null at H60 and H120. Session-end eventually prints more opposite-HVN hits, but rejects still dominate (8 traverse vs 26 reject).",
            "",
            "Slices (lower→upper, upper→lower, clean, sized) do not rescue a traverse mechanism at the primary horizons.",
            "",
            "No forward return is computed here. No entry is defined. A return test built on `lower HVN → LVN → opposite HVN` as the typical path would be testing the wrong event.",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[step4] wrote {REPORT}", flush=True)


if __name__ == "__main__":
    write()
