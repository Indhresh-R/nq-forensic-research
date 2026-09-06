# Conclusion

**Verdict: `ENGINE_OK`**

| Check | Result |
|-------|--------|
| Buy-and-hold identity (full + yearly) | **PASS** (0 failures) |
| SMA50/200 hand recompute | **PASS** |
| ^NDX cross calendar (±10d) | **94.4%** match (1 miss: 2012-12 death, 13d) |

Full-sample BH: 1795.00 → 29839.50 = **+28044.50** pts (hand match).  
SMA long-only (9 trades, next-open fills): **+23715.75** gross.

Interpretation: the local NQ load + daily aggregation + simple ledger math are trustworthy.
Failed research strategies are not explained by a broken buy/sell P&L engine.
