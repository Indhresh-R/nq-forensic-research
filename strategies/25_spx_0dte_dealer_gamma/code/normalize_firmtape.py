"""Normalize FirmTape raw session JSON → minute-level Parquet panel."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "data" / "firmtape" / "raw"
OUT = ROOT / "data" / "firmtape" / "processed"
MINUTE_COLS = [
    "spot",
    "vwap",
    "b2u",
    "b2l",
    "flip",
    "gpct",
    "ngv_meas",
    "ngv_conv",
    "charm",
    "dex",
    "vex",
    "skew",
    "skewpct",
    "hold_lo",
    "hold_hi",
    "exp_range",
    "straddle",
    "atmiv",
    "div30",
    "rvi15",
    "rvi30",
    "rvi60",
    "hhi",
    "flowvel",
]


def _last_of_minute(secs: list, values: list) -> dict[str, object]:
    """Map HH:MM → last second observation in that minute."""
    out: dict[str, object] = {}
    for s, v in zip(secs, values):
        if not isinstance(s, str) or len(s) < 5:
            continue
        m = s[:5]
        out[m] = v
    return out


def session_to_rows(path: Path) -> list[dict]:
    d = json.loads(path.read_text(encoding="utf-8"))
    day = d.get("day") or path.stem
    minutes = d.get("minutes") or []
    n = len(minutes)
    rows: list[dict] = []

    # Volume-convention net gamma: last second of each minute from sec book
    vol_by_min: dict[str, object] = {}
    flip_vol_by_min: dict[str, object] = {}
    vanna_by_min: dict[str, object] = {}
    cr0_by_min: dict[str, object] = {}
    ps0_by_min: dict[str, object] = {}
    sec = d.get("sec") or {}
    if isinstance(sec, dict) and sec.get("secs"):
        vol_by_min = _last_of_minute(sec["secs"], sec.get("ngv_volcp") or [])
        flip_vol_by_min = _last_of_minute(sec["secs"], sec.get("flip_volcp") or [])
        vanna_by_min = _last_of_minute(sec["secs"], sec.get("vanna") or [])
        cr0_by_min = _last_of_minute(sec["secs"], sec.get("cr0") or [])
        ps0_by_min = _last_of_minute(sec["secs"], sec.get("ps0") or [])

    # Peak +/- gamma strikes from measured flow ladder frames (5-min)
    # Attach last known frame peak to subsequent minutes until next frame.
    pos_peak = [None] * n
    neg_peak = [None] * n
    frames = d.get("frames") or []
    if isinstance(frames, list) and frames:
        frame_by_t = {fr.get("t"): fr for fr in frames if isinstance(fr, dict)}
        last_pos = last_neg = None
        for i, m in enumerate(minutes):
            fr = frame_by_t.get(m)
            if fr and fr.get("strikes") and fr.get("g") is not None:
                strikes = fr["strikes"]
                g = fr["g"]
                if strikes and g and len(strikes) == len(g):
                    jmax = int(np.nanargmax(np.asarray(g, dtype=float)))
                    jmin = int(np.nanargmin(np.asarray(g, dtype=float)))
                    last_pos = float(strikes[jmax])
                    last_neg = float(strikes[jmin])
            pos_peak[i] = last_pos
            neg_peak[i] = last_neg

    gb = d.get("ga_backfill") or {}
    for i, m in enumerate(minutes):
        row = {
            "session_date": day,
            "minute": m,
            "built": d.get("built"),
            "ga_backfill_at": gb.get("at"),
            "ga_backfill_applied": gb.get("applied"),
            "pos_gamma_peak": pos_peak[i],
            "neg_gamma_peak": neg_peak[i],
            "ngv_vol": vol_by_min.get(m),
            "flip_vol": flip_vol_by_min.get(m),
            "vanna": vanna_by_min.get(m),
            "cr0": cr0_by_min.get(m),
            "ps0": ps0_by_min.get(m),
        }
        for col in MINUTE_COLS:
            arr = d.get(col)
            row[col] = arr[i] if isinstance(arr, list) and i < len(arr) else None
        rows.append(row)
    return rows


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    files = sorted(RAW.glob("????-??-??.json"))
    print(f"raw sessions: {len(files)}", flush=True)
    if not files:
        raise SystemExit("no raw FirmTape JSON found — run download_firmtape.py first")

    all_rows: list[dict] = []
    for i, path in enumerate(files):
        rows = session_to_rows(path)
        if not rows:
            print(f"empty {path.name}", flush=True)
            continue
        all_rows.extend(rows)
        if (i + 1) % 100 == 0 or (i + 1) == len(files):
            print(f"parsed {i+1}/{len(files)} sessions rows={len(all_rows)}", flush=True)

    df = pd.DataFrame(all_rows)
    for col in MINUTE_COLS + [
        "pos_gamma_peak",
        "neg_gamma_peak",
        "ngv_vol",
        "flip_vol",
        "vanna",
        "cr0",
        "ps0",
    ]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in ("built", "ga_backfill_at", "ga_backfill_applied", "session_date", "minute"):
        if col in df.columns:
            df[col] = df[col].astype("string")
    ts = pd.to_datetime(df["session_date"].astype(str) + " " + df["minute"].astype(str), format="%Y-%m-%d %H:%M")
    df["ts"] = ts.dt.tz_localize("America/New_York", ambiguous="infer", nonexistent="shift_forward")
    df["year"] = df["ts"].dt.year.astype(np.int16)
    df["ny_min"] = (df["ts"].dt.hour.astype(np.int16) * 60 + df["ts"].dt.minute.astype(np.int16))
    out_path = OUT / "firmtape_minutes.parquet"
    df.to_parquet(out_path, index=False, compression="zstd")
    n_sessions = int(df["session_date"].nunique())
    n_rows = len(df)

    # session index
    idx = []
    for path in files:
        try:
            meta = json.loads(path.read_text(encoding="utf-8"))
            mins = meta.get("minutes") or []
            idx.append(
                {
                    "session_date": meta.get("day") or path.stem,
                    "built": meta.get("built"),
                    "n_minutes": len(mins),
                    "first_minute": mins[0] if mins else None,
                    "last_minute": mins[-1] if mins else None,
                    "bytes": path.stat().st_size,
                    "ga_backfill_at": (meta.get("ga_backfill") or {}).get("at"),
                }
            )
        except Exception as e:  # noqa: BLE001
            idx.append({"session_date": path.stem, "error": str(e)})
    pd.DataFrame(idx).to_parquet(OUT / "firmtape_sessions.parquet", index=False)
    print(f"DONE sessions={n_sessions} rows={n_rows} -> {OUT}", flush=True)


if __name__ == "__main__":
    main()
