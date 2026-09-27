"""Write the Step 2 report from the stored tables.

Does not remeasure regions and does not add a cutoff.
"""

from __future__ import annotations

import pandas as pd

from frozen import RESULTS

ROOT = RESULTS.parents[0]
REPORT = ROOT / "STEP2_NODE_STRUCTURE_REPORT.md"


def _q(series: pd.Series, prob: float) -> float:
    return float(series.quantile(prob, interpolation="linear"))


def _fmt(value: float, digits: int = 3) -> str:
    if value != value:
        return ""
    return f"{value:.{digits}f}"


def _pct_row(series: pd.Series) -> str:
    probs = (0.0, 0.10, 0.25, 0.50, 0.75, 0.90, 1.0)
    return " | ".join(_fmt(_q(series, prob)) for prob in probs)


def _count_table(frame: pd.DataFrame, column: str, order: list[str]) -> str:
    counts = frame[column].value_counts()
    lines = ["| Bin | Sessions | Share |", "| --- | ---: | ---: |"]
    n = len(frame)
    for name in order:
        count = int(counts.get(name, 0))
        lines.append(f"| {name} | {count} | {count / n:.1%} |")
    return "\n".join(lines)


def write() -> None:
    sessions = pd.read_csv(RESULTS / "step2_sessions.csv")
    gaps = pd.read_csv(RESULTS / "step2_gaps.csv")
    sensitivity = pd.read_csv(RESULTS / "step2_sensitivity.csv")
    sessions["session_date"] = sessions["session_date"].astype(str)
    gaps["session_date"] = gaps["session_date"].astype(str)
    n = len(sessions)
    two = sessions.loc[sessions["structure"] == "two_regions"].copy()
    one = sessions.loc[sessions["structure"] == "one_region"].copy()
    many = sessions.loc[sessions["structure"] == "many_regions"].copy()
    clean = sessions.loc[sessions["clean_two"]].copy()
    material = gaps.loc[gaps["material"]].copy()
    weak = gaps.loc[~gaps["material"]].copy()
    depth_min = float(gaps["valley_depth"].min())
    weak_sep_fail = int((weak["separation"] < 0.20).sum())
    weak_depth_fail = int((weak["valley_depth"] < 0.30).sum())
    thin_two = int((two["second_region_share"] < 0.25).sum())
    balanced_two = int((two["second_region_share"] >= 0.30).sum())
    thin_clean = int((clean["second_region_share"] < 0.25).sum())
    balanced_clean = int((clean["second_region_share"] >= 0.30).sum())
    two_with_minor = int((two["weak_minor_peaks_between"] > 0).sum())
    material_with_minor = int(((material["minor_peaks_between"] > 0)).sum())
    one_multi = int((one["n_major_peaks"] >= 2).sum())

    cross = pd.crosstab(sessions["dominant_third"], sessions["structure"]).reindex(
        index=["lower", "middle", "upper"],
        columns=["one_region", "two_regions", "many_regions"],
        fill_value=0,
    )
    cross_lines = ["| Dominant third | One region | Two regions | Three regions |", "| --- | ---: | ---: | ---: |"]
    for name, row in cross.iterrows():
        cross_lines.append(
            f"| {name} | {int(row['one_region'])} | {int(row['two_regions'])} | {int(row['many_regions'])} |"
        )

    label_cross = pd.crosstab(sessions["primary_class"], sessions["structure"]).reindex(
        index=["P-like", "b-like", "D-like", "B-like", "UNCLASSIFIED"],
        columns=["one_region", "two_regions", "many_regions"],
        fill_value=0,
    )
    label_lines = ["| Step 1 label | One region | Two regions | Three regions |", "| --- | ---: | ---: | ---: |"]
    for name, row in label_cross.iterrows():
        label_lines.append(
            f"| {name} | {int(row['one_region'])} | {int(row['two_regions'])} | {int(row['many_regions'])} |"
        )

    ranked = two.sort_values(
        ["weak_depth", "weak_separation", "session_date"],
        ascending=[False, False, True],
        kind="mergesort",
    ).head(10)
    rank_lines = [
        "| Rank | Session | Step 1 | Depth | Separation | Smaller share | Minors in gap | Clean |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for rank, row in enumerate(ranked.itertuples(index=False), start=1):
        rank_lines.append(
            f"| {rank} | {row.session_date} | {row.primary_class} | {_fmt(row.weak_depth)} | "
            f"{_fmt(row.weak_separation)} | {_fmt(row.second_region_share)} | "
            f"{int(row.weak_minor_peaks_between)} | {'yes' if row.clean_two else 'no'} |"
        )

    many_sorted = many.sort_values(["n_regions", "session_date"], ascending=[False, True], kind="mergesort")
    many_lines = [
        "| Session | Regions | Major peaks | Weakest depth | Strongest depth | Largest share |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in many_sorted.itertuples(index=False):
        many_lines.append(
            f"| {row.session_date} | {int(row.n_regions)} | {int(row.n_major_peaks)} | "
            f"{_fmt(row.weak_depth)} | {_fmt(row.strong_depth)} | {_fmt(row.largest_region_share)} |"
        )

    base = sensitivity.loc[sensitivity["setting"] == "baseline", ["session_date", "n_regions"]].rename(
        columns={"n_regions": "baseline_regions"}
    )
    sens_lines = [
        "| Setting | Prominence | Separation | One | Two | Three or more | Clean two | Same region count as baseline |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for setting, prominence, separation in (
        ("baseline", 0.20, 0.10),
        ("looser", 0.12, 0.06),
        ("stricter", 0.30, 0.15),
    ):
        part = sensitivity.loc[sensitivity["setting"] == setting]
        merged = base.merge(part, on="session_date", how="inner")
        same = int((merged["baseline_regions"] == merged["n_regions"]).sum())
        sens_lines.append(
            f"| {setting} | {_fmt(prominence, 2)} | {_fmt(separation, 2)} | "
            f"{int((part['structure'] == 'one_region').sum())} | "
            f"{int((part['structure'] == 'two_regions').sum())} | "
            f"{int((part['structure'] == 'many_regions').sum())} | "
            f"{int(part['clean_two'].sum())} | {same} of {n} |"
        )

    b_like = sessions.loc[sessions["primary_class"] == "B-like"]
    b_clean = int(b_like["clean_two"].sum())
    random_dates = (RESULTS / "figures" / "step2" / "random_dates.txt").read_text(encoding="utf-8").split()
    random_rows = sessions.set_index("session_date").loc[random_dates]
    random_bits = [
        f"{date} ({row.structure.replace('_', ' ')}, Step 1 {row.primary_class})"
        for date, row in random_rows.iterrows()
    ]

    text = f"""# Step 2 — Accepted volume regions

This report does not test profitability, entries, exits, or forward returns. Region counts use the rules in `STEP2_PREREGISTRATION.md`. Those rules were not changed after the tables or the pictures were seen. `one_region`, `two_regions`, and `many_regions` are bins of a count. They are not P, b, D, or B labels, and they are not a trading setup.

## A. Dataset verification

The run stopped unless the stored Step 1 sample still matched the Step 1 report, and unless the recomputed peaks and concentration matched the stored geometry.

- Analysis sessions: {n}.
- Stored `in_analysis_sample` matches `analysis_mask`.
- Primary labels: P-like 1, b-like 2, D-like 0, B-like 7, UNCLASSIFIED 86.
- Recomputed POC location, `vw_std_norm`, `poc_concentration_10`, major-peak count, and local-maximum count match the stored Step 1 columns on every analysis session.
- Region volumes sum to the session volume on every analysis session.
- Detail is in `results/step2_verification.json`.

The peak detector, the 50% major-peak rule, and the 0.20 / 0.30 gap cuts are the Step 1 constants. Nothing in this file refits them.

## B. What was measured

Four facts, kept separate.

Location is the share of volume in the lower, middle, and upper third of the session's own price range. The dominant third is the largest share. An exact tie would go to lower, then middle. The name is only a label for the cross-tab.

Concentration is `vw_std_norm` and `poc_concentration_10`. A larger standard deviation is a broader profile. A larger POC concentration is a tighter band around the POC. The share of volume in the largest region is not concentration: one region can cover a wide day.

Modality is the number of accepted regions. Only major peaks seed a region. Adjacent major peaks stay in one region unless the gap between them is material: separation at least 0.20 of the range and valley depth at least 0.30. A material gap is clean when no other detected local maximum sits strictly between those two major peaks.

Separation is reported on those adjacent gaps. The deepest gap is not a score for the session.

## C. Location

| Third | Sessions where it dominates | Share of sessions |
| --- | ---: | ---: |
| Middle | {int((sessions['dominant_third'] == 'middle').sum())} | {(sessions['dominant_third'] == 'middle').mean():.1%} |
| Upper | {int((sessions['dominant_third'] == 'upper').sum())} | {(sessions['dominant_third'] == 'upper').mean():.1%} |
| Lower | {int((sessions['dominant_third'] == 'lower').sum())} | {(sessions['dominant_third'] == 'lower').mean():.1%} |

Volume shares across the 96 sessions:

| Share | Min | p10 | p25 | Median | p75 | p90 | Max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Lower third | {_pct_row(sessions['lower_share'])} |
| Middle third | {_pct_row(sessions['middle_share'])} |
| Upper third | {_pct_row(sessions['upper_share'])} |

The middle third is the most common place for the plurality of volume. Upper dominates twice as often as lower. That is the same direction as Step 1, where a P-like profile existed and a b-like profile was rarer, but it is not a letter classification. The median middle share is {_fmt(_q(sessions['middle_share'], 0.5))}. No third is empty on the median day.

{chr(10).join(cross_lines)}

## D. Concentration

| Measure | Min | p10 | p25 | Median | p75 | p90 | Max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `vw_std_norm` | {_pct_row(sessions['vw_std_norm'])} |
| `poc_concentration_10` | {_pct_row(sessions['poc_concentration_10'])} |

The normalized standard deviation sits in a narrow band, from {_fmt(sessions['vw_std_norm'].min())} to {_fmt(sessions['vw_std_norm'].max())}. Median POC concentration is {_fmt(_q(sessions['poc_concentration_10'], 0.5))}. Days with one accepted region are a little tighter than days with more than one. Medians:

| Structure | Sessions | Median `vw_std_norm` | Median POC concentration | Median major peaks |
| --- | ---: | ---: | ---: | ---: |
| One region | {len(one)} | {_fmt(one['vw_std_norm'].median())} | {_fmt(one['poc_concentration_10'].median())} | {_fmt(one['n_major_peaks'].median(), 1)} |
| Two regions | {len(two)} | {_fmt(two['vw_std_norm'].median())} | {_fmt(two['poc_concentration_10'].median())} | {_fmt(two['n_major_peaks'].median(), 1)} |
| Three regions | {len(many)} | {_fmt(many['vw_std_norm'].median())} | {_fmt(many['poc_concentration_10'].median())} | {_fmt(many['n_major_peaks'].median(), 1)} |

The shift is small next to the spread inside each bin. Concentration does not separate the region counts into different kinds of day.

## E. Modality

Major-peak counts and region counts are not the same object.

| Count | Major peaks | Accepted regions |
| --- | ---: | ---: |
| Min | {int(sessions['n_major_peaks'].min())} | {int(sessions['n_regions'].min())} |
| Median | {_fmt(_q(sessions['n_major_peaks'], 0.5), 1)} | {_fmt(_q(sessions['n_regions'], 0.5), 1)} |
| Max | {int(sessions['n_major_peaks'].max())} | {int(sessions['n_regions'].max())} |

{_count_table(sessions, 'structure', ['one_region', 'two_regions', 'many_regions']).replace('one_region', 'One region').replace('two_regions', 'Two regions').replace('many_regions', 'Three or more')}

No session produced four or more accepted regions. The maximum is 3. The median session has one accepted region and three major peaks.

Of the {len(one)} one-region sessions, {one_multi} still contain two or more major peaks. Those peaks were not split apart because the gap between them failed the material test. One accepted region does not mean one peak. It means the major peaks that do exist are not far enough apart under the frozen rule.

The {len(many)} sessions with three regions are the ones the merge could not collapse. They are listed in section H. None has more than three regions.

## F. Separation

There are {len(gaps)} gaps between price-adjacent major peaks. {len(material)} are material. {int(material['clean'].sum())} of those are clean. {material_with_minor} of the {len(material)} material gaps have at least one other local maximum between the two major peaks.

The depth cut does not bind. Every adjacent major-peak gap in this sample has valley depth at least {_fmt(depth_min)}. Of the {len(weak)} gaps that are not material, {weak_sep_fail} fail because separation is below 0.20, and {weak_depth_fail} fail because depth is below 0.30. The non-material gaps are the closer pairs. Their separation percentiles (p10, median, p90) are {_fmt(_q(weak['separation'], 0.1))}, {_fmt(_q(weak['separation'], 0.5))}, {_fmt(_q(weak['separation'], 0.9))}. Their depth percentiles at the same points are {_fmt(_q(weak['valley_depth'], 0.1))}, {_fmt(_q(weak['valley_depth'], 0.5))}, {_fmt(_q(weak['valley_depth'], 0.9))}.

A close pair of major peaks still has a deep tick valley. The minimum tick between them is a poor description of an empty zone. On this sample, region membership is decided by whether the two major peaks are at least 20% of the range apart.

Material gaps that do pass that distance cut have separation percentiles (p10, median, p90) {_fmt(_q(material['separation'], 0.1))}, {_fmt(_q(material['separation'], 0.5))}, {_fmt(_q(material['separation'], 0.9))}, and depth percentiles {_fmt(_q(material['valley_depth'], 0.1))}, {_fmt(_q(material['valley_depth'], 0.5))}, {_fmt(_q(material['valley_depth'], 0.9))}. Depth among the survivors is high because depth was already high before the cut.

## G. Two regions are not two equal masses

A second region is seeded by a major peak, which is a height rule: the peak tick is at least half of POC volume. The region's share of the day's volume can still be small.

Among the {len(two)} two-region sessions:

| | Smaller region's volume share |
| --- | --- |
| Min, p25, median, p75, max | {_fmt(two['second_region_share'].min())}, {_fmt(_q(two['second_region_share'], 0.25))}, {_fmt(two['second_region_share'].median())}, {_fmt(_q(two['second_region_share'], 0.75))}, {_fmt(two['second_region_share'].max())} |
| Smaller share below 0.25 | {thin_two} |
| Smaller share at least 0.30 | {balanced_two} |

Median split is about {_fmt(two['largest_region_share'].median())} / {_fmt(two['second_region_share'].median())}. That is a real second mass on the median two-region day. It is not what the deepest-gap ranking shows. {thin_two} of these 40 days put less than a quarter of the volume in the smaller region.

`clean_two` is narrower: two regions and no other detected peak in the gap. There are {len(clean)} such sessions. {thin_clean} of them still have a smaller share below 0.25, and {balanced_clean} have a smaller share of at least 0.30. An empty gap is not the same thing as two substantial masses. 2026-08-04 is clean, with valley depth {_fmt(float(clean.loc[clean['session_date'] == '2026-08-04', 'weak_depth'].iloc[0]))} and a smaller share of {_fmt(float(clean.loc[clean['session_date'] == '2026-08-04', 'second_region_share'].iloc[0]))}. 2026-07-28 is clean, with a smaller share of {_fmt(float(clean.loc[clean['session_date'] == '2026-07-28', 'second_region_share'].iloc[0]))}.

{two_with_minor} of the {len(two)} two-region sessions have another local maximum inside the one material gap. The distance rule called the gap material. The gap is often not an empty shelf.

The depth-ranked gallery is `results/figures/step2/gallery_two_regions.png`. It is the first 10 of {len(two)} by valley depth, not a sample of balanced splits.

{chr(10).join(rank_lines)}

2026-04-13, in that list, is the near-even case: smaller share {_fmt(float(two.loc[two['session_date'] == '2026-04-13', 'second_region_share'].iloc[0]))}. 2026-04-01, a Step 1 B-like session, has smaller share {_fmt(float(two.loc[two['session_date'] == '2026-04-01', 'second_region_share'].iloc[0]))} and separation {_fmt(float(two.loc[two['session_date'] == '2026-04-01', 'weak_separation'].iloc[0]))}, with one minor peak in the gap. The same sheet contains both objects. Sorting by depth does not tell them apart.

## H. Three-region sessions

All {len(many)} are Step 1 UNCLASSIFIED. None is `clean_two`. Largest region share runs from {_fmt(many['largest_region_share'].min())} to {_fmt(many['largest_region_share'].max())}. The deepest gap on these days is not a description of the whole profile: each of them also has a second material gap.

{chr(10).join(many_lines)}

The contact sheet is `results/figures/step2/gallery_many_regions.png`.

## I. Step 1 labels

This is a consistency check. The region rule does not use the Step 1 label.

{chr(10).join(label_lines)}

All {len(b_like)} Step 1 B-like sessions fall in the two-region bin. {b_clean} of them are clean. Their smaller-region shares run from {_fmt(b_like['second_region_share'].min())} to {_fmt(b_like['second_region_share'].max())}. The Step 1 rule required exactly two major peaks, so these seven were already the days without a third major peak. They are not the days with the deepest gaps, and they are not a new result.

The one Step 1 P-like session, 2026-04-07, is one region with the upper third holding {_fmt(float(sessions.loc[sessions['session_date'] == '2026-04-07', 'upper_share'].iloc[0]))} of volume. The two b-like sessions, 2026-06-22 and 2026-08-17, are one region each, with lower-third shares {_fmt(float(sessions.loc[sessions['session_date'] == '2026-06-22', 'lower_share'].iloc[0]))} and {_fmt(float(sessions.loc[sessions['session_date'] == '2026-08-17', 'lower_share'].iloc[0]))}. The geometry that survived Step 1B shows up here as location inside a single accepted region, not as a second node.

## J. Sensitivity

The looser and stricter settings change only the existing peak-detector prominence and minimum spacing. The major-peak fraction and the 0.20 / 0.30 gap cuts stay fixed. The baseline is not replaced.

{chr(10).join(sens_lines)}

Looser detection finds peaks closer together. A peak that lands inside a wide gap can break that gap into two shorter gaps, and both can then fail the 0.20 separation cut. The profile collapses toward one region, and the clean-two count goes to zero. Stricter detection keeps fewer peaks, leaves more gaps empty, and raises both the two-region count and the clean-two count. The region count moves with the detector. That is a reason to keep it as a description under the baseline detector, not as a type to trade.

## K. Random gallery

Seed 42 on the 96 dates sorted ascending is the same draw as Step 1B. The dates, in draw order, are: {', '.join(random_bits)}.

The sheet is `results/figures/step2/gallery_random.png`. It was not edited. Histograms of the region count and the dominant third are `results/figures/step2/n_regions.png` and `results/figures/step2/dominant_third.png`.

## Conclusion

The letter scores are not how this sample is organized. The median day is one accepted region, even though it usually contains several major peaks, because those peaks sit closer than 20% of the range. A second region is common but not typical: 40 of 96 sessions, and only 14 of those 40 have an empty detected gap. Several of the empty-gap cases are a tall peak in a thin tail, not a second mass. Three accepted regions happen 7 times. Four or more do not happen.

Valley depth between adjacent major peaks is high almost everywhere, including the pairs that stay inside one region. It does not identify a low-volume shelf. Distance does the splitting, and a minor peak inside that distance is common.

Location is usable on its own. Upper volume is more common than lower volume. The original P-like day and both b-like days are single regions sitting in the upper or lower third.

No cutoff here is a trading rule. The question of what happens when the next session trades through a prior low-volume gap is not tested in this step.
"""
    REPORT.write_text(text, encoding="utf-8")
    print(f"[step2] wrote {REPORT}", flush=True)


if __name__ == "__main__":
    write()
