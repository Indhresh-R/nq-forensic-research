# NQ NY Open — Behavioral Discovery Report

**Verdict: C — No demonstrated edge**

After removing label/forward overlap contamination, no NY-open mechanism survives strict IS→Validation→OOS tests with economically meaningful post-confirmation conditional returns. Soft leftovers (PDH reject, PDL accept) sit near ~52% IS win / ~0.02 ONR mean — destroyed by realistic stops and costs.

> **Methodology:** First-pass accept/reject and pullback signals selected on future bars that overlapped the forward-return window (tautological 75–97% short-horizon win rates). Those results are **D — contaminated** and discarded. This report uses post-confirmation next-bar entries only.

Dataset: `nq_1m_continuous.parquet` (2010-06 → 2026-08). IS/Val/OOS = 2010–2021 / 2022–2024 / 2025–2026. Large-impulse threshold (IS P66 impulse/ONR) = **0.5000**.

## 1. NQ Behavioral Facts

- Overnight range median **58.8** pts (mean 89.8); non-stationary across 2010–2026.
- Opening range medians: 1m **11.8**, 5m **23.0**, 10m **31.8**, 30m **46.0** pts.
- By 11:00 ET: ONH **56%**, ONL **52%**, both **17%**; PDH **42%**, PDL **29%**.
- P(5m direction extends to 30m) = **52.6%** — weak persistence.
- Ex-post impulse pullback depth (descriptive): median **1.06×** impulse.

### Year-by-year (median pts)

| Year | n | ONR | 30m | impulse/ONR |
|------|---|-----|-----|-------------|
| 2010 | 32 | 13.1 | 11.5 | 0.361 |
| 2011 | 73 | 16.8 | 12.8 | 0.296 |
| 2012 | 111 | 15.5 | 12.2 | 0.366 |
| 2013 | 211 | 14.0 | 12.5 | 0.400 |
| 2014 | 211 | 17.8 | 16.5 | 0.409 |
| 2015 | 231 | 27.2 | 22.8 | 0.375 |
| 2016 | 258 | 24.8 | 19.5 | 0.367 |
| 2017 | 257 | 19.5 | 18.2 | 0.469 |
| 2018 | 257 | 46.5 | 39.8 | 0.398 |
| 2019 | 258 | 44.2 | 33.8 | 0.358 |
| 2020 | 258 | 102.8 | 77.1 | 0.353 |
| 2021 | 258 | 97.0 | 81.2 | 0.412 |
| 2022 | 258 | 159.8 | 123.5 | 0.360 |
| 2023 | 257 | 102.0 | 79.2 | 0.364 |
| 2024 | 259 | 124.2 | 91.2 | 0.331 |
| 2025 | 257 | 154.5 | 125.0 | 0.383 |
| 2026 | 155 | 235.0 | 186.2 | 0.359 |

## 2. Common-Sense Deductions

- Overnight extremes are tested often enough to study acceptance/rejection.
- First-5m direction is only weakly persistent; blind continuation is unlikely.
- Point thresholds are invalid across eras — normalize by ONR/ATR.
- Any accept/reject edge must be measured **after** confirmation, not during the labeling window.

## 3. Candidate Phenomena (causal)

| Rank | ID | n | Score | Strict | IS h15 win/mean | Val | OOS |
|------|----|---|-------|--------|-----------------|-----|-----|
| 1 | `C_PDH_reject` | 495 | 23.8 | False | 0.522/2.03 | 0.632 | 0.585 |
| 2 | `C_PDL_accept` | 358 | 14.5 | False | 0.511/0.41 | 0.578 | 0.556 |
| 3 | `C_ONH_accept` | 857 | 11.2 | False | 0.509/-0.57 | 0.557 | 0.545 |
| 4 | `C_PDL_reject` | 338 | 8.2 | False | 0.531/1.36 | 0.446 | 0.606 |
| 5 | `C_ONL_reject` | 847 | 7.5 | False | 0.540/1.07 | 0.531 | 0.505 |
| 6 | `C_PDH_accept` | 424 | 3.1 | False | 0.475/-0.47 | 0.485 | 0.571 |
| 7 | `C_ONL_accept` | 833 | -1.6 | False | 0.465/-0.71 | 0.503 | 0.516 |
| 8 | `A_large_impulse_continuation` | 942 | -6.7 | False | 0.445/-2.37 | 0.473 | 0.515 |
| 9 | `A_any_impulse_continuation` | 3207 | -6.8 | False | 0.473/-1.68 | 0.477 | 0.481 |
| 10 | `C_ONH_reject` | 959 | -8.3 | False | 0.468/1.06 | 0.498 | 0.451 |
| 11 | `B_large_failed_impulse_reversal` | 438 | -8.5 | False | 0.481/-0.16 | 0.525 | 0.409 |
| 12 | `B_any_failed_impulse_reversal` | 2008 | -12.3 | False | 0.478/-0.85 | 0.439 | 0.460 |
| 13 | `E_gap_through_reclaim` | 7 | -33.3 | False | 0.667/21.38 | 0.000 | nan |

### Sanity: IS h5 vs h15 win (causal should not show tautological h5)

| ID | h5 win | h15 win | h15 mean | h15/ONR |
|----|--------|---------|----------|---------|
| C_PDH_reject | 0.5462962962962963 | 0.5216049382716049 | 2.0316358024691357 | 0.02254112132368926 |
| C_PDL_accept | 0.4798206278026906 | 0.5112107623318386 | 0.4069506726457399 | 0.037209620679253826 |
| C_ONH_accept | 0.49072512647554806 | 0.5092748735244519 | -0.5704047217537943 | 0.016009696013246758 |
| C_PDL_reject | 0.49765258215962443 | 0.5305164319248826 | 1.3556338028169015 | 0.009538565523182115 |
| C_ONL_reject | 0.5345132743362832 | 0.5398230088495575 | 1.068141592920354 | 0.02269473296711314 |
| C_PDH_accept | 0.5 | 0.4746376811594203 | -0.46557971014492755 | -0.03156052214779563 |
| C_ONL_accept | 0.45080500894454384 | 0.46511627906976744 | -0.7066189624329159 | -0.011656184942528338 |
| A_large_impulse_continuation | 0.45701357466063347 | 0.444947209653092 | -2.374057315233786 | -0.05585006858143759 |

## 4. Falsification

- **C_PDH_reject**: too weak for strict survival; IS win_p=0.522
- **C_PDL_accept**: too weak for strict survival; IS win_p=0.511
- **C_ONH_accept**: mean sign unstable across splits; IS win_p=0.509
- **C_PDL_reject**: mean sign unstable across splits; IS win_p=0.531
- **C_ONL_reject**: mean sign unstable across splits; IS win_p=0.540
- **C_PDH_accept**: mean sign unstable across splits; IS win_p=0.475
- **C_ONL_accept**: mean sign unstable across splits; IS win_p=0.465
- **A_large_impulse_continuation**: mean sign unstable across splits; IS win_p=0.445
- **A_any_impulse_continuation**: mean sign unstable across splits; IS win_p=0.473
- **C_ONH_reject**: mean sign unstable across splits; IS win_p=0.468
- **B_large_failed_impulse_reversal**: mean sign unstable across splits; IS win_p=0.481
- **B_any_failed_impulse_reversal**: mean sign unstable across splits; IS win_p=0.478
- **E_gap_through_reclaim**: mean sign unstable across splits; IS n=6

## 5. Surviving Phenomena

**None** under strict causal criteria.
Soft same-sign: `C_PDH_reject`, `C_PDL_accept`

## 6–7. Strategy & Performance

**No Phase-7 strategy candidate.** Nothing cleared survival, so no executable edge was promoted.

Diagnostic stress test only (soft `C_PDL_accept`, not a candidate): next-bar entry post-confirm; stop-first; costs 0.5pt/side + 0.5pt RT. **Result: killed** (negative expectancy in IS/Val/OOS).

- N=779, WR=41.8%, PF=0.9035044023802472, E[R]=-0.127, totalR=-99.0, maxDD=-110.3R, medianR=-1.036, avgPts=-1.15, trades/day=1.00.
- MAE/MFE: 17.2/19.7. Ambiguous: 0.0%.

| Split | n | WR | E[R] | Total R | Avg pts | PF |
|-------|---|----|------|---------|---------|----|
| IS | 498 | 42.0% | -0.165 | -82.3 | -0.80 | 0.8880079899595199 |
| Validation | 187 | 41.7% | -0.037 | -7.0 | -1.68 | 0.9075867264442158 |
| OOS | 94 | 41.5% | -0.103 | -9.7 | -1.97 | 0.9209286227736215 |

| Year | n | Total R | Avg R | WR |
|------|---|---------|-------|----|
| 2010 | 5 | 0.1 | 0.030 | 60.0% |
| 2011 | 3 | 1.1 | 0.367 | 66.7% |
| 2012 | 14 | -7.1 | -0.504 | 28.6% |
| 2013 | 54 | -21.2 | -0.393 | 35.2% |
| 2014 | 52 | -7.9 | -0.153 | 48.1% |
| 2015 | 45 | -14.5 | -0.322 | 37.8% |
| 2016 | 50 | -12.3 | -0.246 | 42.0% |
| 2017 | 60 | -24.2 | -0.403 | 35.0% |
| 2018 | 57 | 6.8 | 0.119 | 50.9% |
| 2019 | 57 | 2.4 | 0.043 | 47.4% |
| 2020 | 37 | -5.9 | -0.159 | 37.8% |
| 2021 | 64 | 0.4 | 0.006 | 42.2% |
| 2022 | 61 | 6.2 | 0.102 | 47.5% |
| 2023 | 66 | -1.8 | -0.028 | 42.4% |
| 2024 | 60 | -11.4 | -0.189 | 35.0% |
| 2025 | 58 | -18.3 | -0.316 | 32.8% |
| 2026 | 36 | 8.6 | 0.240 | 55.6% |

2025/2026: `{'2025': {'n': 58, 'total_R': -18.341254117802468, 'avg_R': -0.3162285192724563, 'win_rate': 0.3275862068965517}, '2026': {'n': 36, 'total_R': 8.631597890229392, 'avg_R': 0.23976660806192754, 'win_rate': 0.5555555555555556}}`
OOS by weekday: `[{'dow': 0, 'n': 17, 'avg_R': 0.069751296193708, 'win_rate': 0.5294117647058824}, {'dow': 1, 'n': 20, 'avg_R': -0.13916220486929562, 'win_rate': 0.4}, {'dow': 2, 'n': 20, 'avg_R': -0.42346020370016435, 'win_rate': 0.3}, {'dow': 3, 'n': 17, 'avg_R': 0.42952521820729833, 'win_rate': 0.5882352941176471}, {'dow': 4, 'n': 20, 'avg_R': -0.34724544005004937, 'win_rate': 0.3}]`
Monthly profitability rate: 40%.

## 8. Final Verdict

**C — No demonstrated edge**

Successful research outcome: the NY cash open is structurally active (frequent ONH/ONL tests, rising vol), but once measured causally, common-sense mechanisms (impulse continuation, failed-impulse reversal, overnight/prior-day accept-reject) do **not** produce a small persistent executable asymmetry at ~1–2 trades/day.
