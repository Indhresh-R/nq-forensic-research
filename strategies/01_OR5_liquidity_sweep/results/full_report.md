# Results — OR5 Liquidity Sweep Fade

**Verdict: `D` / FAILED (execution artifact)** — headline edge is not executable under causal fills.

Canonical: `artifacts/01_OR5_liquidity_sweep/edge_report.json`, `exit_forensic_report.json`, `gap_through_forensic_report.json`, `target_inset_sensitivity.json`

## Headline vs causal truth

| Book | n | WR | PF | Exp | Notes |
|------|--:|---:|---:|-----:|-------|
| next_open ORB_VWAP (headline) | 3828 | 47.62% | 2.07 | $37.60 | contaminated through-stop fills |
| close-fill same | 3828 | 47.1% | 2.06 | $37.43 | same pathology |
| OOS ORB-gate (contaminated) | 280 | 64.29% | **6.17** | $181.83 | 2026 live ORB n=97 WR=67% PF=7.41 |
| **Reject-through OOS ORB (stress)** | — | — | **0.80** | **−$17.56** | through-stop = 59.6% trades / **99.6%** of PnL |
| Clip-through OOS ORB | — | — | 1.00 | −$0.12 | kills edge |
| Reject 2026 ORB | — | — | **0.18** | — | collapses |

Through-stop share OOS ORB: **59.6%** of trades carry **$50,697 / $50,913** of PnL.

## Subperiod PF (ORB_VWAP)

| Era | PF |
|-----|---:|
| 2010–14 | 0.91 |
| 2015–18 | 1.02 |
| 2019–21 | 1.73 |
| 2022–24 | 2.30 |
| 2025–26 | 2.96 (n=769, WR=53.58%) |

Slip +1pt PF → **1.82**. Years profitable (close ORB_VWAP): **11/17**.

## Gap-through (parked)

PRIMARY OOS: n=613, WR=49.1%, PF=**0.75**, exp=−11.43, PnL=−$7004. RAW OOS PF=0.81. Grid: **0/34** cells with IS&Val PF≥1.2.

## Standardized split table (contaminated headline OOS ORB)

| Metric | IS | Validation | OOS | 2025 | 2026 |
|--------|---:|----------:|----:|-----:|-----:|
| Contaminated PF (ORB gate) | mixed early | rising | **6.17** | high | **7.41** (n=97) |
| Reject-through PF | — | — | **0.80** | — | **0.18** |

**Kill number:** reject-through drops OOS ORB PF **6.17 → 0.80**.
