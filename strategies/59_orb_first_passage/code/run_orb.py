"""Run Strategy 59 ORB first-passage end-to-end."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(CODE))


def main() -> None:
    print("=== ORB analyze ===", flush=True)
    import orb_analyze as a

    a.main()

    print("=== ORB audit ===", flush=True)
    import orb_audit as aud

    aud.main()

    print("=== ORB report ===", flush=True)
    from orb_write_report import write_report

    print(f"Done: {write_report()}", flush=True)


if __name__ == "__main__":
    main()
