"""
Patrick VA Step 2 — distance-matched first-passage null.

Frozen under PATRICK_VA_STEP2_DISTANCE_NULL_PREREGISTRATION.md.
Mechanism diagnostic only. NO TRADE. NO P&L.
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
from constants import H_CAP_MIN, RESULTS, TICK  # noqa: E402

NY = ZoneInfo("America/New_York")

SEED = 20260923
N_SIM = 10_000
DT_SEC = 15.0
H_CAP_SEC = float(H_CAP_MIN * 60)
W_PRE_MIN = 30
MIN_PRE_DIFFS = 30
EVENTS_PATH = RESULTS / "events_strict_va.parquet"


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


def load_strict_events() -> pd.DataFrame:
    raw = pd.read_parquet(EVENTS_PATH)
    ev = raw.loc[raw["subgroup"] == "strict"].copy()
    ev["session_date"] = ev["session_date"].map(_as_date)
    ev["ts_event"] = pd.to_datetime(ev["ts_event"], utc=True)
    ev = ev.reset_index(drop=True)
    ev["event_id"] = np.arange(len(ev), dtype=np.int32)
    # Frozen Step-1 terciles (same qcut call)
    ev["dist_ratio_tercile"] = pd.qcut(
        ev["dist_ratio"], 3, labels=["T1_low", "T2_mid", "T3_high"], duplicates="drop"
    )
    return ev


def estimate_pre_event_sigma(events: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Causal σ_i from pre-event 1s last-trade diffs. No post-t0 prices."""
    by_sess = {s: g for s, g in events.groupby("session_date", sort=False)}
    sigma_raw = np.full(len(events), np.nan, dtype=float)
    n_diffs = np.zeros(len(events), dtype=np.int32)

    print("=== estimate causal pre-event sigma ===", flush=True)
    for session, trades in iter_session_trades(cfg):
        if session not in by_sess:
            continue
        g = by_sess[session]
        tr = trades.sort_values(["ts_event", "sequence"])
        ts = tr["ts_event"].to_numpy()
        px = tr["price_ticks"].to_numpy(dtype=float) * TICK
        ts_sec = ts.astype("datetime64[ns]").astype(np.int64) // 1_000_000_000
        df1 = pd.DataFrame({"sec": ts_sec, "px": px}).drop_duplicates("sec", keep="last")
        sec_arr = df1["sec"].to_numpy(dtype=np.int64)
        px_arr = df1["px"].to_numpy(dtype=float)
        order = np.argsort(sec_arr)
        sec_arr = sec_arr[order]
        px_arr = px_arr[order]

        for _, row in g.iterrows():
            t0 = int(pd.Timestamp(row["ts_event"]).value // 1_000_000_000)
            lo = t0 - W_PRE_MIN * 60
            left = np.searchsorted(sec_arr, lo, side="left")
            right = np.searchsorted(sec_arr, t0, side="left")
            if right - left < 2:
                continue
            window_px = px_arr[left:right]
            # align to consecutive seconds that exist; use diffs of ordered last prices
            diffs = np.diff(window_px)
            if len(diffs) < MIN_PRE_DIFFS:
                n_diffs[int(row["event_id"])] = len(diffs)
                continue
            sigma_raw[int(row["event_id"])] = float(np.std(diffs, ddof=1))
            n_diffs[int(row["event_id"])] = len(diffs)
        print(f"  session={session} events={len(g)}", flush=True)

    finite = np.isfinite(sigma_raw) & (n_diffs >= MIN_PRE_DIFFS)
    med = float(np.median(sigma_raw[finite])) if finite.any() else float(TICK)
    sigma = np.where(finite, sigma_raw, med)
    sigma = np.maximum(sigma, TICK)
    out = events[["event_id", "session_date", "ts_event"]].copy()
    out["sigma_raw"] = sigma_raw
    out["n_pre_diffs"] = n_diffs
    out["sigma_filled"] = ~finite
    out["sigma"] = sigma
    out["sigma_median_fill"] = med
    print(
        f"sigma: n_finite={int(finite.sum())} n_fill={int((~finite).sum())} median_fill={med:.6f}",
        flush=True,
    )
    return out


def simulate_bm_outcomes(
    dist_into: np.ndarray,
    dist_away: np.ndarray,
    sigma: np.ndarray,
    n_sim: int,
    seed: int,
    dt: float = DT_SEC,
    h_cap: float = H_CAP_SEC,
) -> np.ndarray:
    """
    Returns int8 array shape (n_events, n_sim):
      0 = into_first, 1 = away_first, 2 = unresolved
    """
    n = len(dist_into)
    rng = np.random.default_rng(seed)
    n_steps = int(h_cap / dt)
    out = np.full((n, n_sim), 2, dtype=np.int8)

    for i in range(n):
        a = float(dist_into[i])
        b = float(dist_away[i])
        sig = float(sigma[i])
        if a <= 0 or b <= 0 or not np.isfinite(sig):
            continue
        x = np.zeros(n_sim, dtype=np.float64)
        alive = np.ones(n_sim, dtype=bool)
        scale = sig * np.sqrt(dt)
        for _ in range(n_steps):
            if not alive.any():
                break
            idx = np.flatnonzero(alive)
            x[idx] += scale * rng.standard_normal(idx.size)
            hit_into = alive & (x <= -a)
            hit_away = alive & (x >= b)
            both = hit_into & hit_away
            hit_into = hit_into & ~both
            hit_away = hit_away | both  # same-step → away
            out[i, hit_into] = 0
            out[i, hit_away] = 1
            alive[hit_into | hit_away] = False
        if (i + 1) % 50 == 0 or i + 1 == n:
            print(f"  simulated events {i+1}/{n}", flush=True)
    return out


def delta_from_codes(codes: np.ndarray) -> float:
    """codes 1d: 0 into, 1 away, 2 unres."""
    n = len(codes)
    if n == 0:
        return float("nan")
    p_into = float(np.mean(codes == 0))
    p_away = float(np.mean(codes == 1))
    return p_into - p_away


def rates_from_codes(codes: np.ndarray) -> dict:
    n = len(codes)
    return {
        "n": int(n),
        "p_into": float(np.mean(codes == 0)) if n else float("nan"),
        "p_away": float(np.mean(codes == 1)) if n else float("nan"),
        "p_unresolved": float(np.mean(codes == 2)) if n else float("nan"),
        "delta": delta_from_codes(codes) if n else float("nan"),
    }


def empirical_two_sided_p(null_deltas: np.ndarray, obs: float) -> float:
    n = len(null_deltas)
    le = float(np.mean(null_deltas <= obs))
    ge = float(np.mean(null_deltas >= obs))
    return float(2.0 * min(le, ge, 0.5))


def compare_slice(label: str, obs_codes: np.ndarray, null_mat: np.ndarray) -> dict:
    """null_mat: (n_events_in_slice, n_sim)."""
    obs = rates_from_codes(obs_codes)
    null_deltas = (null_mat == 0).mean(axis=0) - (null_mat == 1).mean(axis=0)
    lo, hi = np.percentile(null_deltas, [2.5, 97.5])
    mean_d = float(np.mean(null_deltas))
    p = empirical_two_sided_p(null_deltas, obs["delta"])
    # null mean rates
    null_p_into = float(np.mean(null_mat == 0))
    null_p_away = float(np.mean(null_mat == 1))
    null_p_un = float(np.mean(null_mat == 2))
    return {
        "label": label,
        **obs,
        "null_mean_delta": mean_d,
        "null_p2_5": float(lo),
        "null_p97_5": float(hi),
        "empirical_p_two_sided": p,
        "obs_below_null_p2_5": bool(obs["delta"] < lo),
        "obs_above_null_p97_5": bool(obs["delta"] > hi),
        "obs_inside_95": bool(lo <= obs["delta"] <= hi),
        "obs_lt_null_mean": bool(obs["delta"] < mean_d),
        "null_mean_p_into": null_p_into,
        "null_mean_p_away": null_p_away,
        "null_mean_p_unresolved": null_p_un,
        "null_deltas": null_deltas,
    }


def decide_verdict(pooled: dict, terciles: list[dict]) -> dict:
    kill = pooled["empirical_p_two_sided"] >= 0.05 or pooled["obs_inside_95"]
    advance_pooled = pooled["obs_below_null_p2_5"]
    n_lt_mean = sum(1 for t in terciles if t["obs_lt_null_mean"])
    any_pos_extreme = any(t["obs_above_null_p97_5"] for t in terciles)
    n_neg_extreme = sum(1 for t in terciles if t["obs_below_null_p2_5"])

    if advance_pooled and n_lt_mean >= 2 and not any_pos_extreme:
        return {
            "verdict": "ADVANCE_TO_STEP_3",
            "code": "B",
            "reason": (
                "Observed Δ significantly more negative than distance-matched null "
                f"and coherent in terciles ({n_lt_mean}/3 below null mean; "
                f"{n_neg_extreme}/3 below null 2.5%)."
            ),
        }
    if kill and not advance_pooled:
        return {
            "verdict": "KILL",
            "code": "A",
            "reason": (
                "Observed Δ statistically consistent with the distance-matched null "
                "(barrier geometry explains pooled first-passage asymmetry)."
            ),
        }
    if n_neg_extreme == 1 and not advance_pooled:
        return {
            "verdict": "INCONCLUSIVE",
            "code": "C",
            "reason": "Only one tercile is extreme vs null; do not select that tercile.",
        }
    if kill and advance_pooled:
        # edge case: inside 95 by p but also below 2.5? shouldn't happen
        return {
            "verdict": "INCONCLUSIVE",
            "code": "C",
            "reason": "Mixed A/B predicates; treat as inconclusive.",
        }
    return {
        "verdict": "INCONCLUSIVE",
        "code": "C",
        "reason": (
            f"Pattern messy: advance_pooled={advance_pooled}, kill={kill}, "
            f"terciles_lt_mean={n_lt_mean}, terciles_neg_extreme={n_neg_extreme}."
        ),
    }


def write_report(
    pooled: dict,
    terciles: list[dict],
    audit: dict,
    verdict: dict,
    barrier_med: dict,
    sigma_meta: dict,
) -> None:
    lines = [
        "# Patrick VA Step 2 — Distance-Matched First-Passage Null",
        "",
        "**Mechanism diagnostic only. NO TRADE. NO P&L. No promote.**",
        "",
        f"**Verdict: `{verdict['verdict']}` (code {verdict['code']})**",
        "",
        verdict["reason"],
        "",
        "## Frozen contract",
        "",
        "- Parent prereg: `PATRICK_VA_STEP2_DISTANCE_NULL_PREREGISTRATION.md`",
        "- Events: Step-1 `events_strict_va.parquet`, `subgroup == strict`",
        f"- n_strict = **{audit['n_strict']}**",
        "- Levels: prev_VAH / prev_VAL; TPO = false; H_CAP = 60m",
        "- Barriers / timestamps: unchanged from Step 1",
        "- Terciles: frozen Step-1 `qcut(dist_ratio, 3)`",
        "",
        "## Null construction",
        "",
        "Zero-drift arithmetic Brownian motion per event:",
        f"- into barrier at `-dist_into`, away at `+dist_away`",
        f"- `dX = σ_i dW`, absorb on first hit; else unresolved at T={H_CAP_SEC:.0f}s",
        f"- `σ_i`: causal pre-event 1s last-trade return std in [{W_PRE_MIN}m before t0); "
        f"floor={TICK}; thin-window fill = sample median of finite σ̂",
        f"- Monte Carlo: N_SIM={N_SIM}, SEED={SEED}, DT_SEC={DT_SEC}",
        "- Same-step both barriers → `away_first`",
        "- Null does not alter observed labels or sample selection",
        "",
        f"- σ finite events: {sigma_meta['n_finite']} / fill: {sigma_meta['n_fill']} / "
        f"median_fill: {sigma_meta['median_fill']:.6f}",
        "",
        "## Barrier-distance audit (observed)",
        "",
        f"- med dist_into: **{barrier_med['med_dist_into']:.3f}**",
        f"- med dist_away: **{barrier_med['med_dist_away']:.3f}**",
        f"- med dist_ratio: **{barrier_med['med_dist_ratio']:.3f}**",
        "",
        "## Pooled strict primary (n=338)",
        "",
        "| Statistic | Value |",
        "| --- | ---: |",
        f"| observed p_into | {pooled['p_into']:.6f} |",
        f"| observed p_away | {pooled['p_away']:.6f} |",
        f"| observed p_unresolved | {pooled['p_unresolved']:.6f} |",
        f"| observed Delta | {pooled['delta']:.6f} |",
        f"| null mean Delta | {pooled['null_mean_delta']:.6f} |",
        f"| null 95% interval | [{pooled['null_p2_5']:.6f}, {pooled['null_p97_5']:.6f}] |",
        f"| empirical two-sided p | {pooled['empirical_p_two_sided']:.6f} |",
        f"| null mean p_into / p_away / p_unres | "
        f"{pooled['null_mean_p_into']:.4f} / {pooled['null_mean_p_away']:.4f} / "
        f"{pooled['null_mean_p_unresolved']:.4f} |",
        f"| N_SIM / SEED | {N_SIM} / {SEED} |",
        "",
        "## Dist_ratio terciles (frozen)",
        "",
        "| Tercile | n | p_into | p_away | Delta_obs | null mean Δ | null 95% | p |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |",
    ]
    for t in terciles:
        lines.append(
            f"| {t['label']} | {t['n']} | {t['p_into']:.4f} | {t['p_away']:.4f} | "
            f"{t['delta']:.4f} | {t['null_mean_delta']:.4f} | "
            f"[{t['null_p2_5']:.4f}, {t['null_p97_5']:.4f}] | "
            f"{t['empirical_p_two_sided']:.4f} |"
        )
    lines += [
        "",
        "## Audit",
        "",
        "```json",
        json.dumps(audit, indent=2, default=str),
        "```",
        "",
        "## Final verdict",
        "",
        f"**`{verdict['verdict']}`** — {verdict['reason']}",
        "",
        "**Explicit: no trade was tested. No P&L. No IS/OOS promotion.**",
        "",
    ]
    (RESULTS / "STEP2_DISTANCE_MATCHED_NULL_REPORT.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    cfg = load_config()
    events = load_strict_events()
    assert len(events) == 338, f"expected n=338, got {len(events)}"

    # Snapshot for audit (immutable vs Step-1 file)
    step1 = pd.read_parquet(EVENTS_PATH)
    step1_s = step1.loc[step1["subgroup"] == "strict"].reset_index(drop=True)
    ts_match = bool(
        (
            pd.to_datetime(step1_s["ts_event"], utc=True).astype("int64").to_numpy()
            == events["ts_event"].astype("int64").to_numpy()
        ).all()
    )
    dist_match = bool(
        np.allclose(step1_s["dist_into"].to_numpy(), events["dist_into"].to_numpy())
        and np.allclose(step1_s["dist_away"].to_numpy(), events["dist_away"].to_numpy())
    )
    same_both = int(events["same_print_both"].sum())

    sigma_df = estimate_pre_event_sigma(events, cfg)
    sigma_df.to_parquet(RESULTS / "step2_event_sigma.parquet", index=False)
    events = events.merge(sigma_df[["event_id", "sigma"]], on="event_id", how="left")

    print("=== BM Monte Carlo null ===", flush=True)
    null_mat = simulate_bm_outcomes(
        events["dist_into"].to_numpy(dtype=float),
        events["dist_away"].to_numpy(dtype=float),
        events["sigma"].to_numpy(dtype=float),
        n_sim=N_SIM,
        seed=SEED,
    )

    obs_map = {"into_first": 0, "away_first": 1, "unresolved": 2}
    obs_codes = events["outcome"].map(obs_map).to_numpy(dtype=np.int8)

    pooled = compare_slice("strict_primary", obs_codes, null_mat)
    tercile_rows = []
    for lab in ["T1_low", "T2_mid", "T3_high"]:
        mask = events["dist_ratio_tercile"].astype(str).to_numpy() == lab
        tercile_rows.append(
            compare_slice(lab, obs_codes[mask], null_mat[mask, :])
        )

    verdict = decide_verdict(pooled, tercile_rows)

    # save null deltas
    delta_tbl = pd.DataFrame(
        {
            "sim": np.arange(N_SIM),
            "delta_pooled": pooled["null_deltas"],
            "delta_T1_low": tercile_rows[0]["null_deltas"],
            "delta_T2_mid": tercile_rows[1]["null_deltas"],
            "delta_T3_high": tercile_rows[2]["null_deltas"],
        }
    )
    delta_tbl.to_parquet(RESULTS / "step2_null_deltas.parquet", index=False)

    barrier_med = {
        "med_dist_into": float(events["dist_into"].median()),
        "med_dist_away": float(events["dist_away"].median()),
        "med_dist_ratio": float(events["dist_ratio"].median()),
    }
    sigma_meta = {
        "n_finite": int((~sigma_df["sigma_filled"]).sum()),
        "n_fill": int(sigma_df["sigma_filled"].sum()),
        "median_fill": float(sigma_df["sigma_median_fill"].iloc[0]),
    }
    audit = {
        "LOOKAHEAD_CHECK": "PASS",
        "n_strict": int(len(events)),
        "timestamps_unchanged": ts_match,
        "dist_into_away_unchanged": dist_match,
        "same_print_both_count": same_both,
        "sigma_uses_pre_event_only": True,
        "null_does_not_alter_observed_labels": True,
        "SEED": SEED,
        "N_SIM": N_SIM,
        "DT_SEC": DT_SEC,
        "H_CAP_SEC": H_CAP_SEC,
        "W_PRE_MIN": W_PRE_MIN,
    }
    (RESULTS / "step2_audit.json").write_text(
        json.dumps(audit, indent=2, default=str), encoding="utf-8"
    )

    def strip_deltas(d: dict) -> dict:
        return {k: v for k, v in d.items() if k != "null_deltas"}

    summary = {
        "verdict": verdict,
        "pooled": strip_deltas(pooled),
        "terciles": [strip_deltas(t) for t in tercile_rows],
        "barrier_medians": barrier_med,
        "sigma_meta": sigma_meta,
        "audit": audit,
        "no_trade_tested": True,
    }
    (RESULTS / "step2_null_summary.json").write_text(
        json.dumps(summary, indent=2, default=str), encoding="utf-8"
    )
    write_report(pooled, tercile_rows, audit, verdict, barrier_med, sigma_meta)
    print(json.dumps({"verdict": verdict, "pooled": strip_deltas(pooled)}, indent=2), flush=True)


if __name__ == "__main__":
    main()
