# Results — NY Open State Transitions

**Verdict: `B_weak_state_transition`** (kill for trading)

Canonical: [`artifacts/04_NY_open_state_transitions/ny_open_state_transition_report.md`](../../../artifacts/04_NY_open_state_transitions/ny_open_state_transition_report.md)

Panel: **25,200** rows · **3,601** days.

## Key cells

| State / clock | IS n | IS win | Val | OOS | 2025 | 2026 | Notes |
|---------------|-----:|-------:|----:|----:|-----:|-----:|-------|
| `open_near_ONH` +5→h30 | 586 | **55.9%** | 54.6% | 54.7% | **47.3%** | **65.0%** | year unstable |
| `strong_and_persistent` +10→h15 | 658 | 53.2% | 58.0% | **59.6%** | 54.5% | **69.7%** | IS mean **−0.3** pts |
| `high_persistence` +5→h5 | — | 55.2% | 50.7% | 54.6% | — | — | ~coin |

Typical odds shift vs unconditional ~52%: only **+3 to +6pp** IS.

## Raw-pt artifact (must normalize)

`wide_ON_quiet_open` T+10 h5: raw ΔP10 **+0.07** → ONR ΔP05 **−0.09** (sign flips under ONR).

**Kill number:** closest OOS win **59.6%** but IS mean **−0.3** pts and 2025/2026 **54.5%/69.7%**.
