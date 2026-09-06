# Conclusion — 23D-ES (overnight ES/NQ relative strength)

**Verdict: `C` CLOSED** (IS-only kill — Val/OOS not run)

## Scope of this verdict (read carefully)

This closes **only the ES leg** of the original 23D cross-asset lead-lag dossier.

| Leg | Status |
|-----|--------|
| **23D-ES** (overnight ES−NQ RS under Strategy-12 HIGH) | **Tested → C** |
| **23D-bonds** (ZN / ZB overnight RS vs NQ) | **UNTESTED** — local continuous parquet absent; **not** a null, **not** closed |

Do **not** read this file as “bonds were tested and failed.”

## Methodology (brief)

- Overnight window: prior RTH close (≤16:00 ET) → NY open (09:30)
- Signals: `es_follow` / `es_fade` (sign of ES overnight − NQ overnight)
- Grid pre-registered at **24** cells before scan; three-way from the start
- HIGH = Strategy-12 frozen `rng_psr` p66; next-bar open fills

## IS result (decisive)

- Strong: **0** / Soft: **2** (E-or-tiny leftovers with **negative** incremental win)
- Every NY_AM H=30 clock: HIGH+signal **loses** to HIGH-long (about −0.8pp to −6.7pp)

## Failure mode

No clock shows positive incremental lift of overnight ES−NQ relative strength over
HIGH-long at IS. The hypothesis is rejected at the earliest, cheapest checkpoint —
before Val. Cross-asset *equity* overnight RS does not add independent sign on top
of the already-validated Strategy 12 activity gate in this frozen design.

## What remains open

**23D-bonds (ZN/ZB):** still a live, cheap candidate *if* continuous 1m (or daily
overnight) data is sourced from the same vendor as ES/NQ. Opening it requires a
new pre-registered grid — not a rescue of 23D-ES.
