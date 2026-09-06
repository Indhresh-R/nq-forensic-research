# Causal Rules

## Non-negotiable

1. **Signal information set:** only bars / fields with timestamp `<= T`.
2. **Entry / outcome start:** next bar **open** after T (unless a dossier freezes a different causal rule and documents it).
3. **No lookahead:** no future highs/lows, no same-day EOD used at 09:30, no revised prints as if known live.
4. **Ambiguity:** same-bar both-side touches are not counted as clean wins (NaN / skip / stop-first — document which).
5. **Frozen constants:** IS-only thresholds; never refit on Val/OOS for promotion.

## HIGH gate (when used)

- `vol_expansion_high` is **opportunity / activity timing**, not direction.
- Thresholds in `artifacts/ny_open_opp_timing_thresholds_IS.json` are **frozen**.
- Do not optimize HIGH against directional PnL.

## External data lag

- EOD options (~16:15 ET) may only condition **later** sessions (`opt_date < session_date`).
- CFTC TFF / COT: `report_date` is the **Tuesday** snapshot; public release is the
  following **Friday ~15:30 ET**. Usable only from the **next trading session after
  that Friday release** — never Tuesday–Friday of the snapshot week (see Strategy 23A).
