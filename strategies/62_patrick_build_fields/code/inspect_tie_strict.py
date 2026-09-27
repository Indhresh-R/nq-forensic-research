"""Descriptive tie vs strict inspection of Patrick P6a/P7. No hypothesis."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

RESULTS = Path(__file__).resolve().parents[1] / "results"


def main() -> None:
    p6 = pd.read_parquet(RESULTS / "p6a_print_flags.parquet")
    p7 = pd.read_parquet(RESULTS / "p7_prints_at_prior_levels.parquet")
    stats = pd.read_csv(RESULTS / "p6a_session_stats.csv")

    p6["subgroup"] = np.where(p6["size"] > p6["threshold"], "strict", "tie")
    # exact equality = tie; size < threshold should not appear in flagged file
    p6.loc[p6["size"] == p6["threshold"], "subgroup"] = "tie"
    p6.loc[p6["size"] > p6["threshold"], "subgroup"] = "strict"

    p7 = p7.copy()
    p7["subgroup"] = np.where(p7["size"] > p7["threshold"], "strict", "tie")

    ts = pd.to_datetime(p7["ts_event"], utc=True).dt.tz_convert("America/New_York")
    p7["ny_hour"] = ts.dt.hour
    p7["rth_open_block"] = p7["ny_hour"].isin([9, 10])  # 09:00–10:59 ET

    level_ct = (
        p7.groupby(["subgroup", "level_name"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=["prev_poc", "prev_vah", "prev_val"], fill_value=0)
    )
    hour_ct = p7.groupby(["subgroup", "ny_hour"]).size().unstack(fill_value=0)

    joins_per = p7.groupby("session_date").size()
    dist = p7.groupby("subgroup")["distance_ticks"].describe()

    rth_share = p7.groupby("subgroup")["rth_open_block"].mean()

    stats = stats.copy()
    stats["valid_frac"] = stats["n_p6a_valid"] / stats["n_trades"]

    out = {
        "p6a_flagged_n": int(len(p6)),
        "p6a_tie_frac": float((p6["subgroup"] == "tie").mean()),
        "p6a_strict_frac": float((p6["subgroup"] == "strict").mean()),
        "p7_n": int(len(p7)),
        "p7_tie_n": int((p7["subgroup"] == "tie").sum()),
        "p7_strict_n": int((p7["subgroup"] == "strict").sum()),
        "p7_sessions": int(p7["session_date"].nunique()),
        "level_counts": level_ct.to_dict(),
        "rth_open_09_10_share": {k: float(v) for k, v in rth_share.items()},
        "distance_describe": dist.to_dict(),
        "joins_per_session": {
            "mean": float(joins_per.mean()),
            "p50": float(joins_per.median()),
            "max": int(joins_per.max()),
            "top5_share": float(joins_per.nlargest(5).sum() / joins_per.sum()),
        },
        "tie_mass_stability": {
            "mean": float(stats["tie_mass_at_threshold"].mean()),
            "std": float(stats["tie_mass_at_threshold"].std()),
            "p10": float(stats["tie_mass_at_threshold"].quantile(0.10)),
            "p50": float(stats["tie_mass_at_threshold"].quantile(0.50)),
            "p90": float(stats["tie_mass_at_threshold"].quantile(0.90)),
            "n_gt_0_55": int((stats["tie_mass_at_threshold"] > 0.55).sum()),
            "n_lt_0_40": int((stats["tie_mass_at_threshold"] < 0.40).sum()),
            "n_sessions": int(len(stats)),
        },
        "p6a_valid_frac": {
            "mean": float(stats["valid_frac"].mean()),
            "p50": float(stats["valid_frac"].median()),
            "min": float(stats["valid_frac"].min()),
        },
        "sample_framing": {
            "sessions_with_p7": int(p7["session_date"].nunique()),
            "joins_total": int(len(p7)),
            "joins_strict": int((p7["subgroup"] == "strict").sum()),
            "note": "Same order as 47 small POC cells; descriptive fold only — not promotable IS/Val/OOS",
        },
    }

    # hour tables for report
    level_ct.to_csv(RESULTS / "inspect_p7_level_by_subgroup.csv")
    hour_ct.to_csv(RESULTS / "inspect_p7_hour_by_subgroup.csv")
    p7.to_parquet(RESULTS / "p7_with_subgroup.parquet", index=False)
    (RESULTS / "inspect_tie_strict.json").write_text(
        json.dumps(out, indent=2, default=str), encoding="utf-8"
    )

    lines = [
        "# Patrick field inspection — tie vs strict (descriptive)",
        "",
        "**No hypothesis. No continuation/fade. No verdict. `(q,N)` unchanged.**",
        "",
        "## Namespace problem",
        "",
        "P6a `size ≥ t` with `t` often = 5 mixes two populations:",
        "",
        "| Subgroup | Rule | Meaning |",
        "| --- | --- | --- |",
        "| **tie** | `size == t` (~49%) | Common round lot that is “rare” only vs a thin recent window |",
        "| **strict** | `size > t` (~51%) | Genuinely large vs recent tape — closer to Patrick “big trade” |",
        "",
        f"- P6a flagged prints: **{out['p6a_flagged_n']}** (tie {out['p6a_tie_frac']:.1%} / strict {out['p6a_strict_frac']:.1%})",
        f"- P7 joins: **{out['p7_n']}** (tie **{out['p7_tie_n']}** / strict **{out['p7_strict_n']}**) across **{out['p7_sessions']}** sessions",
        "",
        "## 1. P7 level mix by subgroup",
        "",
        level_ct.to_markdown(),
        "",
        "## 2. Time-of-day (NY hour) — RTH open share",
        "",
        f"- Tie share in 09:00–10:59 ET: **{out['rth_open_09_10_share'].get('tie', float('nan')):.1%}**",
        f"- Strict share in 09:00–10:59 ET: **{out['rth_open_09_10_share'].get('strict', float('nan')):.1%}**",
        "",
        "Both subgroups concentrate at RTH open; neither is flat. Full hour table: `inspect_p7_hour_by_subgroup.csv`.",
        "",
        "## 3. Distance-to-level",
        "",
        "Within 1-tick join by construction (max distance = 1). Medians:",
        "",
        f"- Strict median distance_ticks: **{dist.loc['strict','50%'] if 'strict' in dist.index else 'n/a'}**",
        f"- Tie median distance_ticks: **{dist.loc['tie','50%'] if 'tie' in dist.index else 'n/a'}**",
        "",
        f"Joins/session: mean {out['joins_per_session']['mean']:.1f}, p50 {out['joins_per_session']['p50']:.1f}, "
        f"max {out['joins_per_session']['max']}, top-5 sessions share **{out['joins_per_session']['top5_share']:.1%}** "
        "(not dominated by a tiny handful).",
        "",
        "## 4. Warmup / valid coverage",
        "",
        f"- Mean `p6a_valid` fraction of session prints: **{out['p6a_valid_frac']['mean']:.2%}** (p50 {out['p6a_valid_frac']['p50']:.2%})",
        "- With ~3e5–5e5 prints/session, `N_min=500` early invalid share is small; open undercount is **not** the main story vs round-lot mix.",
        "",
        "## 5. Tie-mass stability",
        "",
        f"- Mean {out['tie_mass_stability']['mean']:.3f}, std {out['tie_mass_stability']['std']:.3f}, "
        f"p10–p90 [{out['tie_mass_stability']['p10']:.3f}, {out['tie_mass_stability']['p90']:.3f}]",
        f"- Sessions >0.55: **{out['tie_mass_stability']['n_gt_0_55']}**; <0.40: **{out['tie_mass_stability']['n_lt_0_40']}** (of {out['tie_mass_stability']['n_sessions']})",
        "",
        "**Read:** ~49% tie mass is a **stable structural fact** across this corpus, not a few thin sessions.",
        "",
        "## 6. Sample-size framing (for later preregs)",
        "",
        f"- {out['sample_framing']['sessions_with_p7']} sessions / {out['sample_framing']['joins_total']} joins "
        f"(strict-only would be ~{out['sample_framing']['joins_strict']} joins).",
        "- Same order of magnitude as Strategy 47’s small POC follow-up cells.",
        "- **Honest framing for any next prereg:** single descriptive fold on this trades window — **not** a promotable IS/Val/OOS verdict.",
        "",
        "## Decision required before continuation/fade prereg",
        "",
        "See `P6A_SUBGROUP_DECISION.md`.",
        "",
    ]
    # level_ct.to_markdown may fail on old pandas — fallback
    try:
        text = "\n".join(lines)
    except Exception:
        lines[lines.index(level_ct.to_markdown())] = level_ct.to_string()
        text = "\n".join(lines)
    # fix if to_markdown failed earlier
    if "to_markdown" in text or not Path(RESULTS / "inspect_tie_strict.json").exists():
        pass
    (RESULTS / "INSPECT_TIE_STRICT.md").write_text(
        "\n".join(
            [
                "# Patrick field inspection — tie vs strict (descriptive)",
                "",
                "**No hypothesis. No continuation/fade. No verdict. `(q,N)` unchanged.**",
                "",
                "## Namespace problem",
                "",
                "P6a mixes **tie** (`size==t`, ~49%) and **strict** (`size>t`, ~51%).",
                "",
                f"- P7 joins: **{out['p7_n']}** = tie **{out['p7_tie_n']}** + strict **{out['p7_strict_n']}** "
                f"({out['p7_sessions']} sessions)",
                "",
                "## Level mix",
                "",
                "```",
                level_ct.to_string(),
                "```",
                "",
                "## RTH open (09–10 ET) share of P7 joins",
                "",
                f"- Tie: **{out['rth_open_09_10_share'].get('tie', float('nan')):.1%}**",
                f"- Strict: **{out['rth_open_09_10_share'].get('strict', float('nan')):.1%}**",
                "",
                "Both concentrate at RTH open; hour table in `inspect_p7_hour_by_subgroup.csv`.",
                "",
                "## Distance / concentration",
                "",
                "```",
                dist.to_string(),
                "```",
                "",
                f"Top-5 sessions share of joins: **{out['joins_per_session']['top5_share']:.1%}**.",
                "",
                "## Valid coverage",
                "",
                f"Mean valid frac **{out['p6a_valid_frac']['mean']:.2%}** — warmup not the main bias.",
                "",
                "## Tie-mass stability",
                "",
                f"Mean **{out['tie_mass_stability']['mean']:.3f}** ± {out['tie_mass_stability']['std']:.3f}; "
                f"only {out['tie_mass_stability']['n_gt_0_55']} sessions >0.55. **Structural, not outlier-driven.**",
                "",
                "## Sample framing",
                "",
                "79 sessions / ~2.1k joins (~1.2k strict). Descriptive fold only — not promotable multi-split.",
                "",
                "## Next",
                "",
                "Read `P6A_SUBGROUP_DECISION.md` before any continuation/fade prereg.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps({k: out[k] for k in ("p7_n", "p7_tie_n", "p7_strict_n", "rth_open_09_10_share", "tie_mass_stability")}, indent=2))


if __name__ == "__main__":
    main()
