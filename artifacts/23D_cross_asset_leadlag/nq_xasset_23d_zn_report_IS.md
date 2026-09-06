# Hypothesis 23D-ZN — Overnight ZN/NQ RS under Strategy-12 HIGH (IS only)

## Pre-registration (before look)

- Grid: **24** cells
- ZB: **UNAVAILABLE** (duplicate ZN dumps ≠ ZB)
- Hard stop: 0 strong OR ES/23A-like all-clock negative incremental → close family 23

- Panel rows: **13,585**
- Soft / strong: **2** / **0**
- Tag: **`IS_HARD_STOP_FAMILY_23`**
- Hard stop fired: **YES**

## Three-way H=30

### `zn_follow`

| T+ | ALL+sig | HIGH-long | HIGH+sig | vs ALL | vs HIGH-long | n |
|----|---------|-----------|----------|--------|--------------|---|
| 15 | 49.0% | 51.1% | 50.4% | +1.4pp | -0.7pp | 750 |
| 30 | 48.3% | 53.5% | 48.9% | +0.6pp | -4.6pp | 740 |
| 60 | 48.9% | 53.4% | 46.1% | -2.8pp | -7.2pp | 746 |
| 90 | 48.6% | 55.5% | 49.1% | +0.5pp | -6.5pp | 742 |

### `zn_fade`

| T+ | ALL+sig | HIGH-long | HIGH+sig | vs ALL | vs HIGH-long | n |
|----|---------|-----------|----------|--------|--------------|---|
| 15 | 50.2% | 51.1% | 48.3% | -2.0pp | -2.8pp | 750 |
| 30 | 50.4% | 53.5% | 49.7% | -0.7pp | -3.8pp | 740 |
| 60 | 49.9% | 53.4% | 52.5% | +2.7pp | -0.8pp | 746 |
| 90 | 50.1% | 55.5% | 49.9% | -0.2pp | -5.7pp | 742 |

## Candidates

| Tier | Signal | T+ | H | HIGH+sig | vs ALL | vs HIGH-long | n |
|------|--------|----|---|----------|--------|--------------|---|
| soft | zn_follow | 30 | 15 | 51.4% | +1.1pp | +0.1pp | 740 |
| soft | zn_fade | 60 | 30 | 52.5% | +2.7pp | -0.8pp | 746 |

## Family stop reading

Hard stop **FIRED**. Close Strategy 23 family. Do not open VIX/skew/order-flow without a new argument. ZB remaining absent is a data gap — **not** a rescue path after this ZN kill. Next: HOW (size on Strategy 12 WHEN) or stop.
