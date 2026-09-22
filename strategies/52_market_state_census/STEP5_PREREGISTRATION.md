# Step 5 Preregistration — Signed exit displacement (ExpExit diagnostic)

**Status:** FROZEN BEFORE SIGNED-POSITION ANALYSIS.  
**Parent:** Strategy 52 Steps 0–4.  
**Namespace:** `strategies/52_market_state_census/`  
**Label:** Single-feature mechanism diagnostic only. **Not** a trading strategy.

Scope: **ExpExit only** (C vs D). CompExit is not re-tested here (`B_COMPOSITIONAL` in Step 4).

No giant CEM. No new matching recipe. No directional trade labels.

---

## Question

> After controlling for **where** the C/D exit occurs relative to the pre-event origin range (signed position), does the C-vs-D destination asymmetry remain?

---

## Feature (frozen)

Pre-event origin envelope uses bars `[i0, te)` (onset through last non-NORMAL bar before the event), same window family as Step 4:

- `P_high = max(high)`, `P_low = min(low)` over `[i0, te)`
- `P_mid = 0.5 * (P_high + P_low)`
- `R = P_high − P_low` (require `R > 0`)

Event price at the NORMAL transition:

- `P_event = close[te]`

Primary signed normalized position:

\[
S = \frac{P_{\text{event}} - P_{\text{mid}}}{R}
\]

Secondary (reported only): `S_atr = (P_event - P_mid) / ATR_30[te-1]`.

All inputs are available at `te`. No post-event path information.

---

## Binning (frozen before destination claims)

On **IS ExpExit events only**, freeze tercile cuts of `S` (33% / 67%).

| Bin | Rule |
| --- | --- |
| `S_T1` | `S ≤ q33` |
| `S_T2` | `q33 < S ≤ q67` |
| `S_T3` | `S > q67` |

Also report a **sign split** (not used to retune terciles): `S < 0` vs `S ≥ 0`.

Apply the same IS cuts to Validation / OOS / pooled.

---

## Endpoints

Unchanged from Steps 2–4:

| Endpoint | Horizons |
| --- | --- |
| `P(return_to_origin_range)` | **30m primary**, 60m secondary |
| `P(reach_opposite_range)` | **30m primary**, 60m secondary |

Contrast: **`D − C`** within each `S` bin.

Minimum-n for an eligible within-bin claim: both C and D have `n_valid ≥ 200` at the primary horizon (same rule spirit as Step 3).

---

## Predeclared interpretation

| Result | Interpretation |
| --- | --- |
| **Remain** | Eligible bins keep the same sign as pooled Step-4 unmatched ExpExit destination diffs, and typical `|within-bin diff|` is not collapsed near zero | More consistent with **directionality-at-exit** (still associative, not causal proof) |
| **Disappear** | Eligible bins lose the Step-4 sign **or** shrink below half the unmatched pooled magnitude on both endpoints | Residual was likely **geometry not yet matched** (unsigned distance insufficient; side/location mattered) |
| **Conditional** | Only some signed-position regions show the asymmetry; others do not | Association is **conditional on exit location** |

“Remain / disappear / conditional” is judged on the **primary horizon (30m)** using eligible bins only.

---

## Forbidden

- Re-running CompExit as a primary claim
- Adding this feature into a re-optimized CEM to maximize residual effect
- Future returns, post-event displacement, CVD/delta, ER variants as the Step 5 object
- Continuation / reversal trade language

---

## Outputs

| Path | Role |
| --- | --- |
| `results/step5_signed_features.parquet` | Per-event `S`, bins |
| `results/step5_s_cuts_frozen.json` | IS tercile cuts |
| `results/step5_within_bin_contrasts.csv` | D−C by S bin |
| `results/step5_composition.csv` | C/D mass by bin |
| `results/step5_verdict.json` | Remain / disappear / conditional |
| `results/step5_audit.json` | Scope audit |
| `STEP5_SIGNED_EXIT_POSITION.md` | Report |

---

## Verdict format

**STEP 5 VERDICT** using the three outcomes above, then **NEXT RESEARCH QUESTION** (still not a trade).
