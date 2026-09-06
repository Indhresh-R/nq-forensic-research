# Hypothesis 23D — Overnight ES/NQ RS under Strategy-12 HIGH (IS only)

## Pre-registered grid (before scan)

- Cells: **24** = NY_AM × 4 clocks × 3 H × 2 signals
- Expected false strong @~5%: **~1.2**
- ZN/ZB: **UNAVAILABLE** (not tested)
- Primary metric: HIGH+signal vs **HIGH-long** (incremental)

## Freeze

- Panel rows: **13,577**
- Soft / strong: **2** / **0**
- Provisional IS tag: **`IS_SOFT_ONLY`**

## Three-way H=30 (every clock)

### `es_follow`

| T+ | ALL+sig | HIGH-long | HIGH+sig | vs ALL | vs HIGH-long | n |
|----|---------|-----------|----------|--------|--------------|---|
| 15 | 49.5% | 51.0% | 50.2% | +0.7pp | -0.8pp | 749 |
| 30 | 49.5% | 53.4% | 48.9% | -0.6pp | -4.6pp | 741 |
| 60 | 50.5% | 53.5% | 49.5% | -1.0pp | -4.0pp | 746 |
| 90 | 48.1% | 55.5% | 50.1% | +2.0pp | -5.4pp | 742 |

### `es_fade`

| T+ | ALL+sig | HIGH-long | HIGH+sig | vs ALL | vs HIGH-long | n |
|----|---------|-----------|----------|--------|--------------|---|
| 15 | 49.7% | 51.0% | 48.5% | -1.3pp | -2.5pp | 749 |
| 30 | 49.2% | 53.4% | 49.8% | +0.6pp | -3.6pp | 741 |
| 60 | 48.3% | 53.5% | 49.3% | +1.0pp | -4.2pp | 746 |
| 90 | 50.5% | 55.5% | 48.8% | -1.7pp | -6.7pp | 742 |

## IS candidates

| Tier | Signal | T+ | H | HIGH+sig | vs ALL | vs HIGH-long | n |
|------|--------|----|---|----------|--------|--------------|---|
| soft | es_fade | 30 | 60 | 49.8% | +0.6pp | -2.2pp | 741 |
| soft | es_fade | 30 | 30 | 49.8% | +0.6pp | -3.6pp | 741 |

## Hostile IS reading (final)

Provisional tag was `IS_SOFT_ONLY`; **closed as C** without Val/OOS — cheapest kill.
Strong **0**; incremental vs HIGH-long negative on every H30 clock. Soft leftovers
ignored (negative incremental).

**Scope:** this kill is **23D-ES only**. ZN/ZB remain **UNTESTED**.
