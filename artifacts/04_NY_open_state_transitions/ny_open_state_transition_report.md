# NQ NY Open — State Transition Discovery

**Prior hypothesis (level + confirmation → trade): STOPPED.** Clean failure; do not reopen with filters.

**This stage:** What information between 09:30–10:30 changes the odds of what happens next?
No entries. No stops. No targets. No optimization.

---

## Protocol

| Rule | Implementation |
|------|----------------|
| Decision clocks T | 09:35, 09:40, 09:45, 09:50, 10:00, 10:15, 10:30 |
| State at T | Only bars with `ny_min <= T` |
| Outcome | From **next bar open after T**; horizons 5/15/30m |
| No overlap | State window and forward window are disjoint |
| Thresholds | IS terciles only (open location fixed at 20/80, 10/90) |
| Splits | IS 2010–21 / Val 2022–24 / OOS 2025–26 |

States tested (behavioral, not mined): vol expansion, overnight compression→day expansion, strong directional move, path persistence, speed, open/price location vs overnight, path vs overnight activity, and simple intersections (`strong_and_persistent`, `fast_and_expanded`).

Panel: **25,200** rows · **3,601** days.

---

## Two tracks

1. **Directional persistence** — given direction at T, does forward continue? (vs 50%)
2. **Magnitude** — does P(large subsequent move) change vs same-TOD unconditional?

---

## Hostile finding on magnitude

Raw-point magnitude “survivors” (`wide_ON_quiet_open`, `compress_then_expand`) looked strong on **P(|fwd| ≥ 10 pts)**.

Under **ONR-normalized** P(|fwd|/ONR ≥ 0.05) they **flip or shrink**:

| State | Raw ΔP10 (IS) | ONR ΔP05 (IS) | Interpretation |
|-------|---------------|---------------|----------------|
| `wide_ON_quiet_open` T+10 h5 | +0.07 | **−0.09** | Condition selects wide overnight → 10pts is easy; artifact |
| `wide_ON_quiet_open` T+20 h15 | +0.10 | **−0.06** | Same |
| `compress_then_expand` T+15 h30 | −0.10 | **+0.03** | Condition selects tight overnight → 10pts is hard; artifact |

**Kill the raw-point magnitude track.** It does not answer “odds of a large *relative* move.”

---

## Directional results (clean)

No directional state cleared a **strong** bar (IS & OOS win ≥ 55% with |Δ| ≥ 5pp and sensible mean).

Closest survivors (gross, direction-aligned forwards):

| State | T | H | IS n | Rate | IS win | Val | OOS | IS mean pts | Notes |
|-------|---|---|------|------|--------|-----|-----|-------------|-------|
| `open_near_ONH` | +5m | 30 | 586 | 0.24 | 55.9% | 54.6% | 54.7% | +2.7 | 2025: 47% / 2026: 65% — year-unstable |
| `strong_and_persistent` | +10m | 15 | 658 | 0.27 | 53.2% | 58.0% | 59.6% | **−0.3** | Win>50% but **negative mean** (losers larger) |
| `price_near_ONH` | +10m | 15 | 610 | 0.25 | 55.0% | 51.8% | 56.8% | −0.3 | Same payoff problem on IS |
| `high_persistence` | +5m | 5 | 833 | 0.34 | 55.2% | **50.7%** | 54.6% | +1.3 | Val collapses to coin |

### 2025 vs 2026 (best directional candidates)

| State | 2025 n / win | 2026 n / win |
|-------|--------------|--------------|
| `open_near_ONH` +5→h30 | 55 / 47.3% | 40 / 65.0% |
| `strong_and_persistent` +10→h15 | 66 / 54.5% | 33 / 69.7% |
| `high_persistence` +5→h5 | 89 / 53.9% | 63 / 55.6% |

2026 looks better on small samples; that must **not** drive promotion.

---

## What actually changed the odds?

**Honest answer: almost nothing usable.**

- NY open is volatile and level interactions are common — already established.
- Conditional states at T shift directional odds by roughly **+3 to +6pp** in-sample at best.
- Those shifts either:
  - fail payoff asymmetry (more wins, larger losses), or
  - fail Validation, or
  - disagree between 2025 and 2026.
- Magnitude “edges” on fixed points were **selection artifacts** of overnight range size.

Unconditional same-TOD baseline remains ~**52%** directional / modest drift — matching the collapsed level-confirmation result.

---

## Stage verdict

**`B_weak_state_transition` / effectively kill for trading**

We found *statistical* same-sign survivors under frozen terciles, but **no information variable that materially and stably reprices the forward distribution** in an economically meaningful way.

Closest story worth remembering (not trading):

> After ~10 minutes, a **strong ONR-normalized move that has also been path-persistent** shows slightly elevated continuation frequency in Val/OOS — but IS expectancy in points is flat/negative. That is **not** “what to trade.” It is barely “the market sometimes trends for a bit.”

---

## Explicit non-actions (still forbidden)

- Do not optimize terciles, clocks, or 0.05 ONR cutoffs
- Do not add VWAP / SMT / EMA / ORB
- Do not restrict weekdays or drop years
- Do not convert `strong_and_persistent` into a strategy because OOS win looks high

---

## What this implies for the research program

We have now falsified two layers:

1. **Level + confirmation → next move** — failed cleanly.
2. **Simple morning state (vol / persistence / location / speed) → next move** — no material odds shift.

The remaining question is narrower and harder:

> Is there *any* mid-morning variable (possibly cross-asset, volume shock, or multi-scale) that changes odds enough to support a wait/go rule — still without mining?

If the next pass also returns ~50–52% with bad payoff, the correct conclusion is:

**The first 30–60 minutes of NQ are noisy; references exist, but tradable state transitions are not evident in this feature family.**

---

## Artifacts

- `artifacts/ny_open_state_panel.parquet`
- `artifacts/ny_open_state_transitions.csv`
- `artifacts/ny_open_state_transition_report.json`
- `artifacts/ny_open_state_thresholds_IS.json`
- `artifacts/ny_open_state_onr_sanity.txt`
- `run_ny_open_state_transitions.py`
