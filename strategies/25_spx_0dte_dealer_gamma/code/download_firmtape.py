"""Download every finished FirmTape session JSON via curl.exe (preserve raw)."""
from __future__ import annotations

import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "data" / "firmtape" / "raw"
META = ROOT / "data" / "firmtape"
BASE = "https://firmtape.com/snapshots/{day}.json"
WORKERS = 8
RETRIES = 5


def fetch_days() -> list[str]:
    cached = META / "days.txt"
    if not cached.exists():
        raise SystemExit("missing data/firmtape/days.txt — refresh via curl /api/days")
    days = [ln.strip() for ln in cached.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if len(days) < 100:
        raise SystemExit(f"days.txt too short: {len(days)}")
    return days


def download_one(day: str) -> tuple[str, str, int]:
    dest = RAW / f"{day}.json"
    if dest.exists() and dest.stat().st_size > 1000:
        return day, "exists", dest.stat().st_size
    url = BASE.format(day=day)
    tmp = dest.with_suffix(".partial")
    last_err = ""
    for attempt in range(RETRIES):
        try:
            if tmp.exists():
                tmp.unlink()
            cmd = [
                "curl.exe",
                "-sL",
                "--fail",
                "--retry",
                "2",
                "--max-time",
                "120",
                "-A",
                "Mozilla/5.0 (compatible; NQ-2-research/1.0)",
                "-o",
                str(tmp),
                url,
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode != 0:
                raise RuntimeError(proc.stderr.strip() or f"curl exit {proc.returncode}")
            if not tmp.exists() or tmp.stat().st_size < 1000:
                raise RuntimeError("empty/short file")
            head = tmp.read_bytes()[:1]
            if head != b"{":
                raise RuntimeError("not json object")
            tmp.replace(dest)
            return day, "ok", dest.stat().st_size
        except Exception as e:  # noqa: BLE001
            last_err = str(e)
            time.sleep(0.4 * (attempt + 1) + 0.1 * attempt)
            if tmp.exists():
                try:
                    tmp.unlink()
                except OSError:
                    pass
    return day, f"fail:{last_err}", 0


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    days = fetch_days()
    print(f"sessions listed: {len(days)}  range {days[-1]} .. {days[0]}", flush=True)
    ok = fail = skip = 0
    fails: list[str] = []
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(download_one, d): d for d in days}
        done = 0
        for fut in as_completed(futs):
            day, status, _nbytes = fut.result()
            done += 1
            if status == "exists":
                skip += 1
            elif status == "ok":
                ok += 1
            else:
                fail += 1
                fails.append(f"{day} {status}")
            if done % 50 == 0 or done == len(days):
                print(
                    f"progress {done}/{len(days)} ok={ok} skip={skip} fail={fail}",
                    flush=True,
                )
    if fails:
        (META / "download_failures.txt").write_text("\n".join(fails) + "\n", encoding="utf-8")
        print(f"wrote {len(fails)} failures to download_failures.txt", flush=True)
    print(f"DONE ok={ok} skip={skip} fail={fail} raw_dir={RAW}", flush=True)


if __name__ == "__main__":
    main()
