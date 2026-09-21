"""Extract the frozen session list. Skips a date that already has an audit file."""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from mbo_orderflow.order_fate.code.extract_day import OUT, extract_day
from research.mbo.sessions import IS_SESSIONS


def main(dates: list[str]) -> None:
    for date_str in dates:
        audit = OUT / "audit" / f"{date_str}.json"
        if audit.exists():
            print(f"[{date_str}] skip", flush=True)
            continue
        extract_day(date_str)


if __name__ == "__main__":
    chosen = sys.argv[1:] or list(IS_SESSIONS)
    main(chosen)
