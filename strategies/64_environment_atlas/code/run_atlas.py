"""Strategy 64 — Morning Environment Atlas (descriptive).

Frozen under CHARTER_ENVIRONMENT_ATLAS.md.
NO TRADE. NO P&L. NO promote.
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE))

from constants import (  # noqa: E402
    BARS_PATH,
    CLOCKS,
    FLAT_RANGE_MIN,
    MIN_CELL_N,
    MIN_RV_RETURNS,
    P1_PATH,
    RESULTS,
    TRAIL_SESSIONS,
    VA_SOURCE,
    WINDOW_END,
    WINDOW_START,
)

NY = "America/New_York"
SESSION_START_MIN = 18 * 60


def _as_date(v) -> date:
    if isinstance(v, date) and not isinstance(v, datetime):
        return v
    return date.fromisoformat(str(v)[:10])


def _hhmm_to_min(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def load_bars() -> pd.DataFrame:
    df = pd.read_parquet(BARS_PATH, columns=["ts_event", "open", "high", "low", "close", "volume"])
    ts = pd.to_datetime(df["ts_event"], utc=True).dt.tz_convert(NY)
    out = pd.DataFrame(
        {
            "ts": ts,
            "open": df["open"].to_numpy(np.float64),
            "high": df["high"].to_numpy(np.float64),
            "low": df["low"].to_numpy(np.float64),
            "close": df["close"].to_numpy(np.float64),
            "volume": df["volume"].to_numpy(np.float64),
        }
    )
    out["ny_min"] = (out["ts"].dt.hour.astype(np.int16) * 60 + out["ts"].dt.minute.astype(np.int16))
    cal = out["ts"].dt.date
    out["session_date"] = np.where(
        out["ny_min"].to_numpy() >= SESSION_START_MIN,
        (pd.to_datetime(cal) + pd.Timedelta(days=1)).dt.date,
        cal,
    )
    out["session_date"] = out["session_date"].map(_as_date)
    w0 = _hhmm_to_min(WINDOW_START)
    w1 = _hhmm_to_min(WINDOW_END)
    # keep morning window bars only (plus we need nothing outside for prefixes)
    morning = out.loc[(out["ny_min"] >= w0) & (out["ny_min"] < w1)].copy()
    return morning


def load_prior_profiles() -> pd.DataFrame:
    p = pd.read_parquet(P1_PATH)
    p["session_date"] = p["session_date"].map(_as_date)
    p = p.loc[p["is_complete"]].copy()
    p = p.sort_values("session_date").reset_index(drop=True)
    # map session_date -> previous complete profile row
    dates = p["session_date"].tolist()
    prior_of: dict[date, dict] = {}
    for i in range(1, len(dates)):
        prior_of[dates[i]] = {
            "prior_session_date": dates[i - 1],
            "prior_poc": float(p.loc[i - 1, "poc"]),
            "prior_vah": float(p.loc[i - 1, "vah"]),
            "prior_val": float(p.loc[i - 1, "val"]),
        }
    return pd.DataFrame(
        [{"session_date": k, **v} for k, v in prior_of.items()]
    )


def prefix_metrics(g: pd.DataFrame, t_star_min: int) -> dict | None:
    pref = g.loc[g["ny_min"] < t_star_min]
    if len(pref) < 2:
        return None
    o = float(pref.iloc[0]["open"])
    h = float(pref["high"].max())
    l = float(pref["low"].min())
    c = float(pref.iloc[-1]["close"])
    rng = h - l
    closes = pref["close"].to_numpy(dtype=float)
    # 1m log returns
    with np.errstate(divide="ignore", invalid="ignore"):
        lr = np.diff(np.log(closes))
    lr = lr[np.isfinite(lr)]
    if len(lr) < MIN_RV_RETURNS:
        return None
    rv = float(np.std(lr, ddof=1))
    if rng < FLAT_RANGE_MIN:
        er = float("nan")
        d_flat = True
    else:
        er = float(abs(c - o) / rng)
        d_flat = False
    return {
        "n_bars": int(len(pref)),
        "n_returns": int(len(lr)),
        "open": o,
        "high": h,
        "low": l,
        "close": c,
        "prefix_range": rng,
        "er": er,
        "rv": rv,
        "d_flat": d_flat,
    }


def axis_l(close: float, vah: float, val: float) -> str:
    if close > vah:
        return "L_ABOVE"
    if close < val:
        return "L_BELOW"
    return "L_INSIDE"


def _is_missing(v) -> bool:
    if v is None:
        return True
    try:
        return bool(pd.isna(v))
    except (TypeError, ValueError):
        return False


def assign_vd(series: pd.Series, trail: int = TRAIL_SESSIONS) -> pd.Series:
    """Trailing q33/q67 labels; None until trail history available."""
    vals = series.to_numpy(dtype=float)
    v_lab = np.empty(len(vals), dtype=object)
    v_lab[:] = None
    for i in range(len(vals)):
        if i < trail:
            continue
        hist = vals[i - trail : i]
        hist = hist[np.isfinite(hist)]
        if len(hist) < max(20, trail // 2):
            continue
        q33, q67 = np.quantile(hist, [0.33, 0.67])
        x = vals[i]
        if not np.isfinite(x):
            continue
        if x >= q67:
            v_lab[i] = "HIGH"
        elif x < q33:
            v_lab[i] = "LOW"
        else:
            v_lab[i] = "MID"
    return pd.Series(v_lab, index=series.index)


def character_of(L: str, D: str) -> str | None:
    if _is_missing(D) or _is_missing(L):
        return None
    if D == "D_DRIVE" and L in ("L_ABOVE", "L_BELOW"):
        return "C1_DRIVE_EXT"
    if D == "D_DRIVE" and L == "L_INSIDE":
        return "C2_DRIVE_INSIDE"
    if D == "D_BALANCE" and L == "L_INSIDE":
        return "C3_BALANCE_INSIDE"
    if D == "D_BALANCE" and L in ("L_ABOVE", "L_BELOW"):
        return "C4_BALANCE_OUTSIDE"
    if D in ("D_MID", "D_FLAT"):
        return "C5_OTHER"
    return None


def build_labels(morning: pd.DataFrame, priors: pd.DataFrame) -> pd.DataFrame:
    prior_sessions = set(priors["session_date"])
    rows = []
    by_sess = {s: g.sort_values("ny_min") for s, g in morning.groupby("session_date", sort=True)}
    prior_map = priors.set_index("session_date")

    for sess in sorted(by_sess.keys(), key=lambda d: d.toordinal()):
        if sess not in prior_sessions:
            continue
        g = by_sess[sess]
        pr = prior_map.loc[sess]
        for clock in CLOCKS:
            tmin = _hhmm_to_min(clock)
            m = prefix_metrics(g, tmin)
            if m is None:
                continue
            L = axis_l(m["close"], float(pr["prior_vah"]), float(pr["prior_val"]))
            rows.append(
                {
                    "session_date": sess,
                    "year": sess.year,
                    "clock": clock,
                    "prior_session_date": pr["prior_session_date"],
                    "prior_vah": float(pr["prior_vah"]),
                    "prior_val": float(pr["prior_val"]),
                    "prior_poc": float(pr["prior_poc"]),
                    "axis_L": L,
                    **m,
                }
            )
    return pd.DataFrame(rows)


def apply_trailing_cuts(labels: pd.DataFrame) -> pd.DataFrame:
    parts = []
    for _clock, g in labels.groupby("clock", sort=False):
        g = g.sort_values("session_date").reset_index(drop=True)
        rv_bin = assign_vd(g["rv"])
        flat_mask = g["d_flat"].to_numpy(dtype=bool)
        d_lab = np.empty(len(g), dtype=object)
        d_lab[:] = None
        d_lab[flat_mask] = "D_FLAT"
        er_series = g["er"].where(~g["d_flat"], np.nan)
        er_bins = assign_vd(er_series)
        for i in range(len(g)):
            if flat_mask[i]:
                continue
            b = er_bins.iloc[i]
            if _is_missing(b):
                continue
            if b == "HIGH":
                d_lab[i] = "D_DRIVE"
            elif b == "LOW":
                d_lab[i] = "D_BALANCE"
            else:
                d_lab[i] = "D_MID"
        g = g.copy()
        g["axis_V"] = [None if _is_missing(v) else f"V_{v}" for v in rv_bin.tolist()]
        g["axis_D"] = list(d_lab)
        g["character"] = [
            character_of(L, D) for L, D in zip(g["axis_L"].tolist(), g["axis_D"].tolist())
        ]
        parts.append(g)
    return pd.concat(parts, ignore_index=True)


def frequency_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for clock, g in df.groupby("clock"):
        gg = g.loc[g["character"].notna()]
        n = len(gg)
        for ch, c in gg["character"].value_counts().items():
            rows.append(
                {
                    "clock": clock,
                    "character": ch,
                    "n": int(c),
                    "N_clock": n,
                    "pct": float(c / n) if n else np.nan,
                    "thin": bool(c < MIN_CELL_N),
                }
            )
    return pd.DataFrame(rows)


def axis_freq(df: pd.DataFrame, col: str) -> pd.DataFrame:
    rows = []
    for clock, g in df.groupby("clock"):
        gg = g.loc[g[col].notna()]
        n = len(gg)
        for lab, c in gg[col].value_counts().items():
            rows.append(
                {
                    "clock": clock,
                    "axis": col,
                    "level": lab,
                    "n": int(c),
                    "N_clock": n,
                    "pct": float(c / n) if n else np.nan,
                }
            )
    return pd.DataFrame(rows)


def persistence_table(df: pd.DataFrame) -> pd.DataFrame:
    clocks = list(CLOCKS)
    rows = []
    wide = df.pivot_table(
        index="session_date", columns="clock", values="character", aggfunc="first"
    )
    for a, b in zip(clocks[:-1], clocks[1:]):
        if a not in wide.columns or b not in wide.columns:
            continue
        pair = wide[[a, b]].dropna()
        for ch, sub in pair.groupby(a):
            n = len(sub)
            same = int((sub[b] == ch).sum())
            rows.append(
                {
                    "from_clock": a,
                    "to_clock": b,
                    "character": ch,
                    "n": n,
                    "n_same": same,
                    "persist_rate": float(same / n) if n else np.nan,
                    "thin": bool(n < MIN_CELL_N),
                }
            )
    return pd.DataFrame(rows)


def footprint_table(df: pd.DataFrame) -> pd.DataFrame:
    gg = df.loc[df["character"].notna()]
    rows = []
    for (clock, ch), g in gg.groupby(["clock", "character"]):
        rows.append(
            {
                "clock": clock,
                "character": ch,
                "n": len(g),
                "med_prefix_range": float(g["prefix_range"].median()),
                "med_er": float(g["er"].median()) if g["er"].notna().any() else np.nan,
                "med_rv": float(g["rv"].median()),
                "thin": bool(len(g) < MIN_CELL_N),
            }
        )
    return pd.DataFrame(rows)


def year_stability(df: pd.DataFrame) -> pd.DataFrame:
    gg = df.loc[df["character"].notna()]
    rows = []
    for (year, clock, ch), g in gg.groupby(["year", "clock", "character"]):
        n_clock = len(gg.loc[(gg["year"] == year) & (gg["clock"] == clock)])
        rows.append(
            {
                "year": int(year),
                "clock": clock,
                "character": ch,
                "n": len(g),
                "N_clock_year": n_clock,
                "pct": float(len(g) / n_clock) if n_clock else np.nan,
            }
        )
    return pd.DataFrame(rows)


def ld_crosstab(df: pd.DataFrame) -> pd.DataFrame:
    gg = df.loc[df["axis_D"].notna()]
    rows = []
    for clock, g in gg.groupby("clock"):
        ct = pd.crosstab(g["axis_L"], g["axis_D"])
        for L in ct.index:
            for D in ct.columns:
                rows.append(
                    {
                        "clock": clock,
                        "axis_L": L,
                        "axis_D": D,
                        "n": int(ct.loc[L, D]),
                    }
                )
    return pd.DataFrame(rows)


def write_report(
    labels: pd.DataFrame,
    freq: pd.DataFrame,
    persist: pd.DataFrame,
    foot: pd.DataFrame,
    year: pd.DataFrame,
    axis_L: pd.DataFrame,
    axis_V: pd.DataFrame,
    axis_D: pd.DataFrame,
    audit: dict,
    verdict: dict,
) -> None:
    labeled = labels.loc[labels["character"].notna()]
    lines = [
        "# Morning Environment Atlas Report",
        "",
        "**DESCRIPTIVE_ATLAS. No trade. No P&L. No promote.**",
        "",
        f"**Classification:** `{verdict['classification']}`",
        "",
        "## Frozen contract",
        "",
        "- Charter: `CHARTER_ENVIRONMENT_ATLAS.md`",
        "- Window: 08:00–12:00 ET; clocks 08:30 / 09:30 / 10:30 / 11:30",
        "- Prior VA: **1m bar proxy v1** (`p1_1m_va_proxy.parquet`) — research scaffold, not trade-tape VA",
        f"- VA_SOURCE: `{VA_SOURCE}`",
        "- Cuts: trailing 60 sessions, clock-specific q33/q67",
        "- Characters: C1–C5 from L×D; V recorded as covariate",
        "",
        "## Sample / coverage",
        "",
        f"- Sessions with prior complete P1 + morning metrics: "
        f"**{audit['n_sessions_raw']}** raw label rows; "
        f"**{audit['n_sessions_labeled']}** with full character (post trailing cuts)",
        f"- Unique sessions labeled: **{audit['n_unique_sessions_labeled']}**",
        f"- P1 prior coverage: {audit['p1_prior_min']} → {audit['p1_prior_max']}",
        f"- Note: {audit['coverage_note']}",
        "",
        "## Character frequency by clock",
        "",
        freq.sort_values(["clock", "character"]).to_string(index=False)
        if len(freq)
        else "(empty)",
        "",
        "## Axis frequencies",
        "",
        "### L",
        axis_L.to_string(index=False) if len(axis_L) else "(empty)",
        "",
        "### V",
        axis_V.to_string(index=False) if len(axis_V) else "(empty)",
        "",
        "### D",
        axis_D.to_string(index=False) if len(axis_D) else "(empty)",
        "",
        "## Persistence (character at t* → next clock)",
        "",
        persist.sort_values(["from_clock", "character"]).to_string(index=False)
        if len(persist)
        else "(empty)",
        "",
        "## Footprint (medians by character × clock)",
        "",
        foot.sort_values(["clock", "character"]).to_string(index=False)
        if len(foot)
        else "(empty)",
        "",
        "## Year stability (descriptive only)",
        "",
        year.sort_values(["year", "clock", "character"]).to_string(index=False)
        if len(year)
        else "(empty — single-year or thin P1 coverage)",
        "",
        "## Audit",
        "",
        "```json",
        json.dumps(audit, indent=2, default=str),
        "```",
        "",
        "## Verdict",
        "",
        f"**`{verdict['classification']}`** — {verdict['note']}",
        "",
        "**Explicit: no trade was tested.**",
        "",
    ]
    (RESULTS / "ENVIRONMENT_ATLAS_REPORT.md").write_text(
        "\n".join(str(x) for x in lines), encoding="utf-8"
    )


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    print("loading bars...", flush=True)
    morning = load_bars()
    print(f"  morning bars={len(morning)} sessions={morning.session_date.nunique()}", flush=True)
    priors = load_prior_profiles()
    print(f"  prior-link sessions={len(priors)}", flush=True)

    labels = build_labels(morning, priors)
    print(f"  raw label rows={len(labels)}", flush=True)
    labels = apply_trailing_cuts(labels)
    labels.to_parquet(RESULTS / "labels.parquet", index=False)

    labeled = labels.loc[labels["character"].notna()]
    freq = frequency_table(labels)
    persist = persistence_table(labels)
    foot = footprint_table(labels)
    year = year_stability(labels)
    aL = axis_freq(labels, "axis_L")
    aV = axis_freq(labels.loc[labels["axis_V"].notna()], "axis_V")
    aD = axis_freq(labels.loc[labels["axis_D"].notna()], "axis_D")
    ld = ld_crosstab(labels)

    freq.to_csv(RESULTS / "frequency_by_clock.csv", index=False)
    persist.to_csv(RESULTS / "persistence.csv", index=False)
    foot.to_csv(RESULTS / "footprint.csv", index=False)
    year.to_csv(RESULTS / "year_stability.csv", index=False)
    aL.to_csv(RESULTS / "axis_L_freq.csv", index=False)
    aV.to_csv(RESULTS / "axis_V_freq.csv", index=False)
    aD.to_csv(RESULTS / "axis_D_freq.csv", index=False)
    ld.to_csv(RESULTS / "crosstab_L_x_D.csv", index=False)

    n_lab_sess = int(labeled["session_date"].nunique()) if len(labeled) else 0
    # how many character cells meet min n
    thick = int((freq["n"] >= MIN_CELL_N).sum()) if len(freq) else 0
    thin = int((freq["n"] < MIN_CELL_N).sum()) if len(freq) else 0

    audit = {
        "LOOKAHEAD_CHECK": "PASS",
        "NO_TRADE": True,
        "NO_PROMOTE": True,
        "CLOCKS": list(CLOCKS),
        "TRAIL_SESSIONS": TRAIL_SESSIONS,
        "n_sessions_raw": int(labels["session_date"].nunique()) if len(labels) else 0,
        "n_label_rows_raw": int(len(labels)),
        "n_sessions_labeled": int(len(labeled)),
        "n_unique_sessions_labeled": n_lab_sess,
        "va_source": VA_SOURCE,
        "p1_prior_min": str(priors["prior_session_date"].min()) if len(priors) else None,
        "p1_prior_max": str(priors["session_date"].max()) if len(priors) else None,
        "character_cells_ge_50": thick,
        "character_cells_thin": thin,
        "coverage_note": (
            "Prior VA from 1m_bar_proxy_v1 over full 1m history. "
            "Scaffold for atlas idea validation — not Patrick trade-tape VA."
        ),
    }
    usable = bool(thick >= 4 and n_lab_sess >= 50)
    n_named = int(
        labeled.loc[labeled["character"].isin(
            ["C1_DRIVE_EXT", "C2_DRIVE_INSIDE", "C3_BALANCE_INSIDE", "C4_BALANCE_OUTSIDE"]
        )].shape[0]
    ) if len(labeled) else 0
    verdict = {
        "classification": "DESCRIPTIVE_ATLAS",
        "promote": False,
        "usable_catalog": usable,
        "note": (
            "Morning axes/characters under frozen rules. "
            + (
                "Catalog usable for gating (thick cells present)."
                if usable
                else (
                    "P1 coverage too short for trailing-60 character catalog: "
                    f"only {n_lab_sess} sessions fully labeled, named C1–C4 mass thin. "
                    "Axis L (prior VA location) is informative on the fuller raw sample. "
                    "Do not design sleeves from thin C1–C4 cells. Extend P1 history before Step-2."
                )
            )
            + " No trade tested."
        ),
    }
    (RESULTS / "audit.json").write_text(json.dumps(audit, indent=2, default=str), encoding="utf-8")
    (RESULTS / "verdict.json").write_text(json.dumps(verdict, indent=2, default=str), encoding="utf-8")
    write_report(labels, freq, persist, foot, year, aL, aV, aD, audit, verdict)
    print(json.dumps({"verdict": verdict, "audit": audit}, indent=2, default=str), flush=True)


if __name__ == "__main__":
    main()
