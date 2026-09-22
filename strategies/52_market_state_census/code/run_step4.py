"""Run Strategy 52 Step 4 matched-transition study end-to-end."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(CODE))


def main() -> None:
    print("=== Step4 analyze ===", flush=True)
    import step4_analyze as s1

    s1.main()

    print("=== Step4 audit ===", flush=True)
    import step4_audit as s2

    s2.main()

    print("=== Step4 report ===", flush=True)
    from step4_write_report import write_report

    path = write_report()
    print(f"Done: {path}", flush=True)


if __name__ == "__main__":
    main()
