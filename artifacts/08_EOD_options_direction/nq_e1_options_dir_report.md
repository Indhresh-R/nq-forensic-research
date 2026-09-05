# E1 — Prior-day EOD Options → Next-day Intraday NQ Direction (NO HIGH)

**Classification: `C`** — No intraday directional asymmetry from prior-day EOD GEX / PC-imbalance / put-OI-z states (follow and fade both fail hostile gates).

Kill EOD-options-for-direction family: **True**. Tests **intraday direction**, not next-day range/vol. No HIGH.

Frozen: `|gex|≥IS p66` thr=5.515e+10; `|pc_imb|≥IS p80` thr=0.4316; `|put_z|≥1.0`.

Options last date: `2025-12-15`; 2026 sessions with any signal: 150.

Strong: 0 · Soft: 0 · Multi-clock strong: 0

## Mechanism IS summary (median across clocks/horizons)

| Mechanism | med n | win | Δ50 | mean z | MFE>MAE | P(+1R≺) |
|-----------|-------|-----|-----|--------|---------|---------|
| `putz_fade` | 268 | 47.2% | -2.8pp | -0.032 | 48.0% | 50.2% |
| `pc_fade` | 458 | 47.8% | -2.2pp | +0.036 | 49.5% | 49.8% |
| `putz_follow` | 268 | 51.1% | +1.1pp | +0.032 | 50.2% | 49.8% |
| `gex_fade` | 780 | 49.0% | -1.0pp | +0.002 | 49.2% | 49.0% |
| `pc_follow` | 458 | 50.5% | +0.5pp | -0.036 | 49.4% | 50.2% |
| `gex_follow` | 780 | 49.7% | -0.3pp | -0.002 | 49.9% | 51.0% |

## Surviving cells

None.

## Stability

n/a

## Final: **C**

**Kill entire EOD-options-for-direction family.**
Do not rescue with more options feature engineering.
Next: **scheduled information events**.
HIGH remains frozen for later timing-only tests.
