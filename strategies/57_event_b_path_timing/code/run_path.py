"""Run Strategy 57 path/timing diagnostic end-to-end."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(CODE))


def main() -> None:
    print("=== Path analyze ===", flush=True)
    import path_analyze as a

    a.main()

    print("=== Path audit ===", flush=True)
    import path_audit as aud

    aud.main()

    print("=== Path report ===", flush=True)
    from path_write_report import write_report

    print(f"Done: {write_report()}", flush=True)


if __name__ == "__main__":
    main()
