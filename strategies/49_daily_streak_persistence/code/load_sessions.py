"""Load Strategy 48's session builder without editing that study."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def _load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_complete_candles():
    """Call Strategy 48 `load_candles`. Session rules stay in that file."""
    root = Path(__file__).resolve().parents[3]
    code_48 = root / "strategies" / "48_daily_candle_continuation" / "code"
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    saved_definitions = sys.modules.get("definitions")
    saved_candles = sys.modules.get("candles")
    _load_module("definitions", code_48 / "definitions.py")
    candles = _load_module("candles", code_48 / "candles.py")
    try:
        return candles.load_candles()
    finally:
        if saved_definitions is None:
            sys.modules.pop("definitions", None)
        else:
            sys.modules["definitions"] = saved_definitions
        if saved_candles is None:
            sys.modules.pop("candles", None)
        else:
            sys.modules["candles"] = saved_candles
