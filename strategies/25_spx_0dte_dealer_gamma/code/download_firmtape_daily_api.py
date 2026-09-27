"""Download FirmTape public /api/session/{day} summaries (allowed; not bulk snapshots)."""
from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
META = ROOT / "data" / "firmtape"
OUT = ROOT / "data" / "firmtape" / "processed" / "firmtape_daily_api.parquet"
RAW_DAILY = ROOT / "data" / "firmtape" / "daily_api"


def main() -> None:
    days = [ln.strip() for ln in (META / "days.txt").read_text(encoding="utf-8").splitlines() if ln.strip()]
    RAW_DAILY.mkdir(parents=True, exist_ok=True)
    rows = []
    for i, day in enumerate(days):
        dest = RAW_DAILY / f"{day}.json"
        if dest.exists() and dest.stat().st_size > 50:
            payload = json.loads(dest.read_text(encoding="utf-8"))
        else:
            url = f"https://firmtape.com/api/session/{day}"
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; NQ-2-research/1.0)",
                    "Accept": "application/json",
                },
            )
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    data = r.read()
                dest.write_bytes(data)
                payload = json.loads(data.decode("utf-8"))
            except Exception as e:  # noqa: BLE001
                print(f"FAIL {day} {e}", flush=True)
                time.sleep(1.0)
                continue
            time.sleep(0.05)
        eh = payload.get("expected_hold_band") or {}
        rows.append(
            {
                "session_date": payload.get("day") or day,
                "open": payload.get("open"),
                "close": payload.get("close"),
                "high": payload.get("high"),
                "low": payload.get("low"),
                "vwap_close": payload.get("vwap_close"),
                "zero_gamma_flip": payload.get("zero_gamma_flip"),
                "call_resistance": payload.get("call_resistance"),
                "put_support": payload.get("put_support"),
                "hold_lo": eh.get("low"),
                "hold_hi": eh.get("high"),
                "atm_iv_open": payload.get("atm_iv_open"),
                "net_gamma_percentile": payload.get("net_gamma_percentile"),
                "flip_crossings": payload.get("flip_crossings"),
            }
        )
        if (i + 1) % 100 == 0:
            print(f"daily api {i+1}/{len(days)}", flush=True)
    import pandas as pd

    df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT, index=False)
    print(f"DONE n={len(df)} -> {OUT}", flush=True)


if __name__ == "__main__":
    main()
