"""Frozen defaults for ICT NY SMT discretionary backtest. Do not tune to fit."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "data"
OUT_DIR = Path(__file__).resolve().parents[1]
RESULTS = OUT_DIR / "results"
REPORTS = OUT_DIR / "reports"
FIGS = REPORTS / "figures"

NQ_PATH = DATA_DIR / "nq_1m_continuous.parquet"
ES_PATH = DATA_DIR / "es_1m_continuous.parquet"

TICK = 0.25
POINT_VALUE_NQ = 20.0
POINT_VALUE_MNQ = 2.0  # 1/10 NQ
COMMISSION_PER_SIDE = 2.50
DEFAULT_SLIPPAGE_TICKS = 1.0

SESSION_ANCHOR_HOUR = 18  # futures day starts 18:00 ET
ENTRY_START = (8, 30)  # NY window
ENTRY_END = (11, 30)
FORCE_FLAT = (15, 55)

SWING_LOOKBACK = 3  # candles each side
EQUAL_LIQ_TOL_TICKS = 2
MAX_RISK_POINTS = 60.0
SL_BUFFER_TICKS = 1.0
MAX_TRADES_PER_SESSION = 1

IS_FRAC = 0.60
RANDOM_RUNS = 500
RANDOM_SEED = 42

# 7H bin edges as hours from anchor (18:00): 0, 7, 14, 21, 24
# -> 18:00-01:00, 01:00-08:00, 08:00-15:00, 15:00-18:00
SEVEN_H_EDGES_HOURS = (0, 7, 14, 21, 24)


@dataclass
class BacktestConfig:
    nq_path: Path = NQ_PATH
    es_path: Path = ES_PATH
    tick: float = TICK
    point_value_nq: float = POINT_VALUE_NQ
    point_value_mnq: float = POINT_VALUE_MNQ
    commission_per_side: float = COMMISSION_PER_SIDE
    slippage_ticks: float = DEFAULT_SLIPPAGE_TICKS
    session_anchor_hour: int = SESSION_ANCHOR_HOUR
    entry_start: tuple[int, int] = ENTRY_START
    entry_end: tuple[int, int] = ENTRY_END
    force_flat: tuple[int, int] = FORCE_FLAT
    swing_lookback: int = SWING_LOOKBACK
    equal_liq_tol_ticks: int = EQUAL_LIQ_TOL_TICKS
    max_risk_points: float = MAX_RISK_POINTS
    sl_buffer_ticks: float = SL_BUFFER_TICKS
    max_trades_per_session: int = MAX_TRADES_PER_SESSION
    is_frac: float = IS_FRAC
    random_runs: int = RANDOM_RUNS
    random_seed: int = RANDOM_SEED
    seven_h_edges_hours: tuple[int, ...] = SEVEN_H_EDGES_HOURS
    # Invalidation: True = wick through protected level; False = close through
    invalidate_on_wick: bool = True
    # Entry fill: "close" of confirming 5m bar, or "next_open"
    entry_fill: str = "close"
    # 5m confirmation TF; set 4 for 4-minute variant
    smt_confirm_minutes: int = 5
    # Structure TF for protected level preference
    structure_tf: str = "1H"  # "1H" or "4H"
    partial_tp: bool = False  # 50% at TP1, BE, runner to 2R/3R
    runner_r: float = 2.0


VARIANTS = ("A", "B", "C", "D")
SL_MODES = ("A", "B", "C")
TP_MODES = ("liquidity", "1R", "2R", "3R")
SLIPPAGE_GRID = (0.0, 1.0, 2.0)
