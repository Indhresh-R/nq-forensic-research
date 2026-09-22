"""Run Strategy 52 Step 2 transition-event study end-to-end."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(CODE))


def main() -> None:
    print("=== Step2 extract ===", flush=True)
    import step2_extract_transitions as s1

    s1.main()

    print("=== Step2 analyze ===", flush=True)
    import step2_analyze as s2

    s2.main()

    print("=== Step2 audit ===", flush=True)
    import step2_audit as s3

    s3.main()

    print("=== Step2 report ===", flush=True)
    from step2_write_report import write_report

    path = write_report()
    print(f"Done: {path}", flush=True)


if __name__ == "__main__":
    main()
