# Strategy 64 — COMPLETE (DESCRIPTIVE_ATLAS, 1m VA proxy)

**Status:** Rebuilt under `CHARTER_ENVIRONMENT_ATLAS.md` + `CHARTER_ENVIRONMENT_ATLAS_1M_VA_PROXY.md`.  
**Classification:** `DESCRIPTIVE_ATLAS` / `usable_catalog: true`.  
**No trade. No P&L. No promote.**

## What changed

Prior VA now from **1m bar proxy v1** over full continuous history (not 2026 trade P1).

| Item | Value |
| --- | --- |
| Proxy sessions complete | **3612** (2010-06 → 2026-08) |
| Mornings with full character (post trail-60) | **~3551** |
| Character cells n≥50 | **20 / 20** |
| VA source | `1m_bar_proxy_v1` (scaffold ≠ trade tape) |

## Headline frequencies (09:30)

| Character | Share |
| --- | --- |
| C5_OTHER | ~33% |
| C1_DRIVE_EXT | ~22% |
| C4_BALANCE_OUTSIDE | ~21% |
| C3_BALANCE_INSIDE | ~12% |
| C2_DRIVE_INSIDE | ~12% |

Persistence 08:30→09:30 is modest (~28–37% same character). 10:30→11:30 higher for drive-outside (~62%).

## Limits

- Proxy VA ≠ Patrick trade-tape VA. Absolute levels vs Strategy 62 trade P1 are **not** comparable (continuous back-adjust vs contract prints).
- Catalog is for **idea validation / gating research**, not a trade.

## Artifacts

| Path | Role |
| --- | --- |
| `results/p1_1m_va_proxy.parquet` | Session proxy POC/VAH/VAL |
| `results/p1_1m_va_proxy_summary.json` | Build summary |
| `results/labels.parquet` | Session × clock labels |
| `results/frequency_by_clock.csv` | Character frequencies |
| `results/persistence.csv` | Persistence |
| `results/ENVIRONMENT_ATLAS_REPORT.md` | Report |
| `results/verdict.json` | Verdict |

## Next (not auto)

A sleeve charter may now **name** a thick character at a frozen clock — still needs its own prereg, risk unit, and R1–R6 check. Do not trade from this atlas alone.
