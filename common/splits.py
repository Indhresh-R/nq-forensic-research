"""Chronological research splits (frozen program standard)."""
from __future__ import annotations

IS_YEARS = set(range(2010, 2022))
VAL_YEARS = {2022, 2023, 2024}
OOS_YEARS = {2025, 2026}


def split_of(year: int) -> str:
    if year in IS_YEARS:
        return "IS"
    if year in VAL_YEARS:
        return "Validation"
    if year in OOS_YEARS:
        return "OOS"
    return "OTHER"
