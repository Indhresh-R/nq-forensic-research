# Results — AM Trades (Manipulation / Continuation)

**Verdict: `C`**

Canonical: `artifacts/02_AM_Trades/am_trades_forensic_report.json`, `am_trades_definitions.md`, `am_trades_nq_vs_es_compare.json`

## Core book (NQ)

| Split | n | WR | PF | E (pts) | PnL | Monthly+ |
|-------|--:|---:|---:|--------:|----:|---------:|
| **IS** | **730** | **34.0%** | **0.894** | **−1.42** | −1036 | 36.5% |
| Validation | 269 | 39.4% | 1.138 | +4.33 | +1165 | 57.6% |
| **OOS** | **148** | **36.5%** | **1.015** | +0.61 | +90 | 47.4% |
| ALL | 1147 | 35.6% | 1.009 | +0.19 | +219 | — |

OOS year break: **2025 PF=1.16 vs 2026 PF=0.85**.

## Context counts

Bias days: none 1906 / bull 1088 / bear 622 (of 3616). Profiles A 129 / B 423 / C 680 / D 2384.

## OOS slices

| Slice | n | WR | PF | E |
|-------|--:|---:|---:|--:|
| 09:30 opposed | 79 | 49.4% | **2.06** | +25.8 |
| 09:30 aligned | 68 | 22.1% | **0.51** | −28.5 |
| SMT+core | 11 | 27.3% | **0.78** | −5.98 |

## ES twin

Same **C**. ES IS n=326 WR=32.8% PF=**0.786** E=−1.20; ES OOS PF=**0.894**.

**Kill number:** IS PF **0.894** / E **−1.42** on n=730 (robustness grid skipped).
