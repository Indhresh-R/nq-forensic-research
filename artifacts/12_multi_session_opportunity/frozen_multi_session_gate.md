# Frozen Multi-Session Activity Regime (Strategy 12)

**Status: RESEARCH FINDING, NOT TRADEABLE — family 12–14 CLOSED**

```text
Strategy 12 — Multi-Session Activity Regime
Status: RESEARCH FINDING, NOT TRADEABLE

Phase A:
Activity expansion confirmed across all four sessions
(Asia / London / NY AM / NY PM). Strong IS / Val / OOS
HIGH−LOW discrimination (headline H30 quiet→vol_high
~+30 to +55pp).

Phase B:
Direction (13): FAILED — 0/16 promising cells
Residual economics (14): FAILED — LOW covers break-even
at same ~100% rate as HIGH (cover lift +0.0pp OOS)

Conclusion:
The quiet → volatility expansion regime predicts activity,
but does not provide sufficient directional or selective
economic information to overcome the unconditional baseline.

Final verdict: NO TRADE
```

## Preserve as context / regime variable

Keep the IS-frozen session×offset `rng_psr` terciles and session clock.
Do **not** retune them against PnL.

Allowed future use: condition *other* hypotheses that have an explicit
causal story for why QUIET vs VOL_EXPANSION should change the conditional
return distribution.

Forbidden: mining follow/fade, stop/target grids, or residual overlays on
this classifier to rescue Strategies 13/14.

## Artifacts

| File | Role |
|------|------|
| `nq_multi_sess_opp_thresholds_IS.json` | Frozen IS terciles |
| `nq_multi_sess_opp_report.md` | Phase A |
| `../13_multi_session_direction/nq_multi_sess_dir_report.md` | Phase B direction kill |
| `../14_multi_session_residual_econ/nq_multi_sess_resid_report.md` | Phase B econ kill |
