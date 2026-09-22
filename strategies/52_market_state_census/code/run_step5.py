"""Run Strategy 52 Step 5 signed-exit-position diagnostic end-to-end."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(CODE))


def main() -> None:
    print("=== Step5 analyze ===", flush=True)
    import step5_analyze as s1

    s1.main()

    print("=== Step5 audit ===", flush=True)
    import step5_audit as s2

    s2.main()

    print("=== Step5 report ===", flush=True)
    from step5_write_report import write_report

    path = write_report()
    print(f"Done: {path}", flush=True)


if __name__ == "__main__":
    main()
