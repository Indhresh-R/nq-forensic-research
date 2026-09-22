"""Run Strategy 53 regime strategy screen end-to-end."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(CODE))


def main() -> None:
    print("=== screen_core ===", flush=True)
    import screen_core as core

    core.main()

    print("=== audit ===", flush=True)
    import audit as aud

    aud.main()

    print("=== report ===", flush=True)
    from write_report import write_report

    print(f"Done: {write_report()}", flush=True)


if __name__ == "__main__":
    main()
