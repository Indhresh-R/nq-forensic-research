# Results — NY Open Level Acceptance / Rejection

**Verdict: `C`** — survivors_strict = **none**

Canonical: [`artifacts/03_NY_open_level_reactions/ny_open_behavioral_report.md`](../../../artifacts/03_NY_open_level_reactions/ny_open_behavioral_report.md)

Dataset 2010-06→2026-08. Impulse thr (IS P66 impulse/ONR) = **0.5000**. First-pass accept/reject with label/forward overlap was **D (contaminated)** — discarded (tautological WR 75–97%).

## Structural facts

| Fact | Value |
|------|------:|
| ONR median / mean | **58.8 / 89.8** pts |
| OR medians 1m / 5m / 10m / 30m | 11.8 / 23.0 / 31.8 / 46.0 |
| By 11:00 touch ONH / ONL / both | 56% / 52% / 17% |
| PDH / PDL touch | 42% / 29% |
| P(5m dir extends to 30m) | **52.6%** |
| 2025 / 2026 med ONR | 154.5 / **235.0** |

## Causal candidates (post-confirm, next-bar) — none strict

| ID | n | IS h15 win / mean | Val win | OOS win | h15/ONR |
|----|--:|-------------------:|--------:|--------:|--------:|
| `C_PDH_reject` (best soft) | 495 | **0.522** / +2.03 | 0.632 | 0.585 | **0.023** |
| `C_PDL_accept` | 358 | 0.511 / +0.41 | 0.578 | 0.556 | 0.037 |
| `C_ONH_accept` | 857 | 0.509 / −0.57 | 0.557 | 0.545 | 0.016 |
| `C_ONL_reject` | 847 | 0.540 / +1.07 | 0.531 | 0.505 | 0.023 |
| `A_large_impulse_continuation` | 942 | **0.445** / **−2.37** | 0.473 | 0.515 | −0.056 |
| `B_any_failed_impulse_reversal` | 2008 | 0.478 / −0.85 | 0.439 | 0.460 | — |

Strict survival: **0**. Soft same-sign leftovers only: `C_PDH_reject`, `C_PDL_accept`.

## Diagnostic stress (soft `C_PDL_accept` — not a candidate)

Costs 0.5pt/side + 0.5pt RT; stop-first.

| Split | n | WR | E[R] | Total R | Avg pts | PF |
|-------|--:|---:|-----:|--------:|--------:|---:|
| ALL | 779 | **41.8%** | **−0.127** | **−99.0** | −1.15 | **0.904** |
| IS | 498 | 42.0% | −0.165 | −82.3 | −0.80 | 0.888 |
| Validation | 187 | 41.7% | −0.037 | −7.0 | −1.68 | 0.908 |
| OOS | 94 | 41.5% | −0.103 | −9.7 | −1.97 | 0.921 |
| 2025 | 58 | **32.8%** | −0.316 | **−18.3** | — | — |
| 2026 | 36 | 55.6% | +0.240 | +8.6 | — | — |

**Kill number:** best soft IS win **52.2%** (~0.02 ONR mean); executable stress E[R]=**−0.127**.
