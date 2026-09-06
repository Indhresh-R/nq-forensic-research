# Methodology — 23A COT Positioning

## Causality card

```text
Information available at signal T:
  - NQ bars with timestamp <= T
  - Latest COT report whose public RELEASE is strictly before T
    (release = Friday ~15:30 ET after the Tuesday report_date snapshot)

Entry / outcome start:
  next bar OPEN after T (standard causal rule)

Forbidden:
  - Using COT on Tuesday–Friday of the snapshot week
  - Using Friday bars on/after 15:30 as if the report were live before release
  - Refitting deciles / sides on Val or OOS
```

## External data lag (non-negotiable)

| Event | Time |
|-------|------|
| Position snapshot | `report_date_as_yyyy_mm_dd` = **Tuesday** |
| Public release | Following **Friday ~15:30 America/New_York** |
| First usable price action | **Next trading session after that Friday release** (typically Sunday 18:00 ET Globex → `session_date` = Monday) |

Same spirit as EOD-options lag in `research_framework/causal_rules.md`:
information dated D may only condition sessions that begin **after** the
information is public.

Implementation join key: `first_usable_session_date` … `< next_first_usable_session_date`.

## Frozen extreme formula (registered BEFORE any performance look)

Let \(L_t, S_t\) be long/short contracts for a trader category on report \(t\).

```text
net_t = L_t - S_t

# Trailing 2-year window = 104 prior weekly reports (exclusive of t)
W = 104
mu_t = mean(net_{t-W} … net_{t-1})
sd_t = std(net_{t-W} … net_{t-1}, ddof=1)
z_t  = (net_t - mu_t) / sd_t     # require sd_t > 0 and >= W history

# Extreme = top/bottom DECILE of the trailing z distribution (also exclusive)
z_lo_t = percentile(z_{t-W} … z_{t-1}, 10)
z_hi_t = percentile(z_{t-W} … z_{t-1}, 90)

extreme_hi_t = z_t >= z_hi_t
extreme_lo_t = z_t <= z_lo_t
# else: no COT signal that week
```

Categories frozen: Leveraged Money (`lev_*`), Asset Manager (`am_*`).
Dealer nets are pulled for audit/diagnostics only — **not** a promotion signal.

**Not allowed:** choosing the percentile that maximizes IS Sharpe/PF; expanding to
other CFTC categories after seeing results; combining lev+am into a mined stack.

## Strategy-12 HIGH conditioning

- Reuse frozen IS terciles: `artifacts/12_multi_session_opportunity/nq_multi_sess_opp_thresholds_IS.json`
- `HIGH` ⇔ `rng_psr >= p66` at session decision offset (same definition as Strategies 13–22)
- Sessions / clocks: ASIA, LONDON, NY_AM, NY_PM with `SESSION_DECISION_OFFSETS` from `common.sessions`

## Outcomes (pre-specified)

| Horizon | Use |
|---------|-----|
| H ∈ {30, 60, 120} minutes | Primary multi-horizon panel (next-open entry) |
| Week path (Mon usable → Friday RTH close) | Secondary week-bias diagnostic |

PnL in **points**, side-signed. Discovery stage = win rate + E[pts] (distributional).
Economics costs only if a later executable claim is made (mid = 1.0 pt RT).

## Baselines

1. **Unconditional** same session/T/H (no COT filter; long-only and/or coin-flip context via ALL+COT comparison)
2. **HIGH alone** (long-only inside HIGH) — COT must beat this to claim incremental sign resolution
3. **ALL+COT** vs **HIGH+COT** — lift of activity conditioning on top of COT

## Splits

Identical to `research_framework/train_validation_oos.md`:

```text
IS:  2010–2021
Val: 2022–2024
OOS: 2025–2026 (report years separately when n allows)
```

**Stage discipline:** score and publish **IS first**. Do not tune on Val/OOS.

## Multi-comparison note (family 23)

23A and 23D are sibling external-info tests. A single soft IS hit does **not**
justify promotion of family 23 without acknowledging the extra hypothesis count.

## Ambiguity / clustering

- Forward close at H: no stop/target path → no same-bar dual-touch ambiguity
- Multiple HIGH clocks per day are clustered; report per-clock and require
  multi-clock stability for promotion (program standard)
