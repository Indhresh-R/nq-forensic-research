"""
Orchestrate Strategy 52 Step 0 market-state census end-to-end.

Order: features → classify → distribution → persistence → audit → report.
"""
from __future__ import annotations

import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CODE = Path(__file__).resolve().parent
STRAT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(CODE))

from constants import RESULTS


def _git_hash() -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=str(ROOT), stderr=subprocess.DEVNULL
        )
        return out.decode().strip()
    except Exception:
        return None


def _env_info() -> dict:
    import numpy as np
    import pandas as pd

    return {
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "git_hash": _git_hash(),
        "run_utc": datetime.now(timezone.utc).isoformat(),
    }


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    env = _env_info()
    (RESULTS / "environment.json").write_text(json.dumps(env, indent=2), encoding="utf-8")

    print("=== 1/5 build features ===")
    import build_market_state_features as step1

    step1.main()

    print("=== 2/5 classify ===")
    import classify_market_states as step2

    step2.main()

    print("=== 3/5 distribution ===")
    import analyze_state_distribution as step3

    step3.main()

    print("=== 4/5 persistence ===")
    import analyze_state_persistence as step4

    step4.main()

    print("=== 5/5 audit + report ===")
    import audit_market_state as step5

    step5.main()

    from write_census_report import write_report

    report_path = write_report()
    print(f"Done. Report: {report_path}")


if __name__ == "__main__":
    main()
