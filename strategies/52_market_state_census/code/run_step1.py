"""Run Strategy 52 Step 1 path-geometry study end-to-end."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(CODE))


def main() -> None:
    print("=== Step1 extract ===", flush=True)
    import step1_extract_paths as s1

    s1.main()

    print("=== Step1 analyze ===", flush=True)
    import step1_analyze as s2

    s2.main()

    print("=== Step1 audit ===", flush=True)
    import step1_audit as s3

    s3.main()

    print("=== Step1 report ===", flush=True)
    from step1_write_report import write_report

    path = write_report()
    print(f"Done: {path}", flush=True)


if __name__ == "__main__":
    main()
