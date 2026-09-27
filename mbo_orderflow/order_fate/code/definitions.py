"""Frozen order-fate definitions. No market data and no return is read here."""

from __future__ import annotations

from research.mbo.clock import STEP_NS

HORIZONS = (1, 5, 15, 30)
DECISION_HORIZON = 1
PARTIAL_FLOOR = 0.02
MIN_ROWS = 30
PRIMARY_FATES = ("cancel", "fill")
P_COLUMNS = (
    "date",
    "side_sign",
    "age_ms",
    "trade_size_at_price",
    "obi",
    "depth_change",
    "trade_imbalance",
    "replenishment",
    "y1",
    "y5",
    "y15",
    "y30",
)
R_COLUMNS = (
    "date",
    "side_sign",
    "lifetime_ms",
    "fate",
    "obi",
    "depth_change",
    "trade_imbalance",
    "replenishment",
    "y1",
    "y5",
    "y15",
    "y30",
)
BANNED_P_COLUMNS = frozenset(
    {"lifetime_ms", "lifetime", "log_lifetime", "fate", "fate_fill", "terminal_ns"}
)


def anchor_index(terminal_ns: int, open_ns: int, n_bins: int, step_ns: int = STEP_NS) -> int | None:
    """First snapshot index whose timestamp is strictly after the terminal event."""
    idx = (terminal_ns - open_ns) // step_ns + 1
    if idx < 0 or idx >= n_bins:
        return None
    anchor_ns = open_ns + idx * step_ns
    if anchor_ns <= terminal_ns:
        return None
    return int(idx)


def classify_removal(fill_qty: int, unexplained: int) -> str:
    """Label the cancel that removes an order. Price changes are not handled here."""
    if fill_qty <= 0:
        return "cancel"
    if unexplained <= 0:
        return "fill"
    return "partial_then_cancel"


def assert_study_p_schema(columns: list[str] | tuple[str, ...]) -> None:
    banned = BANNED_P_COLUMNS.intersection(columns)
    if banned:
        raise RuntimeError(f"Study P file contains completed-order fields: {sorted(banned)}")
