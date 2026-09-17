# Internet-Sourced Price Action Top-5 Screen

**Verdict: all five patterns rejected under the frozen cross-market, chronological, cost-aware screen.**

## Selection and scope

The patterns—pin bar, inside-bar breakout, body engulfing, inside fake-out, and three-bar reversal—were selected because they are widely documented price-action/candlestick formations, not because online sources establish profitability. They were run on 5m RTH NQ and ES from 2010–2026 with causal next-1m entry, a fixed 60m exit, and 1.0/0.5 NQ/ES round-trip costs.

## Result

No pattern and side has positive net expectancy in NQ and ES across IS, Validation, and OOS. The OOS-positive cells are not candidates: they conflict with earlier splits and/or ES.

| Pattern / side | Why it fails |
| --- | --- |
| Pin bar long | NQ net -0.16 / -1.16 / -2.17 (IS/Val/OOS); ES IS -0.65. |
| Pin bar short | Negative in every NQ split; ES OOS -3.90. |
| Inside-bar breakout long | Negative in all ES splits and all NQ splits. |
| Inside-bar breakout short | Net negative in every split/market (nearest: ES OOS -0.04; NQ OOS -0.08). |
| Engulfing long | OOS NQ/ES positive (+0.27/+0.41), but NQ IS/Val -0.98/-1.67 and ES IS -0.53. |
| Engulfing short | Negative in all ES splits and NQ IS/OOS. |
| Inside fake-out long | NQ OOS +5.83, but NQ Validation -2.34 and ES IS/OOS -0.13/-0.15. |
| Inside fake-out short | Negative in every NQ/ES OOS cell; ES Validation -1.80. |
| Three-bar reversal long | NQ OOS +9.25 and ES OOS +0.31, but NQ IS/Val -1.41/-0.03 and ES IS/Val -0.51/-0.66. |
| Three-bar reversal short | NQ OOS +2.08, but NQ IS/Val -2.02/-0.65 and ES IS/OOS -0.53/-1.99. |

## Reading

The large OOS NQ cells are post-hoc temptations, not results to promote. Each conflicts with a frozen earlier split, and the same pattern fails to replicate on ES. This screen therefore adds no executable price-action pattern and does not justify entry/stop/target optimization.

## Sources used for pattern selection

- CME Group: technical charts/patterns describe candlestick information, reversals, and continuation patterns.
- IG: price-action overview identifies pin bars, inside bars, and fake-outs; its engulfing guide describes the two-bar body pattern.
- Three-bar reversal was included as a common three-candle price-action formation and codified mechanically before testing.

## Audit files

- `trades.csv` — every causal pattern execution.
- `summary.csv` — market × pattern × side × split metrics.
- `research/price_action_top5/PREREGISTRATION.md` — frozen rules.
