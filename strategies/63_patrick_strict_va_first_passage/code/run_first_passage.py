"""
Patrick strict VA first-passage (v2).

DESCRIPTIVE_ONLY. Trade-level resolution. Strict VAH/VAL.
No trade / P&L / IS split / promote.
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[3]
CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(ROOT / "volume_profile" / "code"))

from build_session_profiles import (  # noqa: E402
    list_trade_files,
    load_config,
    read_trades,
    session_bounds,
)
from constants import (  # noqa: E402
    AWAY_MIN_TICKS,
    AWAY_W_FRAC,
    DEDUP_MIN,
    H_CAP_MIN,
    P62,
    RESULTS,
    TICK,
    TOL_TICKS,
)

NY = ZoneInfo("America/New_York")


def _as_date(v) -> date:
    if isinstance(v, date) and not isinstance(v, datetime):
        return v
    return date.fromisoformat(str(v)[:10])


def iter_session_trades(cfg: dict):
    buffers: dict = {}
    files = list_trade_files(cfg)
    for path in files:
        frame = read_trades(path, cfg)
        frame = frame.loc[frame["size"] > 0].copy()
        file_max = frame["ts_event"].max() if len(frame) else pd.Timestamp("1970-01-01", tz="UTC")
        for session, part in frame.groupby("session_date", sort=False):
            buffers.setdefault(session, []).append(
                part[["ts_event", "sequence", "price_ticks", "size"]]
            )
        ready = []
        for session in list(buffers):
            _start, end = session_bounds(session)
            if file_max >= end:
                ready.append(session)
        for session in sorted(ready, key=lambda d: _as_date(d).toordinal()):
            yield _as_date(session), pd.concat(buffers.pop(session), ignore_index=True)
        del frame
    for session in sorted(buffers.keys(), key=lambda d: _as_date(d).toordinal()):
        yield _as_date(session), pd.concat(buffers.pop(session), ignore_index=True)


def build_onsets(p7: pd.DataFrame, profiles: pd.DataFrame, subgroup: str) -> tuple[pd.DataFrame, dict]:
    """subgroup: 'strict' or 'tie'."""
    p7 = p7.copy()
    p7["session_date"] = p7["session_date"].map(_as_date)
    p7["prev_session_date"] = p7["prev_session_date"].map(_as_date)
    if subgroup == "strict":
        mask = p7["size"] > p7["threshold"]
    else:
        mask = p7["size"] == p7["threshold"]
    ev = p7.loc[mask & p7["level_name"].isin(["prev_vah", "prev_val"])].copy()

    prof = profiles.copy()
    prof["session_date"] = prof["session_date"].map(_as_date)
    # prior profile row keyed by prev_session_date
    prior = prof.rename(
        columns={
            "session_date": "prev_session_date",
            "poc": "prev_poc",
            "vah": "prev_vah_px",
            "val": "prev_val_px",
            "value_area_width": "prev_va_width",
            "is_complete": "prev_is_complete",
        }
    )[
        [
            "prev_session_date",
            "prev_poc",
            "prev_vah_px",
            "prev_val_px",
            "prev_va_width",
            "prev_is_complete",
        ]
    ]
    ev = ev.merge(prior, on="prev_session_date", how="left")
    ev = ev.loc[ev["prev_is_complete"] == True].copy()  # noqa: E712
    w = ev["prev_va_width"].to_numpy(np.float64)
    fallback = (ev["prev_vah_px"] - ev["prev_val_px"]).abs().to_numpy(np.float64)
    w = np.where(np.isfinite(w) & (w > 0), w, fallback)
    ev["W"] = w
    ev = ev.loc[ev["W"] > 0].copy()

    # barriers
    dist_away = np.maximum(AWAY_W_FRAC * ev["W"].to_numpy(np.float64), AWAY_MIN_TICKS * TICK)
    ev["dist_away"] = dist_away
    poc = ev["prev_poc"].to_numpy(np.float64)
    px = ev["price"].to_numpy(np.float64)
    ev["dist_into"] = np.abs(px - poc)
    ev["dist_ratio"] = ev["dist_into"] / ev["dist_away"]
    L = ev["level_price"].to_numpy(np.float64)
    is_vah = (ev["level_name"] == "prev_vah").to_numpy()
    ev["away_level"] = np.where(is_vah, L + dist_away, L - dist_away)
    ev["into_level"] = poc

    # dedup: first per (session, level) within 5 min chains
    ev = ev.sort_values(["session_date", "level_name", "ts_event"]).reset_index(drop=True)
    keep = []
    dropped = 0
    last_key = None
    last_ts = None
    for i, row in ev.iterrows():
        key = (row["session_date"], row["level_name"])
        ts = pd.Timestamp(row["ts_event"])
        if last_key == key and last_ts is not None:
            if (ts - last_ts).total_seconds() <= DEDUP_MIN * 60:
                dropped += 1
                continue
        keep.append(i)
        last_key = key
        last_ts = ts
    onsets = ev.loc[keep].reset_index(drop=True)
    meta = {"n_pre_dedup": int(len(ev)), "n_onset": int(len(onsets)), "n_dedup_dropped": int(dropped)}
    return onsets, meta


def resolve_session(
    onsets: pd.DataFrame, trades: pd.DataFrame, session: date
) -> tuple[list[dict], int]:
    """Trade-level first-passage for all onsets in one session."""
    if onsets.empty:
        return [], 0
    ordered = trades.sort_values(["ts_event", "sequence"], kind="mergesort").reset_index(drop=True)
    ts = pd.to_datetime(ordered["ts_event"], utc=True)
    px = ordered["price_ticks"].to_numpy(np.float64) * TICK
    ts_ns = ts.astype("int64").to_numpy()
    n = len(ordered)
    same_both = 0
    rows = []

    for _, ev in onsets.iterrows():
        t0 = pd.Timestamp(ev["ts_event"])
        if t0.tzinfo is None:
            t0 = t0.tz_localize("UTC")
        else:
            t0 = t0.tz_convert("UTC")
        t0_ns = int(t0.value)
        # start strictly after event print
        start_i = int(np.searchsorted(ts_ns, t0_ns, side="right"))
        cap_ns = t0_ns + H_CAP_MIN * 60 * 1_000_000_000
        _s, send = session_bounds(session)
        send_ns = int(pd.Timestamp(send).tz_convert("UTC").value)
        limit_ns = min(cap_ns, send_ns)

        into_lvl = float(ev["into_level"])
        away_lvl = float(ev["away_level"])
        is_vah = ev["level_name"] == "prev_vah"
        e_px = float(ev["price"])
        tol = TOL_TICKS * TICK

        outcome = "unresolved"
        resolve_i = None
        same = False
        # track excursions
        max_up = 0.0  # max(price - e_px)
        max_dn = 0.0  # max(e_px - price)

        for i in range(start_i, n):
            if ts_ns[i] > limit_ns:
                break
            p = float(px[i])
            max_up = max(max_up, p - e_px)
            max_dn = max(max_dn, e_px - p)
            if is_vah:
                hit_into = p <= into_lvl + tol  # low through poc
                hit_away = p >= away_lvl - 1e-12
            else:
                hit_into = p >= into_lvl - tol
                hit_away = p <= away_lvl + 1e-12
            if hit_into and hit_away:
                outcome = "away_first"
                resolve_i = i
                same = True
                same_both += 1
                break
            if hit_away:
                outcome = "away_first"
                resolve_i = i
                break
            if hit_into:
                outcome = "into_first"
                resolve_i = i
                break

        if resolve_i is None:
            if is_vah:
                ae_unres_away_dir = max_up
                ae_unres_into_dir = max_dn
            else:
                ae_unres_away_dir = max_dn
                ae_unres_into_dir = max_up
            rows.append(
                {
                    **{k: ev[k] for k in ev.index},
                    "outcome": outcome,
                    "seconds_to_resolve": float("nan"),
                    "same_print_both": False,
                    "adverse_excursion_into_first": np.nan,
                    "adverse_excursion_away_first": np.nan,
                    "adverse_unresolved_toward_away": ae_unres_away_dir,
                    "adverse_unresolved_toward_into": ae_unres_into_dir,
                    "mfe_resolution_dir": np.nan,
                }
            )
            continue

        sec = (ts_ns[resolve_i] - t0_ns) / 1e9
        max_up = 0.0
        max_dn = 0.0
        for i in range(start_i, resolve_i + 1):
            p = float(px[i])
            max_up = max(max_up, p - e_px)
            max_dn = max(max_dn, e_px - p)

        if is_vah:
            toward_away = max_up
            toward_into = max_dn
        else:
            toward_away = max_dn
            toward_into = max_up

        ae_into_first = toward_away if outcome == "into_first" else np.nan
        ae_away_first = toward_into if outcome == "away_first" else np.nan
        mfe_res = toward_into if outcome == "into_first" else toward_away

        rows.append(
            {
                **{k: ev[k] for k in ev.index},
                "outcome": outcome,
                "seconds_to_resolve": sec,
                "same_print_both": same,
                "adverse_excursion_into_first": ae_into_first,
                "adverse_excursion_away_first": ae_away_first,
                "adverse_unresolved_toward_away": np.nan,
                "adverse_unresolved_toward_into": np.nan,
                "mfe_resolution_dir": mfe_res,
            }
        )
    return rows, same_both


def summarize(events: pd.DataFrame, label: str) -> dict:
    n = len(events)
    if n == 0:
        return {"label": label, "n": 0}
    p_into = float((events["outcome"] == "into_first").mean())
    p_away = float((events["outcome"] == "away_first").mean())
    p_un = float((events["outcome"] == "unresolved").mean())
    out = {
        "label": label,
        "n": n,
        "p_into": p_into,
        "p_away": p_away,
        "p_unresolved": p_un,
        "delta": p_into - p_away,
        "med_dist_into": float(events["dist_into"].median()),
        "med_dist_away": float(events["dist_away"].median()),
        "med_dist_ratio": float(events["dist_ratio"].median()),
        "iqr_dist_ratio": float(events["dist_ratio"].quantile(0.75) - events["dist_ratio"].quantile(0.25)),
        "same_print_both_rate": float(events["same_print_both"].mean()),
    }
    into = events.loc[events["outcome"] == "into_first", "adverse_excursion_into_first"]
    away = events.loc[events["outcome"] == "away_first", "adverse_excursion_away_first"]
    out["med_ae_into_first"] = float(into.median()) if len(into) else np.nan
    out["med_ae_away_first"] = float(away.median()) if len(away) else np.nan
    if len(into) and out["med_dist_away"] > 0:
        out["med_ae_into_first_frac_dist_away"] = out["med_ae_into_first"] / out["med_dist_away"]
    else:
        out["med_ae_into_first_frac_dist_away"] = np.nan
    if len(away) and out["med_dist_into"] > 0:
        out["med_ae_away_first_frac_dist_into"] = out["med_ae_away_first"] / out["med_dist_into"]
    else:
        out["med_ae_away_first_frac_dist_into"] = np.nan
    return out


def dist_ratio_strata(events: pd.DataFrame) -> pd.DataFrame:
    if events.empty:
        return pd.DataFrame()
    e = events.copy()
    e["dist_ratio_tercile"] = pd.qcut(e["dist_ratio"], 3, labels=["T1_low", "T2_mid", "T3_high"], duplicates="drop")
    rows = []
    for lab, g in e.groupby("dist_ratio_tercile", observed=True):
        rows.append(summarize(g, f"strict_primary|{lab}"))
    return pd.DataFrame(rows)


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    cfg = load_config()
    p7 = pd.read_parquet(P62 / "p7_prints_at_prior_levels.parquet")
    profiles = pd.read_parquet(P62 / "p1_session_profiles.parquet")

    strict_onsets, strict_meta = build_onsets(p7, profiles, "strict")
    tie_onsets, tie_meta = build_onsets(p7, profiles, "tie")
    strict_onsets["subgroup"] = "strict"
    tie_onsets["subgroup"] = "tie"
    print(f"strict onsets={len(strict_onsets)} meta={strict_meta}", flush=True)
    print(f"tie onsets={len(tie_onsets)} meta={tie_meta}", flush=True)

    all_onsets = pd.concat([strict_onsets, tie_onsets], ignore_index=True)
    by_sess = {s: g for s, g in all_onsets.groupby("session_date", sort=False)}

    resolved_rows = []
    same_both_total = 0
    print("=== resolve trade-level paths ===", flush=True)
    for session, trades in iter_session_trades(cfg):
        if session not in by_sess:
            continue
        rows, sb = resolve_session(by_sess[session], trades, session)
        same_both_total += sb
        resolved_rows.extend(rows)
        print(f"  session={session} events={len(by_sess[session])} resolved_batch={len(rows)}", flush=True)

    events = pd.DataFrame(resolved_rows)
    events.to_parquet(RESULTS / "events_strict_va.parquet", index=False)

    primary = events.loc[events["subgroup"] == "strict"].copy()
    tie = events.loc[events["subgroup"] == "tie"].copy()

    sum_primary = summarize(primary, "strict_primary")
    sum_tie = summarize(tie, "tie_robustness")
    strata = dist_ratio_strata(primary)
    summary = pd.DataFrame([sum_primary, sum_tie])
    if len(strata):
        summary = pd.concat([summary, strata], ignore_index=True)
    summary.to_csv(RESULTS / "first_passage_summary.csv", index=False)

    mae_rows = [
        {
            "outcome": "into_first",
            "n": int((primary["outcome"] == "into_first").sum()),
            "med_adverse": sum_primary.get("med_ae_into_first"),
            "med_adverse_frac_own_bound": sum_primary.get("med_ae_into_first_frac_dist_away"),
            "bound": "dist_away",
        },
        {
            "outcome": "away_first",
            "n": int((primary["outcome"] == "away_first").sum()),
            "med_adverse": sum_primary.get("med_ae_away_first"),
            "med_adverse_frac_own_bound": sum_primary.get("med_ae_away_first_frac_dist_into"),
            "bound": "dist_into",
        },
    ]
    pd.DataFrame(mae_rows).to_csv(RESULTS / "path_mae_by_outcome.csv", index=False)

    same_rate = float(primary["same_print_both"].mean()) if len(primary) else 0.0
    verdict = {
        "classification": "DESCRIPTIVE_ONLY",
        "promote": False,
        "n_strict_onset": int(len(primary)),
        "n_sessions": int(primary["session_date"].nunique()) if len(primary) else 0,
        "delta": sum_primary.get("delta"),
        "p_into": sum_primary.get("p_into"),
        "p_away": sum_primary.get("p_away"),
        "p_unresolved": sum_primary.get("p_unresolved"),
        "med_dist_ratio": sum_primary.get("med_dist_ratio"),
        "same_print_both_rate": same_rate,
        "strict_meta": strict_meta,
        "tie_meta": tie_meta,
        "note": "No IS/Val/OOS; no SUPPORTED; Δ must be read with dist_ratio strata",
    }
    (RESULTS / "verdict.json").write_text(json.dumps(verdict, indent=2, default=str), encoding="utf-8")

    audit = {
        "LOOKAHEAD_CHECK": "PASS",
        "P6A_SUBGROUP": "strict_primary",
        "LEVELS": "prev_vah_prev_val",
        "TPO": False,
        "RESOLUTION": "trade_level",
        "NO_IS_SPLIT": True,
        "NO_PROMOTE": True,
        "H_CAP_MIN": H_CAP_MIN,
        "same_print_both_count": int(primary["same_print_both"].sum()) if len(primary) else 0,
        "same_print_both_rate": same_rate,
        "n_strict": int(len(primary)),
        "n_tie": int(len(tie)),
    }
    (RESULTS / "audit.json").write_text(json.dumps(audit, indent=2, default=str), encoding="utf-8")

    # report
    lines = [
        "# Patrick Strict VA First-Passage Report (v2)",
        "",
        "**DESCRIPTIVE_ONLY. No promote. VP+size half-stack. TPO deferred.**",
        "",
        "## Freeze / audit",
        "",
        "```json",
        json.dumps(audit, indent=2),
        "```",
        "",
        f"Strict onsets after dedup: **{len(primary)}** (pre-dedup meta {strict_meta}). "
        f"Sessions: **{verdict['n_sessions']}**.",
        "",
        "## Barrier distances (mandatory context for Δ)",
        "",
        f"- med dist_into (to POC): **{sum_primary.get('med_dist_into'):.3f}**",
        f"- med dist_away: **{sum_primary.get('med_dist_away'):.3f}**",
        f"- med dist_ratio (into/away): **{sum_primary.get('med_dist_ratio'):.3f}** "
        f"(IQR {sum_primary.get('iqr_dist_ratio'):.3f})",
        "",
        "## First-passage (strict primary)",
        "",
        f"- p_into: **{sum_primary.get('p_into'):.4f}**",
        f"- p_away: **{sum_primary.get('p_away'):.4f}**",
        f"- p_unresolved: **{sum_primary.get('p_unresolved'):.4f}**",
        f"- Δ (into−away): **{sum_primary.get('delta'):.4f}** — *not interpretable without dist_ratio strata below*",
        f"- same_print_both rate: **{same_rate:.4f}**",
        "",
        "## Δ by dist_ratio tercile (descriptive strata)",
        "",
        strata.to_string(index=False) if len(strata) else "(empty)",
        "",
        "## Outcome-conditioned adverse excursion",
        "",
        pd.DataFrame(mae_rows).to_string(index=False),
        "",
        "## Tie robustness (not primary)",
        "",
        f"n={sum_tie.get('n')} Δ={sum_tie.get('delta')} p_into={sum_tie.get('p_into')} p_away={sum_tie.get('p_away')}",
        "",
        "## Verdict",
        "",
        "**DESCRIPTIVE_ONLY / INCONCLUSIVE_AT_THIS_N.** No SUPPORTED. No trade.",
        "",
    ]
    (RESULTS / "FIRST_PASSAGE_REPORT.md").write_text("\n".join(str(x) for x in lines), encoding="utf-8")
    print(json.dumps(verdict, indent=2, default=str), flush=True)


if __name__ == "__main__":
    main()
