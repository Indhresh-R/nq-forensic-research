"""Run Strategy 52 Step 8 path-feasibility audit end-to-end."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(CODE))


def main() -> None:
    print("=== Step8 analyze ===", flush=True)
    import step8_analyze as s1

    s1.main()

    print("=== Step8 audit ===", flush=True)
    import step8_audit as s2

    s2.main()

    print("=== Step8 report ===", flush=True)
    from step8_write_report import write_report

    print(f"Done: {write_report()}", flush=True)


if __name__ == "__main__":
    main()
