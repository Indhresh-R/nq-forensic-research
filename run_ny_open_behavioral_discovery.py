"""Backward-compatible shim. Canonical script: strategies/03_NY_open_level_reactions/code/run_ny_open_behavioral_discovery.py """
from __future__ import annotations

import runpy
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_TARGET = _ROOT.joinpath(*'strategies/03_NY_open_level_reactions/code/run_ny_open_behavioral_discovery.py'.split("/"))
if not _TARGET.exists():
    raise FileNotFoundError(_TARGET)
sys.argv[0] = str(_TARGET)
runpy.run_path(str(_TARGET), run_name="__main__")
