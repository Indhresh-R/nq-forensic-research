# Rules: Strategy 36 Unconditional NQ Long Bias

## Causal & Execution Rules
1. **No Retrospective Selection**: Entries occur strictly at predefined timestamps or regular intervals without indicators, price patterns, or filters.
2. **Symmetric Execution**: For every entry opportunity, the Long and Short arms are subjected to the identical clock, identical holding period, and identical exit rules.
3. **Execution Timestamp**: Entry at the open of minute bar $T+1$.
4. **Collision Policy**: For stop/target evaluations, same-bar touches are resolved as STOP FIRST.
5. **Frozen Chronological Splits**:
   - In-Sample (IS): 2010–2021
   - Validation: 2022–2024
   - Out-of-Sample (OOS): 2025–2026 (split 2025 and 2026)
6. **Transaction Costs**:
   - Baseline: 1.0 NQ index point round-trip ($20.00 / contract).
   - Sweeps: 0.0, 0.5, 1.0, 1.5, 2.0 points.
