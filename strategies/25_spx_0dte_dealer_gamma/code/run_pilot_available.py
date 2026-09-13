"""
Pilot / partial run on whatever minute JSON is already on disk.

NOT a substitute for the full archive experiment. Labels verdict as SAMPLE_ONLY
when session count < 200 or Discovery years are missing.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "data" / "firmtape" / "raw"
CODE = Path(__file__).resolve().parent


def main() -> None:
    files = [p for p in RAW.glob("????-??-??.json") if p.stat().st_size > 10000]
    print(f"usable raw sessions: {len(files)}", flush=True)
    if len(files) < 5:
        raise SystemExit("insufficient raw FirmTape JSON — see DATA_BLOCKER.md")
    # normalize
    subprocess.check_call([sys.executable, str(CODE / "normalize_firmtape.py")], cwd=str(ROOT))
    # run experiment (will mostly populate OOS / thin Discovery)
    subprocess.check_call([sys.executable, str(CODE / "run_spx_dealer_gamma_experiment.py")], cwd=str(ROOT))
    art = ROOT / "artifacts" / "25_spx_0dte_dealer_gamma"
    note = {
        "warning": "SAMPLE_ONLY — FirmTape bulk snapshot download blocked",
        "n_sessions": len(files),
        "dates": sorted(p.stem for p in files),
        "blocker_doc": "strategies/25_spx_0dte_dealer_gamma/DATA_BLOCKER.md",
    }
    (art / "sample_only_notice.json").write_text(json.dumps(note, indent=2), encoding="utf-8")
    print(json.dumps(note, indent=2), flush=True)


if __name__ == "__main__":
    main()
