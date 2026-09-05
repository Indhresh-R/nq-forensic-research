"""Backward-compatible shim. Canonical script: strategies/11_HIGH_residual_economics/code/run_nq_high_resid_econ.py """
from __future__ import annotations

import runpy
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_TARGET = _ROOT.joinpath(*'strategies/11_HIGH_residual_economics/code/run_nq_high_resid_econ.py'.split("/"))
if not _TARGET.exists():
    raise FileNotFoundError(_TARGET)
sys.argv[0] = str(_TARGET)
runpy.run_path(str(_TARGET), run_name="__main__")
