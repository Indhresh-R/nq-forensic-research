# Strategy 44: MBO Microstructure & Order Flow Information

## Objective
Forensic investigation into whether CME Globex Level 3 (Market by Order - MBO) microstructure information possesses forward predictive power over subsequent continuous NQ futures price movements.

This track is decoupled from prior OHLC bar-based strategies. It tests whether granular order book dynamics contain **measurable, incremental information** before any execution or trading logic is formulated.

---

## Architecture & Separation of Concerns

```text
d:\NQ-2\
│
├── common/
│   └── order_book.py              ← FROZEN ENGINE (Read-Only Infrastructure)
│
├── data/
│   ├── mbo_full_state_50/         ← 50 Sessions (00:00 - 16:00 UTC)
│   └── trades_24h_6m/             ← 126 Sessions (00:00 - 23:59:59 UTC)
│
└── strategies/
    └── 44_mbo_orderflow/
        ├── README.md
        ├── PREREGISTRATION.md
        ├── methodology.md
        │
        ├── hypotheses/
        │   ├── H01_depth_imbalance/
        │   ├── H02_aggressive_delta/
        │   ├── H03_absorption/
        │   └── H04_queue_dynamics/
        │
        ├── code/
        │   ├── replay_mbo.py
        │   ├── extract_features.py
        │   └── information_tests.py
        │
        ├── results/
        └── reports/
```

---

## The Four Independent Hypotheses

| ID | Name | Core Research Question |
| :--- | :--- | :--- |
| **H01** | **Depth Imbalance** | Does the ratio of resting bid vs. ask depth at the top of the book predict subsequent mid-price displacement? |
| **H02** | **Aggressive Flow** | Does short-horizon cumulative trade delta (buyer-initiated vs. seller-initiated volume) predict forward price continuation? |
| **H03** | **Absorption** | When large aggressive trade volume impacts a price level but fails to displace the inside market, does this absorption signal an impending mean-reversion? |
| **H04** | **Queue Dynamics** | Do rapid cancellation-to-addition ratios and top-queue replenishment rates contain forward directional information? |

---

## Research Workflow Gate

```text
Raw MBO (.dbn.zst)
   ↓
Frozen L3 Reconstruction (common/order_book.py)
   ↓
Decision Timestamp T (Causal Cutoff)
   ↓
Feature Extraction F(T)
   ↓
Forward Return ΔP(T + τ) for τ ∈ {1s, 5s, 15s, 60s, 300s}
   ↓
Information Test Gate (Spearman IC, p-value, Quintile Monotonicity)
   ↓
Does True Information Exist in In-Sample?
   ├── NO  → KILL Hypothesis Immediately (No Backtest)
   └── YES → Advance to Validation & Design Execution Model
```
