"""Run Strategy 52 Step 3 destination-stability study end-to-end."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(CODE))


def main() -> None:
    print("=== Step3 analyze ===", flush=True)
    import step3_analyze as s1

    s1.main()

    print("=== Step3 audit ===", flush=True)
    import step3_audit as s2

    s2.main()

    print("=== Step3 report ===", flush=True)
    from step3_write_report import write_report

    path = write_report()
    print(f"Done: {path}", flush=True)


if __name__ == "__main__":
    main()
