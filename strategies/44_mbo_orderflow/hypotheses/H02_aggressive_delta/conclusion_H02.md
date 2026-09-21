# Hypothesis H02: Aggressive Order Flow Delta & Microstructure Dynamics — Forensic Verdict

## Formal Status: RETRACTED

The promotion below was computed with trades from `[t, t+1)` stored on the row at `t`. That assignment is invalid. Validation `2026-08-13` → `2026-08-28` was not run.

The replay now stores events in `(t-1s, t]` on the snapshot at `t`. The same frozen rule, rebuilt on all 26 sessions, does not survive:

- Clock check: 0 rows with a flow event after the snapshot.
- CVD 1s daily rank IC: **−0.0062**.
- Full-sample 10/90 tails, 15s cooldown, 5s taker, −0.25: **n = 11,514**, gross **−0.023**, net **−1.200**, **0/26** days, total **−13,815.8** points.

H02-A, H02-B, and the L3 interaction are not promoted. H02-C and H02-D were killed on the contaminated clock and are not confirmed either. The tables underneath are the retracted run, kept as a record of the bug.

---

### 1. In-Sample Forensic Diagnostic Surface (26 Sessions / 234,000 Observations)

#### Table 1: H02-A Generic CVD Unconditional Performance
| Feature | Horizon ($\tau$) | Mean Rank IC | Std IC | $t$-Statistic | BH-Adjusted $p$-Value | Monotonic? | $Q_1$ Return | $Q_5$ Return | $Q_5 - Q_1$ Spread | Gate Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **$CVD_{1s}$** | **1s** | **+0.5584** | 0.0324 | 87.82 | $0.00 \times 10^{0}$ | **True** | -2.087 pts | +2.088 pts | **+4.175 pts** | **PASS** |
| **$CVD_{1s}$** | **5s** | **+0.2459** | 0.0151 | 82.98 | $0.00 \times 10^{0}$ | **True** | -2.097 pts | +2.069 pts | **+4.166 pts** | **PASS** |
| **$CVD_{1s}$** | **15s** | **+0.1403** | 0.0147 | 48.73 | $0.00 \times 10^{0}$ | **True** | -2.076 pts | +2.017 pts | **+4.093 pts** | **PASS** |
| **$CVD_{1s}$** | **60s** | **+0.0694** | 0.0105 | 33.80 | $0.00 \times 10^{0}$ | **True** | -2.022 pts | +1.781 pts | **+3.804 pts** | **PASS** |
| **$CVD_{1s}$** | **300s** | **+0.0298** | 0.0089 | 17.12 | $5.86 \times 10^{-15}$ | **True** | -2.105 pts | +1.452 pts | **+3.557 pts** | **PASS** |
| **$CVD_{5s}$** | **1s** | **+0.1993** | 0.0172 | 58.96 | $0.00 \times 10^{0}$ | **True** | -0.818 pts | +0.803 pts | **+1.621 pts** | **PASS** |
| **$CVD_{5s}$** | **5s** | **+0.0844** | 0.0210 | 20.46 | $0.00 \times 10^{0}$ | **True** | -0.760 pts | +0.778 pts | **+1.538 pts** | **PASS** |
| **$CVD_{5s}$** | **15s** | **+0.0515** | 0.0245 | 10.72 | $1.56 \times 10^{-10}$ | **True** | -0.771 pts | +0.760 pts | **+1.530 pts** | **PASS** |
| **$CVD_{5s}$** | **60s** | **+0.0245** | 0.0211 | 5.93 | $5.98 \times 10^{-6}$ | **True** | -0.644 pts | +0.508 pts | **+1.152 pts** | **PASS** |
| **$CVD_{5s}$** | **300s** | **+0.0026** | 0.0214 | 0.61 | $0.574$ | True | -0.802 pts | -0.022 pts | +0.780 pts | **FAIL** |
| **$TCD_{1s}$** | **1s** | **+0.5741** | 0.0365 | 80.17 | $0.00 \times 10^{0}$ | **True** | -2.166 pts | +2.156 pts | **+4.322 pts** | **PASS** |
| **$TCD_{1s}$** | **5s** | **+0.2540** | 0.0172 | 75.46 | $0.00 \times 10^{0}$ | **True** | -2.186 pts | +2.135 pts | **+4.321 pts** | **PASS** |

---

#### Table 2: H02-B Range-Conditioned Incremental Information Tests
$$\text{Model A}: R_{t,\tau} \sim Loc_{15m}(t) \quad \text{vs.} \quad \text{Model B}: R_{t,\tau} \sim Loc_{15m}(t) + CVD_w(t)$$

| Feature | Horizon | Model A IC (Range) | Model B IC (Range + Flow) | Incremental $\Delta IC$ | $t$-Statistic | BH $p$-Value | Upper Extreme IC | Lower Extreme IC | Gate Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **$CVD_{5s}$** | **5s** | +0.0070 | +0.0869 | **+0.1109** | 18.31 | $5.33 \times 10^{-15}$ | +0.0989 | +0.0914 | **PASS** ($\Delta IC \ge 0.015$) |
| **$CVD_{5s}$** | **15s** | +0.0062 | +0.0566 | **+0.0959** | 9.68 | $1.83 \times 10^{-9}$ | +0.0627 | +0.0529 | **PASS** ($\Delta IC \ge 0.015$) |
| **$CVD_{5s}$** | **60s** | -0.0040 | +0.0218 | **+0.1065** | 5.18 | $2.36 \times 10^{-5}$ | +0.0367 | +0.0242 | **PASS** ($\Delta IC \ge 0.015$) |
| **$CVD_{15s}$** | **5s** | +0.0070 | +0.0511 | **+0.0771** | 12.89 | $6.06 \times 10^{-12}$ | +0.0662 | +0.0650 | **PASS** ($\Delta IC \ge 0.015$) |
| **$CVD_{15s}$** | **15s** | +0.0062 | +0.0349 | **+0.0829** | 7.45 | $1.67 \times 10^{-7}$ | +0.0509 | +0.0302 | **PASS** ($\Delta IC \ge 0.015$) |

---

#### Table 3: H02-C Price-Flow Divergence (De-duplicated Events, 30s Cooldown)
| Window | Horizon | Independent Events | Mean Reversal | $t$-Statistic | $p_{\text{raw}}$ | IC Excursion Alone ($dp$) | IC Divergence Full | Incremental $\Delta IC$ | Gate Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **15s** | **15s** | 1,998 | +1.116 pts | 4.99 | $6.41 \times 10^{-7}$ | 0.1138 | 0.1137 | **-0.0001** | **FAIL** ($\Delta IC < 0.015$) |
| **15s** | **60s** | 1,998 | +1.596 pts | 3.55 | $3.97 \times 10^{-4}$ | 0.0944 | 0.0862 | **-0.0082** | **FAIL** ($\Delta IC < 0.015$) |
| **60s** | **15s** | 2,092 | +1.219 pts | 5.38 | $8.43 \times 10^{-8}$ | 0.1161 | 0.1226 | **+0.0065** | **FAIL** ($\Delta IC < 0.015$) |
| **60s** | **60s** | 2,092 | +1.460 pts | 3.27 | $1.08 \times 10^{-3}$ | 0.0633 | 0.0674 | **+0.0041** | **FAIL** ($\Delta IC < 0.015$) |

---

#### Table 4: H02-D Passive Absorption (Trade-Only vs. L3 MBO Grounding)
| Window | Horizon | Independent Events | Mean Reversal Return | $t$-Statistic | BH $p$-Value | Reversal Direction? | Gate Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **5s** | **5s** | 266 | **-2.645 pts** | -3.35 | 0.0043 | **CONTINUATION (Opposite)** | **FAIL (REFUTED)** |
| **5s** | **15s** | 266 | **-2.922 pts** | -3.31 | 0.0043 | **CONTINUATION (Opposite)** | **FAIL (REFUTED)** |
| **5s** | **60s** | 266 | **-4.560 pts** | -2.98 | 0.0083 | **CONTINUATION (Opposite)** | **FAIL (REFUTED)** |
| **5s** | **300s** | 266 | **-5.860 pts** | -2.08 | 0.0389 | **CONTINUATION (Opposite)** | **FAIL (REFUTED)** |
| **15s** | **15s** | 59 | **-6.305 pts** | -2.38 | 0.0312 | **CONTINUATION (Opposite)** | **FAIL (REFUTED)** |
| **15s** | **60s** | 59 | **-11.011 pts** | -2.21 | 0.0359 | **CONTINUATION (Opposite)** | **FAIL (REFUTED)** |

---

#### Table 5: Execution Feasibility & Daily Stability (Taker Crossing Friction Model)
Evaluating $CVD_{1s}$ (15s event cooldown, 5s holding horizon, full taker spread paid on entry & exit $+ 0.25$ friction):

| Metric | Empirical In-Sample Value |
| :--- | :--- |
| **Total Independent Events (26 Sessions)** | **11,521** |
| **Average Events Per Day** | **443.1** |
| **Average Continuous Bid-Ask Spread** | **0.909 pts ($18.18)** |
| **Gross Mid-Price Alpha** | **+2.759 pts ($55.18)** |
| **Net Taker Return Per Trade (After All Friction)** | **+1.581 pts ($31.62 per contract)** |
| **Net Trade Win Rate** | **59.6%** |
| **Profitable Days** | **26 / 26 (100.0% Daily Win Rate)** |
| **Total Net In-Sample Profit (1 Contract)** | **+18,233.25 pts ($364,665.00)** |

---

### 2. Forensic Discovery: Trade Tape vs. Level 3 (MBO) Attribution

Does Level 3 MBO book reconstruction provide incremental explanatory power over aggressive trade prints alone?

$$\text{Model 1 (Trade Tape Only)}: R_{t, 5s} = \beta_0 + \beta_1 CVD_{5s}(t)$$
$$\text{Model 2 (Trade Tape + L3 Book)}: R_{t, 5s} = \beta_0 + \beta_1 CVD_{5s}(t) + \beta_2 OBI_1(t) + \beta_3 \text{NetAdds}_{5s}(t) + \beta_4 \text{NetCancels}_{5s}(t)$$

| Model Specification | Rank Information Coefficient (IC) | Explained Variance ($R^2$) | Incremental Gain ($\Delta IC$) |
| :--- | :--- | :--- | :--- |
| **Model 1: Trade-Only ($CVD_{5s}$)** | **0.0847** | 0.78% | Baseline |
| **Model 2: Trade + L3 MBO** | **0.2022** | **3.95%** | **+0.1175 (+138.7% IC boost)** |

#### OLS Betas in Full L3 Model:
- $OBI_1$ (Level 1 Depth Imbalance): **$+0.3123$** ($t \gg 10$)
- $\text{NetAdds}_{5s}$ (Limit Adds at Bid vs. Ask): **$+0.0127$** ($t \gg 10$)
- $\text{NetCancels}_{5s}$ (Limit Cancels at Ask vs. Bid): **$+0.0129$** ($t \gg 10$)

**Microstructure Takeaway:**
While H01 showed that resting depth *alone* has weak predictive power ($IC = 0.016$), when resting depth and queue replenishment are interacting with aggressive order flow ($CVD$), **L3 MBO data more than doubles the information content of the trade tape** (IC surges from 0.085 to 0.202, $R^2$ jumps by 5.1x).

---

### 3. Forensic Analysis & Key Conclusions

1. **Aggressive Delta Contains Massive Short-Horizon Information:**
   * Unlike passive depth (H01), aggressive market orders ($CVD_{1s}$ and $TCD_{1s}$) exert direct physical impact on quotes.
   * At 1 second, rank correlation is **+0.5584**, decaying to **+0.2459 at 5s**, **+0.1403 at 15s**, and **+0.0694 at 60s**. All Benjamini-Hochberg FDR $p$-values are $0.00$.
2. **Execution Feasibility Withstands Taker Friction:**
   * Because the gross move is $+2.76$ points ($55.18) and the average spread is $0.91$ points ($18.18), taker execution remains heavily net positive (**+1.58 points / $31.62 net per trade**).
   * Across all 26 audited In-Sample sessions, **every single session was net profitable**.
3. **The "Passive Absorption Reversal" Myth is Busted:**
   * In continuous double auction NQ futures, large aggressive volume with zero immediate price movement does **NOT** signal passive exhaustion or impending reversal.
   * The empirical return is **negative (-2.65 to -11.01 points)**, proving that aggressive flow consumes the resting iceberg and breaks out in the original direction.
4. **Divergence Fails Incremental Testing:**
   * While price-flow divergence appears profitable on raw inspection, the incremental information test proves that the reversion is driven entirely by the magnitude of the price excursion ($dp$), with CVD divergence adding zero marginal value ($\Delta IC \le 0$).

---

### 4. Next Action

The timestamp assignment is fixed and the frozen comparison has been rerun. It does not show a CVD edge. Do not change the rule to chase a result, and do not open the validation partition on this feature set. A full H02 information rerun on the corrected snapshots is still required before any sub-hypothesis is killed or promoted.
