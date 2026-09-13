"""
Polite FirmTape / gex.live 1-minute snapshot downloader.

- Oldest-first (fills Discovery first)
- Honors HTTP 429 retry_after_s
- Stops on bulk visitor block
- Resume-safe
"""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "data" / "firmtape" / "raw"
META = ROOT / "data" / "firmtape"
# Prefer firmtape host; gex.live is the same archive
HOSTS = ("https://firmtape.com", "https://gex.live")
SLEEP_OK = 4.0
MAX_BLOCKS = 2


def days_oldest_first() -> list[str]:
    d = [ln.strip() for ln in (META / "days.txt").read_text(encoding="utf-8").splitlines() if ln.strip()]
    return list(reversed(d))


def is_block_payload(text: str) -> bool:
    low = text.lower()
    return "bulk" in low and ("copy" in low or "wholesale" in low)


def fetch(day: str, host: str) -> tuple[str, int]:
    dest = RAW / f"{day}.json"
    if dest.exists() and dest.stat().st_size > 10000:
        head = dest.read_text(encoding="utf-8", errors="ignore")[:200]
        if not is_block_payload(head):
            return "exists", 0
    tmp = dest.with_suffix(".partial")
    if tmp.exists():
        tmp.unlink()
    url = f"{host}/snapshots/{day}.json"
    cmd = [
        "curl.exe",
        "-sL",
        "--max-time",
        "120",
        "-A",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "-e",
        f"{host}/session/{day}",
        "-H",
        "Accept: application/json",
        "-o",
        str(tmp),
        "-w",
        "%{http_code}",
        url,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    code = (proc.stdout or "").strip()
    body = tmp.read_text(encoding="utf-8", errors="ignore") if tmp.exists() else ""
    if code == "429":
        retry = 120
        try:
            retry = int(json.loads(body).get("retry_after_s") or 120)
        except Exception:
            pass
        if tmp.exists():
            tmp.unlink()
        return "rate", max(60, retry)
    if code == "403" or is_block_payload(body):
        if tmp.exists():
            tmp.unlink()
        return "blocked", 0
    if code != "200" or not tmp.exists() or tmp.stat().st_size < 1000 or body[:1] != "{":
        if tmp.exists():
            tmp.unlink()
        return f"fail:{code}", 0
    tmp.replace(dest)
    return "ok", 0


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    host = HOSTS[0]
    all_days = days_oldest_first()
    ok = skip = fail = blocked = rate = 0
    blocks_row = 0
    print(f"host={host} days={len(all_days)} start={all_days[0]} end={all_days[-1]}", flush=True)
    for i, day in enumerate(all_days):
        status, wait_s = fetch(day, host)
        if status == "exists":
            skip += 1
            blocks_row = 0
        elif status == "ok":
            ok += 1
            blocks_row = 0
            time.sleep(SLEEP_OK)
        elif status == "rate":
            rate += 1
            print(f"RATE {day} sleep {wait_s}s", flush=True)
            time.sleep(wait_s + 5)
        elif status == "blocked":
            blocked += 1
            blocks_row += 1
            print(f"BLOCKED {day} row={blocks_row}", flush=True)
            if blocks_row >= MAX_BLOCKS:
                print("Exiting for later resume (visitor bulk cap).", flush=True)
                break
            time.sleep(300)
        else:
            fail += 1
            print(f"FAIL {day} {status}", flush=True)
            time.sleep(SLEEP_OK)
        if (i + 1) % 20 == 0 or status in ("ok", "blocked", "rate"):
            have = len([p for p in RAW.glob("????-??-??.json") if p.stat().st_size > 10000])
            print(
                f"progress {i+1}/{len(all_days)} ok={ok} skip={skip} fail={fail} "
                f"rate={rate} blocked={blocked} have={have}",
                flush=True,
            )
    have = len([p for p in RAW.glob("????-??-??.json") if p.stat().st_size > 10000])
    print(f"DONE ok={ok} skip={skip} fail={fail} rate={rate} blocked={blocked} have={have}", flush=True)


if __name__ == "__main__":
    main()
