# Strategy 52 — Market State Census (Step 0)

Descriptive census of NQ market conditions. **No trading logic.**

## Run

```bash
python strategies/52_market_state_census/code/run_census.py
```

Or step-by-step:

```bash
python strategies/52_market_state_census/code/build_market_state_features.py
python strategies/52_market_state_census/code/classify_market_states.py
python strategies/52_market_state_census/code/analyze_state_distribution.py
python strategies/52_market_state_census/code/analyze_state_persistence.py
python strategies/52_market_state_census/code/audit_market_state.py
python strategies/52_market_state_census/code/write_census_report.py
```

## Docs

- `PREREGISTRATION.md` — Step 0 frozen definitions
- `MARKET_STATE_CENSUS.md` — Step 0 descriptive report (generated)
- `STEP1_PREREGISTRATION.md` — Step 1 path-geometry freeze
- `STEP1_PATH_GEOMETRY.md` — Step 1 mechanism report (generated)
- `STEP2_PREREGISTRATION.md` — Step 2 transition-event freeze
- `STEP2_TRANSITION_EVENTS.md` — Step 2 mechanism report (generated)
- `STEP3_PREREGISTRATION.md` — Step 3 destination-stability freeze
- `STEP3_DESTINATION_STABILITY.md` — Step 3 report (generated)
- `STEP4_PREREGISTRATION.md` — Step 4 matched-transition freeze
- `STEP4_MATCHED_TRANSITIONS.md` — Step 4 report (generated)
- `STEP5_PREREGISTRATION.md` — Step 5 signed-exit-position freeze
- `STEP5_SIGNED_EXIT_POSITION.md` — Step 5 report (generated)
- `STEP6_PREREGISTRATION.md` — Step 6 directionality-decomposition freeze
- `STEP6_DIRECTIONALITY_DECOMPOSITION.md` — Step 6 report (generated)
- `STEP7_PREREGISTRATION.md` — Step 7 low-ER origin-history freeze
- `STEP7_ORIGIN_HISTORY.md` — Step 7 report (generated)
- `STEP8_PREREGISTRATION.md` — Step 8 path-feasibility freeze
- `STEP8_PATH_FEASIBILITY.md` — Step 8 report (generated)
- `STEP9_PREREGISTRATION.md` — Step 9 single executable-hypothesis freeze
- `STEP9_EXECUTABLE_HYPOTHESIS.md` — Step 9 report (generated)

## Code

| Module | Role |
| --- | --- |
| `build_market_state_features.py` | Causal ER / RV / ATR / RVOL / range features |
| `classify_market_states.py` | IS-frozen terciles + labels |
| `analyze_state_distribution.py` | Tables 1–7, overlaps |
| `analyze_state_persistence.py` | Tables 8–9, compression→expansion rates |
| `audit_market_state.py` | Leakage / scope audit |
| `write_census_report.py` | Markdown report |
| `run_census.py` | Step 0 end-to-end orchestrator |
| `run_step1.py` | Step 1 path-geometry orchestrator |
| `step1_extract_paths.py` | Episode onsets + forward path metrics |
| `step1_analyze.py` | A/B and C/D contrasts |
| `step1_audit.py` | Step 1 scope audit |
| `step1_write_report.py` | Step 1 markdown report |
| `run_step2.py` | Step 2 transition-event orchestrator |
| `step2_extract_transitions.py` | First →NORMAL events + post-event paths |
| `step2_analyze.py` | CompExit / ExpExit contrasts |
| `step2_audit.py` | Step 2 scope audit |
| `step2_write_report.py` | Step 2 markdown report |
| `run_step3.py` | Step 3 destination-stability orchestrator |
| `step3_analyze.py` | Split / wait / orthogonal destination contrasts |
| `step3_audit.py` | Step 3 scope audit |
| `step3_write_report.py` | Step 3 markdown report |
| `run_step4.py` | Step 4 matched-transition orchestrator |
| `step4_analyze.py` | Pre-event geometry + CEM matching |
| `step4_audit.py` | Step 4 scope audit |
| `step4_write_report.py` | Step 4 markdown report |
| `run_step5.py` | Step 5 signed-exit-position orchestrator |
| `step5_analyze.py` | Signed S + within-bin C/D contrasts |
| `step5_audit.py` | Step 5 scope audit |
| `step5_write_report.py` | Step 5 markdown report |
| `run_step6.py` | Step 6 directionality-decomposition orchestrator |
| `step6_analyze.py` | Transition components + within-bin contrasts |
| `step6_audit.py` | Step 6 scope audit |
| `step6_write_report.py` | Step 6 markdown report |
| `run_step7.py` | Step 7 low-ER origin-history orchestrator |
| `step7_analyze.py` | Duration history + within-bin contrasts |
| `step7_audit.py` | Step 7 scope audit |
| `step7_write_report.py` | Step 7 markdown report |
| `run_step8.py` | Step 8 path-feasibility orchestrator |
| `step8_analyze.py` | Forward path / timing / competing-path audit |
| `step8_audit.py` | Step 8 scope audit |
| `step8_write_report.py` | Step 8 markdown report |
| `run_step9.py` | Step 9 executable-hypothesis orchestrator |
| `step9_analyze.py` | Single fade-to-mid trade ledger + gate |
| `step9_audit.py` | Step 9 scope audit |
| `step9_write_report.py` | Step 9 markdown report |

### Step 1

```bash
python strategies/52_market_state_census/code/run_step1.py
```

### Step 2

```bash
python strategies/52_market_state_census/code/run_step2.py
```

### Step 3

```bash
python strategies/52_market_state_census/code/run_step3.py
```

### Step 4

```bash
python strategies/52_market_state_census/code/run_step4.py
```

### Step 5

```bash
python strategies/52_market_state_census/code/run_step5.py
```

### Step 6

```bash
python strategies/52_market_state_census/code/run_step6.py
```

### Step 7

```bash
python strategies/52_market_state_census/code/run_step7.py
```

### Step 8

```bash
python strategies/52_market_state_census/code/run_step8.py
```

### Step 9

```bash
python strategies/52_market_state_census/code/run_step9.py
```
