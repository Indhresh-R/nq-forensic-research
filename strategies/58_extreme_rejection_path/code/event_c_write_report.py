"""Write Event C report."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(CODE))

from constants import HORIZONS, RESULTS


def write_report() -> Path:
    funnel = json.loads((RESULTS / "event_c_funnel.json").read_text(encoding="utf-8"))
    dest = pd.read_csv(RESULTS / "event_c_destinations.csv")
    verdict = json.loads((RESULTS / "event_c_verdict.json").read_text(encoding="utf-8"))
    audit = json.loads((RESULTS / "audit.json").read_text(encoding="utf-8"))

    lines: list[str] = []
    lines.append("# Event C Report — Extreme Excursion → Rejection")
    lines.append("")
    lines.append("**Family 4 only. Path-first. No Event A/B rescue. No horizon shopping.**")
    lines.append("")
    lines.append("## Funnel")
    lines.append("")
    lines.append(f"- Excursion onsets: {funnel.get('n_onset_excursions')}")
    lines.append(f"- Events (rejection): {funnel.get('n_events')}")
    lines.append(f"- Censored: {funnel.get('n_censored_no_rejection')}")
    lines.append("")
    lines.append("## Freeze / audit")
    lines.append("")
    lines.append("```text")
    lines.append(f"LOOKAHEAD_CHECK = {audit.get('LOOKAHEAD_CHECK')}")
    lines.append(f"EVENT_DEFINITION_FROZEN = {audit.get('EVENT_DEFINITION_FROZEN')}")
    lines.append(f"NO_PARAMETER_RETUNE = {audit.get('NO_PARAMETER_RETUNE')}")
    lines.append(f"NO_EVENT_AB_COMBINE = {audit.get('NO_EVENT_AB_COMBINE')}")
    lines.append(f"NO_HORIZON_PNL_SHOP = {audit.get('NO_HORIZON_PNL_SHOP')}")
    lines.append("```")
    lines.append("")
    lines.append("## Destination asymmetry")
    lines.append("")
    lines.append(
        "| horizon | split | n_valid | p_anchor | p_extreme | p_through | delta_anchor_minus_extreme |"
    )
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for _, r in dest.iterrows():
        lines.append(
            "| {h} | {split} | {n} | {pa:.4f} | {pe:.4f} | {pt:.4f} | {d:.4f} |".format(
                h=int(r["horizon"]),
                split=r["split"],
                n=int(r["n_valid"]),
                pa=float(r["p_anchor"]),
                pe=float(r["p_extreme"]),
                pt=float(r["p_through"]),
                d=float(r["delta_anchor_minus_extreme"]),
            )
        )
    lines.append("")
    dv = verdict["destination"]
    lines.append("## Step 1 / 2 — Destination verdict")
    lines.append("")
    lines.append(f"- **Classification:** `{dv.get('classification')}`")
    lines.append(f"- **Stage:** `{dv.get('stage')}`")
    lines.append(f"- **Reason:** `{dv.get('reason')}`")
    lines.append("")

    pv = verdict.get("path")
    if pv:
        lines.append("## Step 3 — Path / MFE–MAE")
        lines.append("")
        ladder_path = RESULTS / "path_ladder_by_split.csv"
        if ladder_path.exists():
            ladder = pd.read_csv(ladder_path)
            lines.append(
                "| split | horizon | n | med | mean | p_pos | med_mfe | med_mae | p_hit_anchor |"
            )
            lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
            for _, r in ladder.iterrows():
                lines.append(
                    "| {split} | {h} | {n} | {med:.4f} | {mean:.4f} | {pp:.4f} | "
                    "{mfe:.4f} | {mae:.4f} | {ph:.4f} |".format(
                        split=r["split"],
                        h=int(r["horizon"]),
                        n=int(r["n"]),
                        med=float(r["med"]),
                        mean=float(r["mean"]),
                        pp=float(r["p_pos"]),
                        mfe=float(r["med_mfe"]),
                        mae=float(r["med_mae"]),
                        ph=float(r["p_hit_anchor"]),
                    )
                )
            lines.append("")
        for split in ("IS", "Validation", "OOS"):
            d = pv["detail"][split]
            meds = " → ".join(f"{h}:{d['med'][str(h)]:.4f}" for h in HORIZONS)
            lines.append(
                f"- **{split}**: mono={d['mono']}, med60_pos={d['med60_pos']}, "
                f"mfe_gt_mae_15={d['mfe_gt_mae_15']} "
                f"(mfe={d['med_mfe_15']:.4f}, mae={d['med_mae_15']:.4f}); medians [{meds}]"
            )
        lines.append("")
        lines.append(f"- **Path classification:** `{pv.get('classification')}`")
        lines.append(f"- **Reason:** `{pv.get('reason')}`")
        lines.append("")
        fr_path = RESULTS / "first_anchor_timing.csv"
        if fr_path.exists():
            fr = pd.read_csv(fr_path)
            lines.append("### Time to anchor (descriptive)")
            lines.append("")
            lines.append("| split | n_h60 | n_hit | med_bars | p25 | p75 |")
            lines.append("| --- | --- | --- | --- | --- | --- |")
            for _, r in fr.iterrows():
                lines.append(
                    "| {split} | {n} | {nh} | {med:.1f} | {p25:.1f} | {p75:.1f} |".format(
                        split=r["split"],
                        n=int(r["n_h60_valid"]),
                        nh=int(r["n_hit_anchor_by_60"]),
                        med=float(r["med_first_anchor_bars"]),
                        p25=float(r["p25"]),
                        p75=float(r["p75"]),
                    )
                )
            lines.append("")
    else:
        lines.append("## Step 3 — Path")
        lines.append("")
        lines.append("Not run (destination did not advance).")
        lines.append("")

    tv = verdict.get("trade")
    if tv:
        lines.append("## Step 6 — Trade")
        lines.append("")
        lines.append("Side: toward anchor (`−ext_dir`). Entry `open[t+1]`, exit `close[t+15]`, cost 1.0 pt RT.")
        lines.append("")
        ts = pd.read_csv(RESULTS / "event_c_trade_summary.csv")
        lines.append(
            "| split | n_trades | mean_gross | mean_net | median_net | hit_rate | eligible |"
        )
        lines.append("| --- | --- | --- | --- | --- | --- | --- |")
        for _, r in ts.iterrows():
            lines.append(
                "| {split} | {n} | {g:.4f} | {net:.4f} | {med:.4f} | {hr:.4f} | {el} |".format(
                    split=r["split"],
                    n=int(r["n_trades"]),
                    g=float(r["mean_gross"]),
                    net=float(r["mean_net"]),
                    med=float(r["median_net"]),
                    hr=float(r["hit_rate"]),
                    el=bool(r["eligible"]),
                )
            )
        lines.append("")
        lines.append(f"**Trade classification:** `{tv.get('classification')}`")
        lines.append("")
    else:
        lines.append("## Step 6 — Trade")
        lines.append("")
        lines.append("Not run.")
        lines.append("")

    lines.append("## EVENT C FINAL")
    lines.append("")
    lines.append(f"**{verdict.get('final')}**. Do not retune. Do not reopen Event A/B.")
    lines.append("")

    out = RESULTS / "EVENT_C_REPORT.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


if __name__ == "__main__":
    print(write_report())
