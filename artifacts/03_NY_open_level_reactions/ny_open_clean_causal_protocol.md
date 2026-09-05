# NQ NY Open — Clean Causal Protocol Card

Contaminated first-pass results are **nonexistent** for decision-making.
This document describes only the post-confirmation analysis.

---

## Execution model (applies to every event below)

| # | Rule | Implementation |
|---|------|----------------|
| 1 | Exact signal timestamp | Close of the **confirmation** 1m bar (`signal_ny_min` / confirmation index). Not the first touch. |
| 2 | Information at that timestamp | Overnight H/L (known by 09:29), prior-day H/L/C (completed session), open@09:30, path from 09:30 through confirmation bar inclusive. **No** later bars. |
| 3 | Confirmation rule | After first close beyond level: within next ≤15 bars, **first** of (a) accept = close ≥ level ± 0.15·ONR beyond breakout, or (b) reject = close back through level. |
| 4 | Entry | **Next bar open** after confirmation bar (`entry_i = conf_i + 1`). |
| 5 | Forward outcome | Close at entry+5/10/15/20/30m minus entry, signed in trade direction. Starts at entry bar. |
| 6 | No overlap | Classification uses bars `touch+1 … conf`. Outcome uses bars `entry … entry+H`. These sets are disjoint (`entry = conf+1`). |
| 7 | Splits | IS 2010–2021; Validation 2022–2024; OOS 2025–2026. Thresholds frozen on IS only (impulse large = IS P66 of impulse/ONR = 0.50). |
| 8 | OOS years | Reported separately for 2025 and 2026 where sample allows. |
| 9 | Frequency | Event rate = events / session days (≤1 first-touch per level per day). |
| 10 | Costs | Directional table = **gross** pts (predictive test). Strategy stress uses **0.5 pt/side slippage + 0.5 pt RT commission**, stop-first, 1.5R target, risk = max(0.25·ONR, 5 pts). |

Unconditional reference: long from 09:45 open → +15m close: win **51.8%**, mean **+0.72** pts (n=3598).

---

## Event definitions (clean)

### Level accept / reject (Hypothesis C family)

1. First touch: first 1m close beyond ONH/ONL/PDH/PDL after 09:30.
2. Confirmation: first decisive accept or reject bar after touch (rule above).
3. Trade direction: accept → breakout direction; reject → fade.
4. Entry: next bar open after confirmation.
5. Outcome: forward signed returns from entry only.

### Impulse continuation (Hypothesis A)

1. Impulse: direction + extreme inside first 10m after 09:30 (known at that extreme bar).
2. Confirmation: first later bar where pullback from extreme reaches **38.2%** of impulse **without** closing through 09:30 open.
3. Entry: next bar open; direction = impulse direction.
4. “Large” = impulse/ONR ≥ 0.50 (IS P66).

### Failed impulse reversal (Hypothesis B)

1. Same impulse definition.
2. Confirmation: first close through 09:30 open after impulse extreme.
3. Entry: next bar open; direction = opposite impulse.

---

## Clean predictive results (gross directional, post-entry)

### Kill criteria applied

- Need materially above coin-flip **and** payoff asymmetry that survives costs.
- ~50–52% with ~0.02 ONR mean → **kill**.
- No “phenomenon is strong so optimize entry.”

### Best soft leftover: PDH reject (fade after rejection confirmed)

| Split | n | h15 win | h15 mean pts | h15/ONR | h30 win | h30 mean |
|-------|---|---------|--------------|---------|---------|----------|
| IS | 324 | 52.2% | +2.03 | 0.023 | 52.2% | +1.78 |
| Validation | 106 | 63.2% | +9.08 | 0.085 | 54.7% | +12.4 |
| OOS | 65 | 58.5% | +10.6 | 0.031 | 56.9% | +9.1 |

Frequency: ~495 / 3601 ≈ **0.14 events/day** (not 1–2/day alone). Entry typically ~20m after 09:30 (median entry offset 21m; p25–p75 = 9–47m).

OOS year split (gross h15):

| Year | n | h15 win | h15 mean | h30 win | h30 mean |
|------|---|---------|----------|---------|----------|
| 2025 | 38 | 55.3% | +4.8 | 55.3% | +7.2 |
| 2026 | 27 | 63.0% | +18.7 | 59.3% | +11.8 |

**Decision:** IS is **52.2%** — at the floor of “interesting,” but ONR-normalized mean is only **0.023**. Val/OOS (and especially 2026 n=27) look better; that cannot promote an IS-weak core, and must not trigger entry optimization. **Kill as strategy seed.**

### Soft leftover: PDL accept

| Split | n | h15 win | h15 mean | h30 win | h30 mean |
|-------|---|---------|----------|---------|----------|
| IS | 223 | 51.1% | +0.41 | 53.4% | +0.83 |
| Validation | 90 | 57.8% | +1.61 | 45.6% | +0.78 |
| OOS | 45 | 55.6% | +6.81 | **37.8%** | **−13.5** |

| Year | n | h15 win | h15 mean | h30 win | h30 mean |
|------|---|---------|----------|---------|----------|
| 2025 | 29 | **41.4%** | **−16.7** | 34.5% | −32.3 |
| 2026 | 16 | 81.3% | +49.3 | 43.8% | +20.6 |

2025 vs 2026 disagree violently; 2026 n=16 is noise. Frequency ~0.10/day. **Kill.**

### Core mechanisms (clean)

| Event | IS h15 win | IS h15 mean | Verdict |
|-------|------------|-------------|---------|
| Large impulse continuation | 44.5% | −2.37 | Kill |
| Large failed-impulse reversal | 48.1% | −0.16 | Kill |
| ONH accept | 50.9% | −0.57 | Kill |
| ONL reject | 54.0% | +1.07 | Kill (Val mean negative; OOS ~50%) |

### Costed mechanical stress (not a candidate)

Soft PDL-accept → stop 0.25·ONR (min 5), target 1.5R, costs included:

| Split | n | WR | E[R] | PF |
|-------|---|----|------|-----|
| IS | 498 | 42.0% | −0.165 | 0.89 |
| Validation | 187 | 41.7% | −0.037 | 0.91 |
| OOS | 94 | 41.5% | −0.103 | 0.92 |
| 2025 | 58 | 32.8% | −0.316 | — |
| 2026 | 36 | 55.6% | +0.240 | — |

PF ~0.9, expectancy negative. **Kill.**

---

## Final clean call

**The clean post-confirmation event itself does not carry usable predictive information** under the hostile bar:

- No event clears ~52–55% IS directional accuracy **with** stable payoff asymmetry after costs.
- Closest case (PDH reject) is 52.2% IS / 0.023 ONR — economically nothing.
- Do not optimize entries, add filters, or revisit contaminated numbers.

**Verdict remains C — no demonstrated edge.**
