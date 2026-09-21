"""Re-label profiles at the preregistered looser and stricter extrema settings.

Does not change P/b/D cutoffs and does not choose a new baseline.
"""

from __future__ import annotations

import json

import pandas as pd

from detect_shapes import build_dataset
from frozen import (
    CLASS_UNCLASSIFIED,
    LOOSER_PROMINENCE_FRAC,
    LOOSER_SEPARATION_FRAC,
    PRIMARY_CLASSES,
    PROMINENCE_FRAC,
    RESULTS,
    SEPARATION_FRAC,
    STRICTER_PROMINENCE_FRAC,
    STRICTER_SEPARATION_FRAC,
    WEAK_AGREE,
)


def _counts(frame: pd.DataFrame) -> dict[str, int]:
    counts = {name: 0 for name in PRIMARY_CLASSES}
    if frame.empty:
        return counts
    for name, count in frame["primary_class"].value_counts().items():
        counts[str(name)] = int(count)
    return counts


def _transitions(left: pd.Series, right: pd.Series) -> dict[str, int]:
    pairs = {}
    for before, after in zip(left.tolist(), right.tolist()):
        key = f"{before} -> {after}"
        pairs[key] = pairs.get(key, 0) + 1
    return dict(sorted(pairs.items()))


def main() -> None:
    settings = (
        ("looser", LOOSER_PROMINENCE_FRAC, LOOSER_SEPARATION_FRAC),
        ("baseline", PROMINENCE_FRAC, SEPARATION_FRAC),
        ("stricter", STRICTER_PROMINENCE_FRAC, STRICTER_SEPARATION_FRAC),
    )
    labeled = {}
    summaries = []
    for name, prominence, separation in settings:
        dataset, _nodes = build_dataset(prominence, separation)
        labeled[name] = dataset
        sample = dataset[dataset["in_analysis_sample"]]
        summaries.append(
            {
                "name": name,
                "prominence_frac": prominence,
                "separation_frac": separation,
                "n_analysis": int(len(sample)),
                "counts": _counts(sample),
            }
        )
        print(f"[sensitivity] {name} {summaries[-1]['counts']}", flush=True)

    base = labeled["baseline"]
    sample = base["in_analysis_sample"].astype(bool)
    compare = base.loc[:, ["session_date"]].copy()
    compare["in_analysis_sample"] = sample.to_numpy()
    compare["baseline"] = base["primary_class"].to_numpy()
    for name in ("looser", "stricter"):
        other = labeled[name][["session_date", "primary_class"]].rename(columns={"primary_class": name})
        compare = compare.merge(other, on="session_date", how="left", validate="one_to_one")
        held = compare["in_analysis_sample"]
        agree = float((compare.loc[held, "baseline"] == compare.loc[held, name]).mean()) if held.any() else float("nan")
        for item in summaries:
            if item["name"] == name:
                item["agreement_with_baseline"] = agree
        print(f"[sensitivity] agreement {name}={agree:.4f}", flush=True)
    for item in summaries:
        if item["name"] == "baseline":
            item["agreement_with_baseline"] = 1.0

    held = compare["in_analysis_sample"]
    loose_agree = float((compare.loc[held, "baseline"] == compare.loc[held, "looser"]).mean()) if held.any() else float("nan")
    strict_agree = float((compare.loc[held, "baseline"] == compare.loc[held, "stricter"]).mean()) if held.any() else float("nan")
    summary = {
        "settings": summaries,
        "agreement_looser": loose_agree,
        "agreement_stricter": strict_agree,
        "unstable": bool(loose_agree < WEAK_AGREE or strict_agree < WEAK_AGREE),
        "transitions_looser": _transitions(compare.loc[held, "baseline"], compare.loc[held, "looser"]),
        "transitions_stricter": _transitions(compare.loc[held, "baseline"], compare.loc[held, "stricter"]),
        "n_analysis": int(held.sum()),
        "unclassified_name": CLASS_UNCLASSIFIED,
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    compare.to_parquet(RESULTS / "sensitivity_labels.parquet", index=False)
    (RESULTS / "sensitivity_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"[sensitivity] unstable={summary['unstable']}", flush=True)


if __name__ == "__main__":
    main()
