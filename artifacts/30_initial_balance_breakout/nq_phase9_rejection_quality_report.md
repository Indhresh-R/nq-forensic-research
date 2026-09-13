# Phase 9A — rejection quality

Train-fixed thresholds: excursion ≥ 0.464 IB widths (top 20%) and rejection ratio ≥ 0.273. Rejection ratio is re-entry depth divided by maximum outside excursion.

## By direction and geometry

| period     | side                  | geometry                         |   n |    mfe60 |    mae60 |         net |   p_mfe_025 |   p_mfe_050 |
|:-----------|:----------------------|:---------------------------------|----:|---------:|---------:|------------:|------------:|------------:|
| Inner      | downside_failure_long | large_excursion_strong_rejection |   1 | 0.107011 | 0.98893  | -0.881919   |    0        |    0        |
| Inner      | downside_failure_long | other                            | 214 | 0.314138 | 0.446627 | -0.132489   |    0.542056 |    0.182243 |
| Inner      | upside_failure_short  | large_excursion_strong_rejection |   9 | 0.607033 | 0.351043 |  0.25599    |    0.888889 |    0.444444 |
| Inner      | upside_failure_short  | other                            | 274 | 0.283578 | 0.311644 | -0.0280661  |    0.405109 |    0.160584 |
| OOS        | downside_failure_long | large_excursion_strong_rejection |   4 | 0.534229 | 0.509505 |  0.024724   |    0.75     |    0.5      |
| OOS        | downside_failure_long | other                            | 112 | 0.309681 | 0.372049 | -0.0623681  |    0.508929 |    0.169643 |
| OOS        | upside_failure_short  | large_excursion_strong_rejection |   3 | 1.01101  | 0.19729  |  0.813722   |    1        |    0.666667 |
| OOS        | upside_failure_short  | other                            | 160 | 0.280335 | 0.313391 | -0.0330559  |    0.4875   |    0.14375  |
| Train      | downside_failure_long | large_excursion_strong_rejection |  13 | 0.645932 | 0.609783 |  0.0361488  |    0.846154 |    0.461538 |
| Train      | downside_failure_long | other                            | 455 | 0.321684 | 0.384886 | -0.0632021  |    0.494505 |    0.195604 |
| Train      | upside_failure_short  | large_excursion_strong_rejection |  10 | 0.595986 | 0.41363  |  0.182356   |    0.5      |    0.3      |
| Train      | upside_failure_short  | other                            | 535 | 0.303106 | 0.30065  |  0.00245611 |    0.441121 |    0.183178 |
| Validation | downside_failure_long | large_excursion_strong_rejection |   7 | 0.268862 | 0.929333 | -0.660471   |    0.285714 |    0.285714 |
| Validation | downside_failure_long | other                            | 250 | 0.301517 | 0.336662 | -0.0351449  |    0.492    |    0.192    |
| Validation | upside_failure_short  | large_excursion_strong_rejection |   2 | 0.306466 | 0.258488 |  0.0479771  |    0.5      |    0.5      |
| Validation | upside_failure_short  | other                            | 269 | 0.318515 | 0.324322 | -0.00580702 |    0.460967 |    0.226766 |

## Pooled comparison

| period     | geometry                         |   n |    mfe60 |    mae60 |        net |
|:-----------|:---------------------------------|----:|---------:|---------:|-----------:|
| Inner      | large_excursion_strong_rejection |  10 | 0.557031 | 0.414832 |  0.142199  |
| Inner      | other                            | 488 | 0.296979 | 0.370838 | -0.0738582 |
| OOS        | large_excursion_strong_rejection |   7 | 0.738565 | 0.375698 |  0.362866  |
| OOS        | other                            | 272 | 0.292419 | 0.337545 | -0.0451257 |
| Train      | large_excursion_strong_rejection |  23 | 0.624216 | 0.524499 |  0.0997171 |
| Train      | other                            | 990 | 0.311644 | 0.339365 | -0.0277201 |
| Validation | large_excursion_strong_rejection |   9 | 0.277218 | 0.780256 | -0.503038  |
| Validation | other                            | 519 | 0.310327 | 0.330266 | -0.019939  |

Outcome is still next-60-minute normalized MFE minus MAE after the first causal re-entry. This is mechanism evidence, not a tradable confirmation rule.