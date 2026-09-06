# Conclusion — 17 session extreme trap

## Verdict

**`B→kill`** — first vulnerability-class test fails multi-clock / Val+OOS lift.
Do not retune W/thr. Strategy 12 untouched.

## Why (numbers)

Panel **25,201** (trap events only). Mix ~50/50 buyers vs sellers trapped.

| Session | H30 HIGH+trap IS | Lift IS | Lift Val | Lift OOS | HIGH+trap OOS |
|---------|------------------|---------|----------|----------|---------------|
| LONDON | 53.1% | +2.6pp | **−1.1pp** | +8.6pp | 62.8% |
| NY_PM | 56.1% | +2.6pp | +3.3pp | **−0.4pp** | 48.8% |
| NY_AM | 50.5% | +2.3pp | **−6.7pp** | +1.1pp | 49.4% |
| ASIA | 51.0% | +5.6pp | **−2.1pp** | +7.6pp | 63.4% |

Strong: **1** (Asia H120 single-clock). Soft: **3**. Multi-clock strong: **0**.

London/Asia OOS spikes are **not** Val-stable — classic illusion if read OOS-only.

## Interpretation

Tag-and-fail at session extremes is a real vulnerability *concept*, but this
frozen encoding does not deliver stable conditional lift inside Strategy-12 HIGH.

## What not to do next

- Do not retune W=15 / thr to chase London OOS 62%
- Do not reopen 16A/16B
- Next vulnerability hypothesis needs a **different** pre-event imbalance definition
