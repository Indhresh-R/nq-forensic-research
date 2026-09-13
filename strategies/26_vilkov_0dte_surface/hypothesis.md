# Hypothesis (ours — not Vilkov’s)

The **point-in-time** 0DTE SPXW option surface (interpolated mids/Greeks/flow/OI-gamma proxies in the Vilkov panels) changes the conditional distribution of subsequent **ES/SPX** and **NQ** short-horizon returns and realized volatility, beyond ordinary price, volatility, and time-of-day state.

## What we will test (after schema audit)

1. Gamma concentration vs spot (ATM mass, distance of peak gamma, local gamma slope)
2. GEX-style signed/absolute OI-weighted gamma and balance (`g^{OI,n}`, `g^{OI,a}`, `B^Γ`, `R^Γ`) where columns exist and are PIT
3. Flow pressure (`f^Γ`, `f^Δ`, volume×gamma×S²)
4. Forward ES returns/RV at +1/+5/+10/+15/+30/+60 minutes **from the decision timestamp**
5. Transmission: same state → NQ returns/RV
6. Incremental information vs price/vol/TOD baseline
7. Hostile placebos (time-shift, shuffle, wrong-day)

## Explicit non-goals

- Do **not** reproduce Vilkov strategy tables or trust published net Sharpes (Aug 2026 cost bug).
- Do **not** treat interpolated moneyness grid as the raw Cboe tape.
- Do **not** use future moments / same-day settlement PNL as predictors.
