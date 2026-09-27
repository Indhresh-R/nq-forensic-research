"""Run Event B end-to-end under frozen preregistration."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(CODE))


def main() -> None:
    print("=== Event B analyze ===", flush=True)
    import event_b_analyze as a

    a.main()

    print("=== Event B audit ===", flush=True)
    import event_b_audit as aud

    aud.main()

    print("=== Event B report ===", flush=True)
    from event_b_write_report import write_report

    print(f"Done: {write_report()}", flush=True)


if __name__ == "__main__":
    main()
