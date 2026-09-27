# Charter amendment — 1m bar VA proxy (atlas scaffold)

**Status:** FROZEN for Strategy 64 rebuild  
**Date:** 2026-09-27  
**Parent:** `CHARTER_ENVIRONMENT_ATLAS.md`  
**Class:** Research scaffold only. **NO TRADE. NOT a Patrick trade-tape VA.**

---

## Why

Trade-built P1 covers ~2026 only. Free multi-year CME trades are not available.  
1m bars span ~2010–2026. A **bar-proxy VA** unlocks history to validate the morning environment catalog idea.

---

## Frozen proxy method (`1m_bar_proxy_v1`)

| Item | Rule |
| --- | --- |
| Source | `data/nq_1m_continuous.parquet` |
| Session | Globex 18:00 → 17:00 ET (same roll as elsewhere) |
| Tick | 0.25 |
| Volume placement | Each bar’s volume spread **uniformly** across integer ticks from `round(low/tick)` to `round(high/tick)` inclusive |
| POC | Tick with max volume; ties → **lowest** tick (same as trade VP helper) |
| VA | Expand from POC to **70%** of session volume (same `expand_value_area` rule as trade VP) |
| Complete session | `n_bars ≥ 500` and `total_volume > 0` |
| Atlas prior VA | Prior **complete** proxy session only |

---

## Honesty / limits

- Proxy ≠ trade-tape VA. Intra-bar volume is unknown.  
- Use for **atlas idea validation** (frequency, persistence, L×D characters).  
- Do **not** promote a sleeve or claim Patrick-level VA precision from this proxy.  
- Optional audit: compare proxy vs Strategy 62 trade P1 on overlapping 2026 sessions (agreement diagnostic only).

---

## Atlas wiring

Strategy 64 Axis L prior source becomes:

`strategies/64_environment_atlas/results/p1_1m_va_proxy.parquet`

Trade P1 remains available for cross-check; it is no longer the primary atlas prior source under this amendment.
