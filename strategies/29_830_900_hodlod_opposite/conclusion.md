# Conclusion — Strategy 29 (corrected)

## Verdict

**`C` — `NO_CAUSAL_EDGE` on the corrected (tradable) reading.**

Earlier Phase B used **end-of-day** HOD/LOD (lookahead). That was the wrong
idea. Your clarification is the right causal object:

> Before 09:30 we know whether 08:30–09:00 is the **high/low of the day so far**.
> We want that extreme **already established**, price **already reversing**, and
> **skip if 09:30 is still that extreme**. Then probe entries/exits — we do not
> assume which distances win.

Phase D tests exactly that. **0** Val+OOS survivors on the frozen entry/exit grid.

## Corrected setup (Phase D)

| Step | Rule |
|------|------|
| Label | At 09:00, W owns xor **day-so-far** high or low (session from 18:00) |
| Side | LOD_SO_FAR → long; HOD_SO_FAR → short |
| Reversal | By 09:29 close, ≥5 or ≥10 pts off the extreme |
| Skip | 09:30 open still at that so-far extreme |
| Entries | `impulse_pb` (impulse 10/15/20 + pullback 5/10) and `reclaim_O` (dip 5/10) |
| Exits | Fixed +20/25/30, structural stop, 30m time, 1pt cost |

## Frequency (labeled days)

Among days where W is xor day-so-far extreme (~hundreds/split):

| rev buffer | Split | Setup OK (reversed + not at extreme at open) |
|------------|-------|-----------------------------------------------|
| 5 pts | Discovery | 44% |
| 5 pts | Validation | 70% |
| 5 pts | OOS | 74% |
| 10 pts | Discovery | 25% |
| 10 pts | Validation | 62% |
| 10 pts | OOS | 71% |

Skip-at-open-extreme is rare (~1%). Most filters are “has it reversed yet.”

## Headline economics

**reclaim_O**, rev=10, dip=10, target=25:

| Split | n | Win | E_net |
|-------|--:|----:|------:|
| Discovery | 110 | 53% | **+0.75** |
| Validation | 174 | 55% | **−1.92** |
| OOS | 70 | 64% | **−2.86** |

**impulse_pb**, rev=10, impulse=15, pb=5, target=25:

| Split | n | Win | E_net |
|-------|--:|----:|------:|
| Discovery | 138 | 33% | **−1.64** |
| Validation | 197 | 37% | **−4.55** |
| OOS | 87 | 51% | **−0.95** |

Survivors (Val+OOS E_net>0, n≥30): **0**.

## What this means for you

- Your **structure filter** is clear and tradable (day-so-far, not EOD).
- On NQ 1m, with this frozen entry/exit menu, it does **not** produce a stable
  20–30 pt scalp edge after costs.
- Discovery sometimes looks soft-positive on reclaim; Val/OOS kill it — classic
  in-sample hope.

Phase B’s strong oracle numbers only said: *if you already knew it would be the
**final** day extreme, fading worked*. That is a different (non-tradable) claim.

## What not to do

- Do not discretionary-widen the grid until something “fits” OOS
- Do not mix EOD “that was the high” language into live entries
- Do not treat Discovery +0.7 pts as a green light

## Phase E — entry / risk / exit comparison

Expanded frozen grid (~**1,560** cells): entries `at_open`, `reclaim` dips 5/10/15,
`impulse_pb` (10/15/20 × pb 5/10), `break` 5/10/15; stops fixed 10–25 or structural;
targets fixed 15–40 or RR 1/1.5/2; holds 15/30/60.

| Family | Median E Discovery | Val | OOS |
|--------|-------------------:|----:|----:|
| reclaim | +0.15 | −1.36 | −3.62 |
| impulse_pb | −0.37 | −3.18 | −2.75 |
| break | −0.47 | −2.59 | −3.26 |
| at_open | −1.38 | −0.83 | −3.31 |

**Soft Val+OOS positives (3):** after fixing NaN pivot keys. Only **2** also Discovery>0:
`imp20_pb5/10` + fixed stop **25** / target **40** / hold **60** — E ≈ +0.12 Val / +0.51 OOS
(win ~40%). Year path unstable (**2025 −3.1 / 2026 +4.9**). Not promotable.

Artifacts: `phase_e_report.md`, `phase_e_survivors_fixed.csv`, canvas
`strategy-29-param-compare.canvas.tsx`.

## Optional next (only if you want)

Do **not** widen the grid further. Only a single pre-registered discretionary entry
you actually take, with a year-stability kill — otherwise close 29.
