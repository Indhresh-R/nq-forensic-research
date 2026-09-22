"""Run Event C end-to-end under frozen preregistration."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(CODE))


def main() -> None:
    print("=== Event C analyze ===", flush=True)
    import event_c_analyze as a

    a.main()

    print("=== Event C audit ===", flush=True)
    import event_c_audit as aud

    aud.main()

    print("=== Event C report ===", flush=True)
    from event_c_write_report import write_report

    print(f"Done: {write_report()}", flush=True)


if __name__ == "__main__":
    main()
