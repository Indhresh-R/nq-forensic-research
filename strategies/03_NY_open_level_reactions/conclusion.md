# Conclusion — NY Open Level Acceptance / Rejection

## Verdict

**`C`** — No demonstrated edge. Strict causal survivors = **0**.

## Why (numbers)

After removing label/forward overlap, best soft leftover `C_PDH_reject` is IS h15 win **52.2%** / mean **+2.03 pts** / **0.023 ONR** — too weak. Impulse continuation is anti-edge (IS win **44.5%**, mean **−2.37**). Soft stress strategy on `C_PDL_accept`: n=779, WR=41.8%, PF=0.90, E[R]=**−0.127**, totalR=**−99**.

## Split snapshot

| Split | Result |
|-------|--------|
| IS | soft ~52% / stress E[R] −0.165 |
| Validation | soft higher win, stress still ≤0 |
| OOS | soft mixed; stress E[R] −0.103; 2025 WR 32.8% |

## What not to do next

- Do not resurrect contaminated first-pass (75–97% WR) accept/reject labels
- Do not promote soft PDH/PDL leftovers without a new information class
