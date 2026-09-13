# Literature map — Strategy 27

**Rule:** map published results → required data → affordable proxy → testable claim **before** writing experiment code.

This is not a bibliography dump. Each entry answers:

1. What phenomenon was claimed?
2. What data did they need?
3. Can we reproduce anything with local 1m OHLCV (+ later cross-asset bars)?
4. What would falsify a “cheap data is enough” story?

---

## Core thesis (ours)

> When genuinely informed or urgent order flow enters ES/NQ, the market is temporarily more predictable before that information is fully incorporated into price.

We test **information content**, not a trading rule.

---

## Tier A — Directly motivates Strategy 27

### A1. Locke & Onayev (2007) — order flow → S&P futures price

- **Paper:** Peter Locke & Zhan Onayev, “Order flow, dealer profitability, and price formation,” *Journal of Financial Economics* 85(3), 857–887.  
  https://doi.org/10.1016/j.jfineco.2006.05.010  
  (ScienceDirect abs: https://www.sciencedirect.com/science/article/abs/pii/S0304405X07000633)
- **Claim:** Strong short-run relation between customer order flow and S&P 500 futures price; long-run impact small/negative (hedging slippage story); **state-dependent** (volume / floor-trader income regimes).
- **Data they used:** CFTC transaction records with **trade direction** (buy/sell), floor vs customer, ~1998–2001. Not 1m OHLCV.
- **Affordable proxy?** Partial. We have minute volume + returns, **not** true signed customer flow. Closest cheap proxies: signed volume from tick-rule / close-to-close sign × volume; volume shocks; return-per-volume; volume acceleration.
- **Reproduce-able claim with our data:**  
  *Does abnormal unsigned volume / signed-volume proxy add OOS ΔR² for next 1–30m ES returns after vol+TOD+recent return?*  
  Failure here does **not** falsify Locke–Onayev (they had richer flow). It falsifies “1m OHLCV is enough for this edge.”

### A2. Kurov & Lasser (2004) — E-mini price discovery / trader informativeness

- **Paper:** Alexander Kurov & Dennis J. Lasser, “Price Dynamics in the Regular and E-Mini Futures Markets,” *JFQA* 39(2), 365–384.  
  https://doi.org/10.1017/S0022109000003112
- **Claim:** Price discovery initiates in **E-mini**; trades by exchange locals more informative than off-exchange; locals appear informed around large floor trades.
- **Data:** Transactions with **trader-type IDs** (locals vs customers). We do not have this.
- **Affordable proxy?** Leadership of electronic futures is already “baked in” for modern ES/NQ. Useful mainly as mechanism justification: **futures tape is where information shows up first**.
- **Reproduce-able claim:** Prefer ES as primary panel; treat “smart money labels” as unavailable — do not invent ICT-style classifications.

### A3. Hasbrouck (2003) — E-mini dominates index price discovery

- **Paper:** Joel Hasbrouck, “Intraday Price Formation in U.S. Equity Index Markets,” *Journal of Finance* 58(6), 2375–2400.  
  https://doi.org/10.1046/j.1540-6261.2003.00609.x
- **Claim:** For S&P 500 and Nasdaq-100, most price discovery occurs in the **E-mini** vs floor futures / ETFs (second-scale VECM / information shares).
- **Data:** High-frequency quotes/trades across venues.
- **Affordable proxy?** Minute-level ES↔NQ and (later) QQQ/VIX lead-lag are coarser but testable. Supports Strategy 27 priority + Strategy 28 design.
- **Reproduce-able claim:** Cross-instrument lead/lag after own-market controls (Strategy 28 if 27 fails).

### A4. Fishe, Haynes & Onur (2022) — E-mini resiliency / impatient flow

- **Paper:** Raymond P. H. Fishe, Richard W. Haynes & Esen Onur, “Resiliency in the E-mini futures market,” *Journal of Futures Markets* 42, 5–23.  
  https://doi.org/10.1002/fut.22259
- **Claim:** Limit-order replenishment vs market-order re-entry differ; delays depend on market state; some traders delay liquidity provision in active markets (informed-trading avoidance).
- **Data:** Order-book / participant-level CFTC-style data. **Level 3.**
- **Affordable proxy?** Weak with 1m bars. Volume bursts + range expansion are crude stand-ins for “aggressive flow into thin liquidity.”
- **Later mechanism (only if Phase 2 shows residual info):**  
  *Aggressive flow + disappearing liquidity → temporary price impact.*  
  Do **not** jump to L3 until cheap proxies fail for a clear reason (missing side/aggressor, not missing a pattern).

---

## Tier B — Related phenomena (queue, not Strategy 27 Phase 1)

### B1. Lim, Chen & Yap (2019) — intraday risk-neutral skewness

- **Paper:** Kian Guan Lim, Ying Chen & Nelson Yap, “Intraday information from S&P 500 Index futures options,” *Journal of Financial Markets* 42, 29–55.  
  https://doi.org/10.1016/j.finmar.2018.10.001  
  Open PDF via SMU InK: https://ink.library.smu.edu.sg/lkcsb_research/6403/
- **Claim:** 10-minute-ahead **risk-neutral skewness** from E-mini futures options had trading information net of costs; RN **volatility** did not.
- **Data:** Intraday futures-options transactions (~10m aggregation).
- **Relation to 27:** Separate branch — options *information extraction*, not futures order flow. Interesting **after** 27/28, or as a parallel literature track if we obtain affordable options prints.
- **Do not fold into Phase 1 of Strategy 27.**

### B2. Cont / OFI line (context)

- Classic equity LOB work (e.g. Cont, Kukanov, Stoikov on order-flow imbalance) shows OFI predicts short-horizon mid moves — typically **with book/trade imbalance**, not unsigned minute volume.
- Implication: if our unsigned-volume panel fails, the literature still expects a possible L2/trade-signed edge. That is a **data upgrade decision**, not a reason to invent chart patterns.

### B3. Recent HF flow–return VARs on ES

- e.g. work estimating structural return–flow VARs on E-mini at ~1-second resolution: contemporaneous impact strong; impulse responses often die within ~1s under some identifications.
- Implication for us: any **minute-bar** predictability is already a stretched version of a very short-lived microstructure effect. Hostile OOS must be strict; contemporaneous leakage is the main contamination risk.

---

## What the literature does **not** license

| Temptation | Why blocked |
|------------|-------------|
| “Buy when volume spikes” rule search | Optimization before information test |
| ICT / smart-money narrative labels | No trader IDs; Kurov–Lasser advantage is not reconstructible from OHLCV |
| Another gamma/GEX threshold | Already tested (25/26); wrong distance from mechanism |
| Claiming we tested “order flow” when we only have unsigned volume | Naming discipline — call proxies what they are |

---

## Translation table (literature → our Phase 1 candidates)

| Construct in papers | Ideal data | Cheap local proxy (if Phase 0 allows) |
|---------------------|------------|----------------------------------------|
| Signed customer order flow | Aggressor / customer buy–sell | Sign(Δclose)×volume; optional tick-rule on 1m |
| Volume as information state | Trade volume | z-scored volume vs TOD, volume acceleration |
| Price impact | Δp / flow | return per unit volume; range per unit volume |
| Abnormal flow bursts | Clustered aggressive trades | consecutive high-volume minutes; volume×RV |
| Cross-market discovery | Multi-venue HF | ES↔NQ relative return / lead-lag residuals |
| Liquidity resiliency | LOB replenishment | **Not in Phase 1** (needs L2+) |

---

## Decision rule after literature

| Outcome of cheap-data tests | Next step |
|-----------------------------|-----------|
| Residual OOS info survives hostile placebos | Mechanism audit (still no rules); then consider whether L2 would strengthen |
| No incremental info | **Do not** invent Strategy 28 patterns — open **Strategy 28 cross-market lead/lag** |
| Info only contemporaneous / dies at 1–2m | Treat as microstructure noise at our horizon; discard trading search |
| Failure clearly due to missing signed flow | Document data blocker; decide on affordable tick/L2 purchase before any new family |

---

## Reading order (before any coding)

1. Locke & Onayev (2007) abstract + intro (state dependence)
2. Hasbrouck (2003) abstract + E-mini leadership result
3. Kurov & Lasser (2004) abstract (trader-type — what we **cannot** replicate)
4. Fishe et al. (2022) abstract (liquidity branch — later)
5. Lim et al. (2019) abstract only (queue for options-info branch)

Then close Phase 0 data audit (`DATA_NOTES.md`) and freeze `rules.md`.
