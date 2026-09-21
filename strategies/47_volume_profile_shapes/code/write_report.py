"""Write STEP1_PROFILE_SHAPE_REPORT.md from the saved tables.

The verdict uses the rule in frozen.py. This script does not move cutoffs.
"""

from __future__ import annotations

import json

import pandas as pd

from detect_shapes import VERDICT_TEXT, decide
from frozen import (
    BIMODAL_SEPARATION_MIN,
    BIMODAL_VALLEY_DEPTH_MIN,
    BODY_RANGE_FRAC,
    CLASS_B_DOUBLE,
    CLASS_B_LOWER,
    CLASS_D,
    CLASS_P,
    CLASS_UNCLASSIFIED,
    CLEAR_AGREE,
    CLEAR_MIN_EACH,
    CLEAR_UNCLASS_MAX,
    D_CONCENTRATION_MIN,
    D_POC_HI,
    D_POC_LO,
    D_SIDE_BALANCE_MAX,
    D_TAIL_DIFF_MAX,
    MAJOR_PEAK_VOLUME_FRAC,
    NAMED_CLASSES,
    P_ABOVE_SHARE_MIN,
    P_POC_MIN,
    P_TAIL_ASYM_MIN,
    P_UPPER_BODY_MIN,
    POC_BAND_FRAC,
    B_BELOW_SHARE_MIN,
    B_LOWER_BODY_MIN,
    B_POC_MAX,
    B_TAIL_ASYM_MIN,
    PRIMARY_CLASSES,
    PROMINENCE_FRAC,
    RESULTS,
    ROOT,
    SEPARATION_FRAC,
    TAIL_VOLUME_FRAC,
    WEAK_AGREE,
    WEAK_CLASS_COUNT,
    WEAK_MIN_CLASSES,
)


def _num(value, digits: int = 3) -> str:
    if value is None or value != value:
        return "—"
    return f"{float(value):.{digits}f}"


def _pct(count: int, total: int) -> str:
    if not total:
        return "—"
    return f"{100.0 * count / total:.1f}%"


def _counts(frame: pd.DataFrame) -> dict[str, int]:
    counts = {name: 0 for name in PRIMARY_CLASSES}
    if frame.empty:
        return counts
    for name, count in frame["primary_class"].value_counts().items():
        counts[str(name)] = int(count)
    return counts


def _median(series: pd.Series) -> float:
    clean = series.dropna()
    if clean.empty:
        return float("nan")
    return float(clean.median())


def _class_table(frame: pd.DataFrame) -> list[str]:
    counts = _counts(frame)
    total = int(len(frame))
    lines = ["| Primary label | Sessions | Share |", "| --- | ---: | ---: |"]
    for name in PRIMARY_CLASSES:
        lines.append(f"| {name} | {counts[name]} | {_pct(counts[name], total)} |")
    lines.append(f"| Total | {total} | 100% |")
    return lines


def _clause(frame: pd.DataFrame, mask: pd.Series, label: str) -> str:
    count = int(mask.fillna(False).sum())
    return f"| {label} | {count} | {_pct(count, len(frame))} |"


def _flag_line(frame: pd.DataFrame, column: str, label: str) -> str:
    count = int(frame[column].sum()) if len(frame) else 0
    return f"| {label} | {count} | {_pct(count, len(frame))} |"


def _image(record: dict | None, caption: str) -> list[str]:
    if not record:
        return [f"{caption}: not drawn. No analysis-sample session has this primary label.", ""]
    path = record["path"]
    return [f"{caption}: {record['session_date']}.", "", f"![{caption}]({path})", ""]


def build_report() -> str:
    audit = json.loads((RESULTS / "audit_summary.json").read_text(encoding="utf-8"))
    sensitivity = json.loads((RESULTS / "sensitivity_summary.json").read_text(encoding="utf-8"))
    manifest = json.loads((RESULTS / "plot_manifest.json").read_text(encoding="utf-8"))
    data = pd.read_parquet(RESULTS / "profile_shape_dataset.parquet")
    sample = data[data["in_analysis_sample"]].copy()
    counts = _counts(sample)
    n = int(len(sample))
    verdict = decide(
        counts,
        n,
        float(sensitivity["agreement_looser"]),
        float(sensitivity["agreement_stricter"]),
    )
    two_peaks = sample[sample["n_local_maxima"] >= 2]
    lines: list[str] = [
        "# Step 1 — NQ volume-profile shape geometry",
        "",
        "This report does not test profitability, entries, exits, or forward returns.",
        "Class labels were produced by the rules in `PREREGISTRATION.md` and `code/frozen.py`.",
        "Those cutoffs were not moved after the tables below were computed.",
        "",
        "## 1. Dataset audit",
        "",
        f"- Files found: {audit['files_found']} (expected {audit['files_expected']}).",
        f"- Files parsed: {audit['files_parsed']}.",
        f"- Failed or unreadable files: {len(audit['files_failed'])}.",
    ]
    if audit["files_failed"]:
        for item in audit["files_failed"]:
            lines.append(f"  - {item}")
    else:
        lines.append("- No file failed to parse.")
    lines.extend(
        [
            f"- Filename span: `{audit.get('first_file', '')}` through `{audit.get('last_file', '')}`.",
            f"- Filename span mismatch versus the expected 2026-03-25 to 2026-09-16 set: {audit.get('filename_span_mismatch')}.",
            f"- First trade timestamp: {audit['first_timestamp']}.",
            f"- Last trade timestamp: {audit['last_timestamp']}.",
            f"- Total trades: {audit['total_trades']}.",
            f"- Total executed volume (positive size only): {audit['total_volume']}.",
            f"- Rows repeating `(ts_event, sequence, instrument_id)` inside a file: {audit['duplicate_extra_rows_within_files']}. On the first file this key usually groups different prices, so it is not a unique trade id.",
            f"- Exact repeated rows on `(ts_event, sequence, instrument_id, price, size)`: {audit.get('exact_duplicate_extra_rows', 'not counted')}. Repeated rows were not removed. Session volume is the sum of every positive size.",
            f"- Trade actions: {audit.get('action_counts', 'not counted')}. Every parsed row is an executed trade when the only action is T.",
            f"- Consecutive files whose timestamp ranges overlap: {len(audit['cross_file_timestamp_overlaps'])}.",
            f"- Rows in an overlap that repeat the previous file's trade key: {audit['cross_file_duplicate_rows']}.",
            f"- Negative size rows: {audit['negative_size_rows']}. These rows are not added to volume.",
            f"- Sessions assigned: {audit['session_count']}.",
            f"- Calendar dates with no file between the first and last filename date: {len(audit.get('calendar_gaps', []))}. The date list is in `results/audit_summary.json`. A missing file date is not deleted from a session that still has trades.",
            f"- Sessions whose raw volume does not match the session total: {int((~data['volume_matches_meta']).sum())}.",
            "",
            "## 2. Session definition",
            "",
            "Timezone is `America/New_York`. A timestamp at or after 18:00 New York belongs to that calendar date. An earlier timestamp belongs to the previous calendar date. Each profile uses every executed trade in `[18:00, next 18:00)`. The economic close is 17:00. The maintenance break stays inside the window and is not filled in.",
            "",
            "A session is complete when the first trade is within 30 minutes after 18:00 and the last trade is within 30 minutes before 17:00 the next New York day. A roll is an instrument-id change, more than one instrument id in the session, or a gap of at least 150 points between the previous session's last trade and this session's first trade. The first session is a roll only if it contains two instrument ids.",
            "",
            f"- Complete sessions: {int(data['is_complete'].sum())}.",
            f"- Roll-transition sessions: {int(data['is_roll_transition'].sum())}.",
            f"- Analysis sample (complete, not a roll, positive volume and range, no symbol/file/range failure): {n}.",
            "- No complete session is a roll transition, so the analysis sample is exactly the complete sessions."
            if int((data["is_roll_transition"] & data["is_complete"]).sum()) == 0
            else f"- Complete sessions that are also rolls, excluded from the analysis sample: {int((data['is_roll_transition'] & data['is_complete']).sum())}.",
            "",
            "Incomplete sessions, roll sessions, and corrupt sessions remain in `results/profile_shape_dataset.parquet`. They are excluded from the primary counts, the monthly table, the sensitivity agreement, and the shape examples. That exclusion was declared before classification.",
            "",
            "## 3. Profile construction",
            "",
            "Volume is the sum of executed trade size at each 0.25-point NQ tick. Databento prices with absolute value above 1,000,000 are divided by 1e9 before rounding to the tick. Bars, quotes, and the book are not used. Untraded ticks between the lowest and highest traded price are stored with volume 0. The series is not smoothed.",
            "",
            "Raw rows, including a running cumulative volume from the low, are in `results/raw_price_volume.parquet`.",
            "",
            "## 4. Exact mathematical definitions",
            "",
            "Let `k = 0 .. R` be ticks from the low, volume `v_k`, total `V`. `R = 0` is degenerate and is not classified.",
            "",
            "- POC is the smallest `k` with maximum `v_k`. POC location is `k / R`.",
            "- Volume-weighted mean and population standard deviation are moments of this price distribution. They are saved so sessions can be compared. They are not an intraday VWAP and they are not inputs to the class rules.",
            f"- Above-share is volume strictly above the midpoint divided by volume strictly above plus strictly below. The midpoint tick, when `R` is even, is excluded from both sides.",
            f"- A 10% tail width is the smallest fraction of the range, walking inward from that extreme, that accumulates at least {TAIL_VOLUME_FRAC:.0%} of `V`. A wider tail is thinner volume.",
            f"- Upper-body share is volume at prices at or above `high - {BODY_RANGE_FRAC:.0%} of range`. Lower-body share uses the bottom {BODY_RANGE_FRAC:.0%}.",
            f"- POC concentration is volume within `max({POC_BAND_FRAC:.0%} of range, one tick)` of the POC, divided by `V`.",
            f"- Local maxima use `find_peaks` on the raw grid after flat peaks are represented by their lower-price edge. Baseline prominence is {PROMINENCE_FRAC:.0%} of POC volume. Baseline separation is {SEPARATION_FRAC:.0%} of `R`, and at least one tick.",
            f"- A maximum is major when its volume is at least {MAJOR_PEAK_VOLUME_FRAC:.0%} of POC volume. The POC is kept if the distance filter drops it.",
            "- For the two largest local maxima, ordered with peak 1 at the lower price: `normalized_separation = |peak2 - peak1| / range`, `valley_ratio = V_valley / V_min_peak`, `valley_depth = 1 - valley_ratio`. The valley is the minimum original volume strictly between the peaks. Ties use the tick closest to the midpoint, then the lower tick.",
            "",
            "## 5. Classification rules",
            "",
            "Flags may overlap. Primary label is the single true flag. Zero flags, or two or more flags, are `UNCLASSIFIED`. Two or more flags also set `conflict`. Three or more major peaks set `flag_multimodal` and do not receive the B-like flag.",
            "",
            f"- P-like: POC location ≥ {P_POC_MIN:.2f}, above-share ≥ {P_ABOVE_SHARE_MIN:.2f}, lower tail − upper tail ≥ {P_TAIL_ASYM_MIN:.2f}, upper-body share ≥ {P_UPPER_BODY_MIN:.2f}.",
            f"- b-like: POC location ≤ {B_POC_MAX:.2f}, below-share ≥ {B_BELOW_SHARE_MIN:.2f}, upper tail − lower tail ≥ {B_TAIL_ASYM_MIN:.2f}, lower-body share ≥ {B_LOWER_BODY_MIN:.2f}.",
            f"- D-like: POC location in [{D_POC_LO:.2f}, {D_POC_HI:.2f}], |above-share − 0.50| ≤ {D_SIDE_BALANCE_MAX:.2f}, |upper tail − lower tail| ≤ {D_TAIL_DIFF_MAX:.2f}, exactly one major peak, POC concentration ≥ {D_CONCENTRATION_MIN:.2f}.",
            f"- B-like: exactly two major peaks, normalized separation ≥ {BIMODAL_SEPARATION_MIN:.2f}, valley depth ≥ {BIMODAL_VALLEY_DEPTH_MIN:.2f}.",
            "",
            "P is not treated as bullish, b is not treated as bearish, and D is not treated as neutral.",
            "",
            "## 6. Number of profiles in each class",
            "",
            "Primary labels on the analysis sample:",
            "",
        ]
    )
    lines.extend(_class_table(sample))
    lines.extend(
        [
            "",
            "Overlapping flags on the analysis sample. These counts are not exclusive.",
            "",
            "| Flag | Sessions | Share of analysis sample |",
            "| --- | ---: | ---: |",
            _flag_line(sample, "flag_p", "P-like geometry"),
            _flag_line(sample, "flag_b", "b-like geometry"),
            _flag_line(sample, "flag_d", "D-like geometry"),
            _flag_line(sample, "flag_bimodal", "B-like / two major peaks with a valley"),
            _flag_line(sample, "flag_multimodal", "Three or more major peaks"),
            _flag_line(sample, "conflict", "Two or more shape flags"),
            "",
            f"Sessions with both a P-like flag and a B-like flag: {int((sample['flag_p'] & sample['flag_bimodal']).sum())}.",
            f"Sessions with both a b-like flag and a B-like flag: {int((sample['flag_b'] & sample['flag_bimodal']).sum())}.",
            "",
            "How many analysis sessions pass each clause on its own. A primary label still requires the whole clause list. These counts are not a second classifier.",
            "",
            "| Clause | Sessions | Share |",
            "| --- | ---: | ---: |",
            _clause(sample, sample["poc_location"] >= P_POC_MIN, "P: POC in the top 30% of the range"),
            _clause(sample, sample["volume_above_share"] >= P_ABOVE_SHARE_MIN, "P: at least 62% of sided volume above the midpoint"),
            _clause(sample, sample["tail_asymmetry_lower_minus_upper"] >= P_TAIL_ASYM_MIN, "P: lower tail at least 0.20 wider than the upper tail"),
            _clause(sample, sample["upper_body_share"] >= P_UPPER_BODY_MIN, "P: at least 55% of volume in the top 30% of the range"),
            _clause(sample, sample["poc_location"] <= B_POC_MAX, "b: POC in the bottom 30% of the range"),
            _clause(sample, sample["volume_below_share"] >= B_BELOW_SHARE_MIN, "b: at least 62% of sided volume below the midpoint"),
            _clause(sample, -sample["tail_asymmetry_lower_minus_upper"] >= B_TAIL_ASYM_MIN, "b: upper tail at least 0.20 wider than the lower tail"),
            _clause(sample, sample["lower_body_share"] >= B_LOWER_BODY_MIN, "b: at least 55% of volume in the bottom 30% of the range"),
            _clause(sample, (sample["poc_location"] >= D_POC_LO) & (sample["poc_location"] <= D_POC_HI), "D: POC between 40% and 60% of the range"),
            _clause(sample, sample["volume_above_share"].sub(0.5).abs() <= D_SIDE_BALANCE_MAX, "D: above-share within 0.10 of one half"),
            _clause(sample, sample["upper_tail_width_10"].sub(sample["lower_tail_width_10"]).abs() <= D_TAIL_DIFF_MAX, "D: tail widths within 0.12"),
            _clause(sample, sample["n_major_peaks"] == 1, "D: exactly one major peak"),
            _clause(sample, sample["poc_concentration_10"] >= D_CONCENTRATION_MIN, "D: at least 45% of volume in the POC band"),
            _clause(sample, sample["n_major_peaks"] == 2, "B: exactly two major peaks"),
            _clause(sample, sample["normalized_separation"] >= BIMODAL_SEPARATION_MIN, "B: normalized separation at least 0.20"),
            _clause(sample, sample["valley_depth"] >= BIMODAL_VALLEY_DEPTH_MIN, "B: valley depth at least 0.30"),
            "",
            "Primary labels on every saved session, including incomplete and roll sessions:",
            "",
        ]
    )
    lines.extend(_class_table(data))
    lines.extend(
        [
            "",
            "## 7. Shape distributions",
            "",
            "The file set runs from late March 2026 through 16 September 2026. These frequencies are not a claim about long-term NQ behavior.",
            "",
            f"- Analysis sessions: {n}.",
            f"- Median profile range: {_num(_median(sample['profile_range']), 2)} points.",
            f"- Median POC location: {_num(_median(sample['poc_location']), 3)} (0 at the low, 1 at the high).",
            f"- Median normalized separation, among analysis sessions with at least two local maxima (n={len(two_peaks)}): {_num(_median(two_peaks['normalized_separation']), 3)}.",
            f"- Median valley depth on that same subset: {_num(_median(two_peaks['valley_depth']), 3)}.",
            f"- Median number of major peaks: {_num(_median(sample['n_major_peaks']), 2)}.",
            "",
            "Major-peak counts on the analysis sample:",
            "",
            "| Major peaks | Sessions |",
            "| ---: | ---: |",
        ]
    )
    if n:
        for peaks, count in sample["n_major_peaks"].value_counts().sort_index().items():
            lines.append(f"| {int(peaks)} | {int(count)} |")
    lines.extend(["", "By month, analysis sample only:", ""])
    lines.append(
        "| Month | Sessions | P-like | b-like | D-like | B-like | Unclassified | Median range | Median POC location | Median separation | Median valley depth |"
    )
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    if n:
        sample = sample.copy()
        sample["month"] = sample["session_date"].astype(str).str.slice(0, 7)
        for month, part in sample.groupby("month", sort=True):
            month_counts = _counts(part)
            both = part[part["n_local_maxima"] >= 2]
            lines.append(
                "| {month} | {sessions} | {p} | {b} | {d} | {bb} | {u} | {rng} | {poc} | {sep} | {depth} |".format(
                    month=month,
                    sessions=len(part),
                    p=month_counts[CLASS_P],
                    b=month_counts[CLASS_B_LOWER],
                    d=month_counts[CLASS_D],
                    bb=month_counts[CLASS_B_DOUBLE],
                    u=month_counts[CLASS_UNCLASSIFIED],
                    rng=_num(_median(part["profile_range"]), 1),
                    poc=_num(_median(part["poc_location"]), 2),
                    sep=_num(_median(both["normalized_separation"]), 2),
                    depth=_num(_median(both["valley_depth"]), 2),
                )
            )
    lines.extend(
        [
            "",
            "Median separation and valley depth in a month use only that month's analysis sessions that have at least two local maxima. A dash means that month has none.",
            "",
            "## 8. Double-distribution statistics",
            "",
            f"Analysis sessions with at least two prominence-qualified local maxima: {len(two_peaks)} ({_pct(len(two_peaks), n)}).",
            f"Exactly two major peaks: {int((sample['n_major_peaks'] == 2).sum())}.",
            f"Three or more major peaks: {int((sample['n_major_peaks'] >= 3).sum())}.",
            f"Primary B-like labels: {counts[CLASS_B_DOUBLE]}.",
            "",
            "On analysis sessions with at least two local maxima:",
            "",
            f"- Median peak separation: {_num(_median(two_peaks['peak_separation']), 2)} points.",
            f"- Median normalized separation: {_num(_median(two_peaks['normalized_separation']), 3)}.",
            f"- Median valley ratio: {_num(_median(two_peaks['valley_ratio']), 3)}.",
            f"- Median valley depth: {_num(_median(two_peaks['valley_depth']), 3)}.",
            f"- Median peak balance (smaller / larger): {_num(_median(two_peaks['peak_balance']), 3)}.",
            "",
            "The same medians on the primary B-like subset:",
            "",
        ]
    )
    b_like = sample[sample["primary_class"] == CLASS_B_DOUBLE]
    lines.extend(
        [
            f"- Sessions: {len(b_like)}.",
            f"- Median normalized separation: {_num(_median(b_like['normalized_separation']), 3)}.",
            f"- Median valley depth: {_num(_median(b_like['valley_depth']), 3)}.",
            f"- Median peak balance: {_num(_median(b_like['peak_balance']), 3)}.",
            "",
            "Valley depth uses the unsmoothed grid, so a one-tick hole can make a deep valley next to a small second peak. The major-peak rule, volume at least half of the POC, is what stops that hole from becoming a B label. Depth by itself is not treated as a double distribution.",
            "",
            "Node prices and volumes for every session are in `results/nodes.parquet` and in the JSON columns of the session dataset.",
            "",
            "## 9. Sensitivity analysis",
            "",
            "Only prominence and separation move. The P, b, D, and valley cutoffs stay at the preregistered values.",
            "",
            "| Setting | Prominence | Separation | Agreement with baseline | P-like | b-like | D-like | B-like | Unclassified |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for item in sensitivity["settings"]:
        item_counts = item["counts"]
        lines.append(
            "| {name} | {prom:.2f} | {sep:.2f} | {agree} | {p} | {b} | {d} | {bb} | {u} |".format(
                name=item["name"],
                prom=item["prominence_frac"],
                sep=item["separation_frac"],
                agree=_num(item["agreement_with_baseline"], 3),
                p=item_counts.get(CLASS_P, 0),
                b=item_counts.get(CLASS_B_LOWER, 0),
                d=item_counts.get(CLASS_D, 0),
                bb=item_counts.get(CLASS_B_DOUBLE, 0),
                u=item_counts.get(CLASS_UNCLASSIFIED, 0),
            )
        )
    lines.extend(
        [
            "",
            f"Baseline versus looser agreement: {_num(sensitivity['agreement_looser'], 3)}.",
            f"Baseline versus stricter agreement: {_num(sensitivity['agreement_stricter'], 3)}.",
            "",
            "Label changes, analysis sample, baseline to looser:",
            "",
        ]
    )
    for key, count in sensitivity["transitions_looser"].items():
        if "->" in key and key.split(" -> ")[0] != key.split(" -> ")[1]:
            lines.append(f"- {key}: {count}")
    if not any(k.split(" -> ")[0] != k.split(" -> ")[1] for k in sensitivity["transitions_looser"]):
        lines.append("- No label changes.")
    lines.extend(["", "Label changes, analysis sample, baseline to stricter:", ""])
    for key, count in sensitivity["transitions_stricter"].items():
        if key.split(" -> ")[0] != key.split(" -> ")[1]:
            lines.append(f"- {key}: {count}")
    if not any(k.split(" -> ")[0] != k.split(" -> ")[1] for k in sensitivity["transitions_stricter"]):
        lines.append("- No label changes.")
    if sensitivity["unstable"]:
        lines.extend(
            [
                "",
                "The concept is unstable under the preregistered sensitivity. Agreement is below "
                f"{WEAK_AGREE:.0%} on at least one of the two small parameter moves.",
            ]
        )
    else:
        lines.extend(
            [
                "",
                "Full-label agreement stays at or above "
                f"{WEAK_AGREE:.0%} on both settings. Most of that agreement is sessions that stay unclassified.",
            ]
        )
    labels = pd.read_parquet(RESULTS / "sensitivity_labels.parquet")
    held_labels = labels[labels["in_analysis_sample"]]
    gained = held_labels[
        (held_labels["baseline"] == CLASS_UNCLASSIFIED) & (held_labels["stricter"] == CLASS_B_DOUBLE)
    ]
    lost = held_labels[
        (held_labels["baseline"] == CLASS_B_DOUBLE) & (held_labels["looser"] == CLASS_UNCLASSIFIED)
    ]
    b_span = ", ".join(
        f"{item['name']} {item['counts'].get(CLASS_B_DOUBLE, 0)}" for item in sensitivity["settings"]
    )
    lines.extend(["", f"The B-like count itself does not sit still: {b_span}."])
    if len(gained):
        gained_peaks = data.set_index("session_date").loc[gained["session_date"], "n_major_peaks"]
        lines.append(
            f"{len(gained)} sessions move from unclassified to B-like when the extrema rule is tightened. "
            f"At the baseline they have {int(gained_peaks.min())} to {int(gained_peaks.max())} major peaks, "
            "so they miss the exactly-two-peak rule until a stricter prominence drops the extra peaks."
        )
    else:
        lines.append("No unclassified session becomes B-like under the stricter setting.")
    lines.extend(
        [
            f"{len(lost)} baseline B-like sessions move to unclassified when the extrema rule is loosened.",
            "The double-distribution count moves with that small setting change. Most other labels do not, which is why full-label agreement stays high.",
            (
                "The D-like count stays at zero in all three settings."
                if all(item["counts"].get(CLASS_D, 0) == 0 for item in sensitivity["settings"])
                else "The D-like column in the table above shows whether a single centered bell appears under the other settings."
            ),
            "",
        ]
    )
    lines.extend(["", "## 10. Visual examples", ""])
    lines.append(
        "Plots use one color for every class. The title is the algorithm's label. "
        "Random draws use NumPy seed 42. They are not a hand-picked gallery."
    )
    lines.append("")
    for name in NAMED_CLASSES:
        lines.extend(_image(manifest["strongest"].get(name), f"Strongest {name}"))
    amb = manifest.get("ambiguous")
    amb_caption = (
        "Unclassified because two shape flags are both true"
        if amb and amb.get("conflict")
        else "Unclassified session closest to a rule"
    )
    lines.extend(_image(amb, amb_caption))
    lines.extend(["Random draws:", ""])
    for name in PRIMARY_CLASSES:
        draws = manifest["random"].get(name, [])
        if not draws:
            lines.append(f"- {name}: no analysis-sample session.")
            continue
        for record in draws:
            lines.append(f"- {name}: {record['session_date']} (`{record['path']}`)")
    if manifest.get("missing"):
        lines.extend(["", "Plots not drawn:"])
        for item in manifest["missing"]:
            lines.append(f"- {item}")
    if manifest.get("roll_artifact"):
        lines.extend(["", "Roll sessions are not shape examples. One roll that received a B-like primary label is shown only as a data-quality check.", ""])
        lines.extend(_image(manifest["roll_artifact"], "Roll artifact"))
    lines.append("")
    lines.extend(
        [
            "## 11. Data-quality issues",
            "",
            f"- Incomplete sessions: {int((~data['is_complete']).sum())}. They stay in the dataset and out of the analysis sample.",
            f"- Roll-transition sessions: {int(data['is_roll_transition'].sum())}. Dates: "
            + ", ".join(data.loc[data["is_roll_transition"], "session_date"].astype(str).tolist())
            + ".",
            f"- Sessions with a file-level problem (unexpected symbol, tick rounding above 1e-4, or a negative size): {int(data['file_problem'].sum())}.",
            f"- Corrupt ranges above 500,000 ticks: {int(data['corrupt_range'].sum())}.",
            f"- Non-contiguous raw grids: {int(data['noncontiguous_grid'].sum())}.",
            f"- Degenerate profiles: {int(data['degenerate'].sum())}.",
            "",
            "Primary labels on roll-transition sessions only:",
            "",
        ]
    )
    lines.extend(_class_table(data[data["is_roll_transition"]]))
    lines.extend(
        [
            "",
            "Primary labels on incomplete sessions only:",
            "",
        ]
    )
    lines.extend(_class_table(data[~data["is_complete"]]))
    lines.extend(
        [
            "",
            "A contract roll can open a price gap and create a false valley. That is why rolls are flagged and kept out of the analysis sample rather than used as evidence of a double distribution.",
            "",
            "## 12. Limitations",
            "",
            "The sample is about six months, March through mid-September 2026, not a multi-year NQ record. Shape frequencies here should not be quoted as the long-run mix.",
            "",
            "The class rules are round structural cutoffs chosen before this run. They were not fit to maximize how many sessions look like a textbook picture. Many sessions are allowed to stay unclassified. A profile can carry two flags; it is then unclassified rather than forced into one name.",
            "",
            "Local peaks use prominence and a minimum separation, which is a definition choice, not a smoother. The sensitivity section is the check on that choice. No ATR, VWAP filter, previous-day direction, order-flow feature, entry, stop, target, or forward return enters the label.",
            "",
            f"The verdict rule, also frozen beforehand, calls the structure clear only when each named class has at least {CLEAR_MIN_EACH} analysis sessions, both sensitivity agreements are at least {CLEAR_AGREE:.0%}, and the unclassified share is below {CLEAR_UNCLASS_MAX:.0%}. It calls the structure weak when that fails but at least {WEAK_MIN_CLASSES} named classes have at least {WEAK_CLASS_COUNT} sessions and both agreements are at least {WEAK_AGREE:.0%}. Otherwise there is no clear structure.",
            "",
            f"### {verdict}",
            "",
            VERDICT_TEXT[verdict],
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    text = build_report()
    path = ROOT / "STEP1_PROFILE_SHAPE_REPORT.md"
    path.write_text(text, encoding="utf-8")
    print(f"[report] wrote {path}", flush=True)


if __name__ == "__main__":
    main()
