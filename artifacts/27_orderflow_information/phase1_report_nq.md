# Strategy 27 — Phase 1 descriptives (NQ)

**PROXY STUDY - NOT ORDER FLOW.** No delta-R2. No rules.

- Panel rows (RTH): **1,382,157**
- Residual OLS (Discovery): {"intercept": 20.229380210062125, "ret_1m": 1506145.4565754547, "absret_1m": -8629.802982926718, "range_pct": -29113.07478413917, "n_fit": 926888}

## Headline Spearman (Validation + OOS emphasis)

Compare `signed_vol_proxy` vs `signed_vol_proxy_resid` vs raw `ret_1m` / `volume`.

| Split | H | Feature | Target | Spearman | n |
|-------|---|---------|--------|----------|---|
| Discovery | 5 | `absret_1m` | absret | 0.2633 | 914,302 |
| Discovery | 5 | `absret_per_vol` | absret | 0.0058 | 914,302 |
| Discovery | 5 | `ret_1m` | absret | -0.0185 | 914,302 |
| Discovery | 5 | `signed_vol_proxy` | absret | -0.0176 | 914,302 |
| Discovery | 5 | `signed_vol_proxy_resid` | absret | 0.0020 | 914,302 |
| Discovery | 5 | `signed_vol_proxy_sum_5` | absret | -0.0406 | 904,357 |
| Discovery | 5 | `vol_x_range` | absret | 0.4017 | 914,392 |
| Discovery | 5 | `vol_z_tod` | absret | 0.2680 | 914,392 |
| Discovery | 5 | `volume` | absret | 0.3412 | 914,392 |
| Discovery | 5 | `absret_1m` | ret | 0.0046 | 914,302 |
| Discovery | 5 | `absret_per_vol` | ret | -0.0012 | 914,302 |
| Discovery | 5 | `ret_1m` | ret | -0.0136 | 914,302 |
| Discovery | 5 | `signed_vol_proxy` | ret | -0.0108 | 914,302 |
| Discovery | 5 | `signed_vol_proxy_resid` | ret | -0.0027 | 914,302 |
| Discovery | 5 | `signed_vol_proxy_sum_5` | ret | -0.0169 | 904,357 |
| Discovery | 5 | `vol_x_range` | ret | 0.0081 | 914,392 |
| Discovery | 5 | `vol_z_tod` | ret | 0.0047 | 914,392 |
| Discovery | 5 | `volume` | ret | 0.0074 | 914,392 |
| Discovery | 5 | `absret_1m` | rv | 0.4052 | 914,302 |
| Discovery | 5 | `absret_per_vol` | rv | 0.0157 | 914,302 |
| Discovery | 5 | `ret_1m` | rv | -0.0275 | 914,302 |
| Discovery | 5 | `signed_vol_proxy` | rv | -0.0273 | 914,302 |
| Discovery | 5 | `signed_vol_proxy_resid` | rv | 0.0016 | 914,302 |
| Discovery | 5 | `signed_vol_proxy_sum_5` | rv | -0.0608 | 904,357 |
| Discovery | 5 | `vol_x_range` | rv | 0.6134 | 914,392 |
| Discovery | 5 | `vol_z_tod` | rv | 0.4025 | 914,392 |
| Discovery | 5 | `volume` | rv | 0.5155 | 914,392 |
| Discovery | 15 | `absret_1m` | absret | 0.2585 | 889,561 |
| Discovery | 15 | `absret_per_vol` | absret | 0.0069 | 889,561 |
| Discovery | 15 | `ret_1m` | absret | -0.0161 | 889,561 |
| Discovery | 15 | `signed_vol_proxy` | absret | -0.0152 | 889,561 |
| Discovery | 15 | `signed_vol_proxy_resid` | absret | 0.0039 | 889,561 |
| Discovery | 15 | `signed_vol_proxy_sum_5` | absret | -0.0344 | 879,770 |
| Discovery | 15 | `vol_x_range` | absret | 0.3942 | 889,615 |
| Discovery | 15 | `vol_z_tod` | absret | 0.2653 | 889,615 |
| Discovery | 15 | `volume` | absret | 0.3335 | 889,615 |
| Discovery | 15 | `absret_1m` | ret | 0.0092 | 889,561 |
| Discovery | 15 | `absret_per_vol` | ret | -0.0020 | 889,561 |
| Discovery | 15 | `ret_1m` | ret | -0.0066 | 889,561 |
| Discovery | 15 | `signed_vol_proxy` | ret | -0.0051 | 889,561 |
| Discovery | 15 | `signed_vol_proxy_resid` | ret | -0.0010 | 889,561 |
| Discovery | 15 | `signed_vol_proxy_sum_5` | ret | -0.0095 | 879,770 |
| Discovery | 15 | `vol_x_range` | ret | 0.0153 | 889,615 |
| Discovery | 15 | `vol_z_tod` | ret | 0.0095 | 889,615 |
| Discovery | 15 | `volume` | ret | 0.0142 | 889,615 |
| Discovery | 15 | `absret_1m` | rv | 0.4587 | 889,561 |
| Discovery | 15 | `absret_per_vol` | rv | 0.0182 | 889,561 |
| Discovery | 15 | `ret_1m` | rv | -0.0266 | 889,561 |
| Discovery | 15 | `signed_vol_proxy` | rv | -0.0264 | 889,561 |
| Discovery | 15 | `signed_vol_proxy_resid` | rv | 0.0042 | 889,561 |
| Discovery | 15 | `signed_vol_proxy_sum_5` | rv | -0.0606 | 879,770 |
| Discovery | 15 | `vol_x_range` | rv | 0.6941 | 889,615 |
| Discovery | 15 | `vol_z_tod` | rv | 0.4580 | 889,615 |
| Discovery | 15 | `volume` | rv | 0.5825 | 889,615 |
| Discovery | 30 | `absret_1m` | absret | 0.2529 | 852,959 |
| Discovery | 30 | `absret_per_vol` | absret | 0.0078 | 852,959 |
| Discovery | 30 | `ret_1m` | absret | -0.0153 | 852,959 |
| Discovery | 30 | `signed_vol_proxy` | absret | -0.0147 | 852,959 |
| Discovery | 30 | `signed_vol_proxy_resid` | absret | 0.0032 | 852,959 |
| Discovery | 30 | `signed_vol_proxy_sum_5` | absret | -0.0349 | 843,233 |
| Discovery | 30 | `vol_x_range` | absret | 0.3836 | 852,989 |
| Discovery | 30 | `vol_z_tod` | absret | 0.2597 | 852,989 |
| Discovery | 30 | `volume` | absret | 0.3232 | 852,989 |
| Discovery | 30 | `absret_1m` | ret | 0.0112 | 852,959 |
| Discovery | 30 | `absret_per_vol` | ret | -0.0025 | 852,959 |
| Discovery | 30 | `ret_1m` | ret | -0.0023 | 852,959 |
| Discovery | 30 | `signed_vol_proxy` | ret | -0.0018 | 852,959 |
| Discovery | 30 | `signed_vol_proxy_resid` | ret | -0.0005 | 852,959 |
| Discovery | 30 | `signed_vol_proxy_sum_5` | ret | -0.0052 | 843,233 |
| Discovery | 30 | `vol_x_range` | ret | 0.0193 | 852,989 |
| Discovery | 30 | `vol_z_tod` | ret | 0.0117 | 852,989 |
| Discovery | 30 | `volume` | ret | 0.0178 | 852,989 |
| Discovery | 30 | `absret_1m` | rv | 0.4672 | 852,959 |
| Discovery | 30 | `absret_per_vol` | rv | 0.0199 | 852,959 |
| Discovery | 30 | `ret_1m` | rv | -0.0245 | 852,959 |
| Discovery | 30 | `signed_vol_proxy` | rv | -0.0244 | 852,959 |
| Discovery | 30 | `signed_vol_proxy_resid` | rv | 0.0054 | 852,959 |
| Discovery | 30 | `signed_vol_proxy_sum_5` | rv | -0.0571 | 843,233 |
| Discovery | 30 | `vol_x_range` | rv | 0.7041 | 852,989 |
| Discovery | 30 | `vol_z_tod` | rv | 0.4696 | 852,989 |
| Discovery | 30 | `volume` | rv | 0.5892 | 852,989 |
| OOS | 5 | `absret_1m` | absret | 0.2725 | 155,965 |
| OOS | 5 | `absret_per_vol` | absret | 0.0832 | 155,965 |
| OOS | 5 | `ret_1m` | absret | -0.0166 | 155,965 |
| OOS | 5 | `signed_vol_proxy` | absret | -0.0144 | 155,965 |
| OOS | 5 | `signed_vol_proxy_resid` | absret | -0.0028 | 155,965 |
| OOS | 5 | `signed_vol_proxy_sum_5` | absret | -0.0289 | 154,317 |
| OOS | 5 | `vol_x_range` | absret | 0.4223 | 155,965 |
| OOS | 5 | `vol_z_tod` | absret | 0.2807 | 155,965 |
| OOS | 5 | `volume` | absret | 0.3498 | 155,965 |
| OOS | 5 | `absret_1m` | ret | 0.0113 | 155,965 |
| OOS | 5 | `absret_per_vol` | ret | 0.0010 | 155,965 |
| OOS | 5 | `ret_1m` | ret | -0.0046 | 155,965 |
| OOS | 5 | `signed_vol_proxy` | ret | -0.0039 | 155,965 |
| OOS | 5 | `signed_vol_proxy_resid` | ret | -0.0016 | 155,965 |
| OOS | 5 | `signed_vol_proxy_sum_5` | ret | -0.0027 | 154,317 |
| OOS | 5 | `vol_x_range` | ret | 0.0184 | 155,965 |
| OOS | 5 | `vol_z_tod` | ret | 0.0143 | 155,965 |
| OOS | 5 | `volume` | ret | 0.0185 | 155,965 |
| OOS | 5 | `absret_1m` | rv | 0.4157 | 155,965 |
| OOS | 5 | `absret_per_vol` | rv | 0.1214 | 155,965 |
| OOS | 5 | `ret_1m` | rv | -0.0266 | 155,965 |
| OOS | 5 | `signed_vol_proxy` | rv | -0.0235 | 155,965 |
| OOS | 5 | `signed_vol_proxy_resid` | rv | -0.0062 | 155,965 |
| OOS | 5 | `signed_vol_proxy_sum_5` | rv | -0.0503 | 154,317 |
| OOS | 5 | `vol_x_range` | rv | 0.6514 | 155,965 |
| OOS | 5 | `vol_z_tod` | rv | 0.4385 | 155,965 |
| OOS | 5 | `volume` | rv | 0.5421 | 155,965 |
| OOS | 15 | `absret_1m` | absret | 0.2675 | 151,845 |
| OOS | 15 | `absret_per_vol` | absret | 0.0831 | 151,845 |
| OOS | 15 | `ret_1m` | absret | -0.0137 | 151,845 |
| OOS | 15 | `signed_vol_proxy` | absret | -0.0114 | 151,845 |
| OOS | 15 | `signed_vol_proxy_resid` | absret | -0.0018 | 151,845 |
| OOS | 15 | `signed_vol_proxy_sum_5` | absret | -0.0304 | 150,197 |
| OOS | 15 | `vol_x_range` | absret | 0.4149 | 151,845 |
| OOS | 15 | `vol_z_tod` | absret | 0.2744 | 151,845 |
| OOS | 15 | `volume` | absret | 0.3403 | 151,845 |
| OOS | 15 | `absret_1m` | ret | 0.0156 | 151,845 |
| OOS | 15 | `absret_per_vol` | ret | 0.0012 | 151,845 |
| OOS | 15 | `ret_1m` | ret | -0.0027 | 151,845 |
| OOS | 15 | `signed_vol_proxy` | ret | -0.0014 | 151,845 |
| OOS | 15 | `signed_vol_proxy_resid` | ret | 0.0001 | 151,845 |
| OOS | 15 | `signed_vol_proxy_sum_5` | ret | 0.0002 | 150,197 |
| OOS | 15 | `vol_x_range` | ret | 0.0258 | 151,845 |
| OOS | 15 | `vol_z_tod` | ret | 0.0183 | 151,845 |
| OOS | 15 | `volume` | ret | 0.0260 | 151,845 |
| OOS | 15 | `absret_1m` | rv | 0.4684 | 151,845 |
| OOS | 15 | `absret_per_vol` | rv | 0.1463 | 151,845 |
| OOS | 15 | `ret_1m` | rv | -0.0284 | 151,845 |
| OOS | 15 | `signed_vol_proxy` | rv | -0.0249 | 151,845 |
| OOS | 15 | `signed_vol_proxy_resid` | rv | -0.0056 | 151,845 |
| OOS | 15 | `signed_vol_proxy_sum_5` | rv | -0.0599 | 150,197 |
| OOS | 15 | `vol_x_range` | rv | 0.7285 | 151,845 |
| OOS | 15 | `vol_z_tod` | rv | 0.4806 | 151,845 |
| OOS | 15 | `volume` | rv | 0.5989 | 151,845 |
| OOS | 30 | `absret_1m` | absret | 0.2660 | 145,665 |
| OOS | 30 | `absret_per_vol` | absret | 0.0876 | 145,665 |
| OOS | 30 | `ret_1m` | absret | -0.0149 | 145,665 |
| OOS | 30 | `signed_vol_proxy` | absret | -0.0134 | 145,665 |
| OOS | 30 | `signed_vol_proxy_resid` | absret | -0.0027 | 145,665 |
| OOS | 30 | `signed_vol_proxy_sum_5` | absret | -0.0346 | 144,017 |
| OOS | 30 | `vol_x_range` | absret | 0.4073 | 145,665 |
| OOS | 30 | `vol_z_tod` | absret | 0.2705 | 145,665 |
| OOS | 30 | `volume` | absret | 0.3313 | 145,665 |
| OOS | 30 | `absret_1m` | ret | 0.0205 | 145,665 |
| OOS | 30 | `absret_per_vol` | ret | 0.0021 | 145,665 |
| OOS | 30 | `ret_1m` | ret | -0.0050 | 145,665 |
| OOS | 30 | `signed_vol_proxy` | ret | -0.0019 | 145,665 |
| OOS | 30 | `signed_vol_proxy_resid` | ret | 0.0015 | 145,665 |
| OOS | 30 | `signed_vol_proxy_sum_5` | ret | -0.0009 | 144,017 |
| OOS | 30 | `vol_x_range` | ret | 0.0336 | 145,665 |
| OOS | 30 | `vol_z_tod` | ret | 0.0216 | 145,665 |
| OOS | 30 | `volume` | ret | 0.0326 | 145,665 |
| OOS | 30 | `absret_1m` | rv | 0.4749 | 145,665 |
| OOS | 30 | `absret_per_vol` | rv | 0.1538 | 145,665 |
| OOS | 30 | `ret_1m` | rv | -0.0275 | 145,665 |
| OOS | 30 | `signed_vol_proxy` | rv | -0.0240 | 145,665 |
| OOS | 30 | `signed_vol_proxy_resid` | rv | -0.0050 | 145,665 |
| OOS | 30 | `signed_vol_proxy_sum_5` | rv | -0.0597 | 144,017 |
| OOS | 30 | `vol_x_range` | rv | 0.7334 | 145,665 |
| OOS | 30 | `vol_z_tod` | rv | 0.4802 | 145,665 |
| OOS | 30 | `volume` | rv | 0.5976 | 145,665 |
| Validation | 5 | `absret_1m` | absret | 0.2340 | 293,220 |
| Validation | 5 | `absret_per_vol` | absret | 0.0803 | 293,220 |
| Validation | 5 | `ret_1m` | absret | -0.0173 | 293,220 |
| Validation | 5 | `signed_vol_proxy` | absret | -0.0158 | 293,220 |
| Validation | 5 | `signed_vol_proxy_resid` | absret | -0.0074 | 293,220 |
| Validation | 5 | `signed_vol_proxy_sum_5` | absret | -0.0320 | 290,124 |
| Validation | 5 | `vol_x_range` | absret | 0.3571 | 293,220 |
| Validation | 5 | `vol_z_tod` | absret | 0.2027 | 293,220 |
| Validation | 5 | `volume` | absret | 0.2712 | 293,220 |
| Validation | 5 | `absret_1m` | ret | -0.0007 | 293,220 |
| Validation | 5 | `absret_per_vol` | ret | -0.0010 | 293,220 |
| Validation | 5 | `ret_1m` | ret | -0.0038 | 293,220 |
| Validation | 5 | `signed_vol_proxy` | ret | -0.0044 | 293,220 |
| Validation | 5 | `signed_vol_proxy_resid` | ret | -0.0069 | 293,220 |
| Validation | 5 | `signed_vol_proxy_sum_5` | ret | -0.0085 | 290,124 |
| Validation | 5 | `vol_x_range` | ret | -0.0014 | 293,220 |
| Validation | 5 | `vol_z_tod` | ret | -0.0015 | 293,220 |
| Validation | 5 | `volume` | ret | -0.0008 | 293,220 |
| Validation | 5 | `absret_1m` | rv | 0.3694 | 293,220 |
| Validation | 5 | `absret_per_vol` | rv | 0.1271 | 293,220 |
| Validation | 5 | `ret_1m` | rv | -0.0305 | 293,220 |
| Validation | 5 | `signed_vol_proxy` | rv | -0.0272 | 293,220 |
| Validation | 5 | `signed_vol_proxy_resid` | rv | -0.0122 | 293,220 |
| Validation | 5 | `signed_vol_proxy_sum_5` | rv | -0.0518 | 290,124 |
| Validation | 5 | `vol_x_range` | rv | 0.5759 | 293,220 |
| Validation | 5 | `vol_z_tod` | rv | 0.3238 | 293,220 |
| Validation | 5 | `volume` | rv | 0.4320 | 293,220 |
| Validation | 15 | `absret_1m` | absret | 0.2242 | 285,480 |
| Validation | 15 | `absret_per_vol` | absret | 0.0794 | 285,480 |
| Validation | 15 | `ret_1m` | absret | -0.0159 | 285,480 |
| Validation | 15 | `signed_vol_proxy` | absret | -0.0151 | 285,480 |
| Validation | 15 | `signed_vol_proxy_resid` | absret | -0.0072 | 285,480 |
| Validation | 15 | `signed_vol_proxy_sum_5` | absret | -0.0318 | 282,384 |
| Validation | 15 | `vol_x_range` | absret | 0.3446 | 285,480 |
| Validation | 15 | `vol_z_tod` | absret | 0.1881 | 285,480 |
| Validation | 15 | `volume` | absret | 0.2567 | 285,480 |
| Validation | 15 | `absret_1m` | ret | 0.0002 | 285,480 |
| Validation | 15 | `absret_per_vol` | ret | 0.0017 | 285,480 |
| Validation | 15 | `ret_1m` | ret | 0.0036 | 285,480 |
| Validation | 15 | `signed_vol_proxy` | ret | 0.0021 | 285,480 |
| Validation | 15 | `signed_vol_proxy_resid` | ret | -0.0019 | 285,480 |
| Validation | 15 | `signed_vol_proxy_sum_5` | ret | 0.0019 | 282,384 |
| Validation | 15 | `vol_x_range` | ret | -0.0019 | 285,480 |
| Validation | 15 | `vol_z_tod` | ret | -0.0034 | 285,480 |
| Validation | 15 | `volume` | ret | -0.0023 | 285,480 |
| Validation | 15 | `absret_1m` | rv | 0.4213 | 285,480 |
| Validation | 15 | `absret_per_vol` | rv | 0.1555 | 285,480 |
| Validation | 15 | `ret_1m` | rv | -0.0269 | 285,480 |
| Validation | 15 | `signed_vol_proxy` | rv | -0.0243 | 285,480 |
| Validation | 15 | `signed_vol_proxy_resid` | rv | -0.0097 | 285,480 |
| Validation | 15 | `signed_vol_proxy_sum_5` | rv | -0.0533 | 282,384 |
| Validation | 15 | `vol_x_range` | rv | 0.6525 | 285,480 |
| Validation | 15 | `vol_z_tod` | rv | 0.3582 | 285,480 |
| Validation | 15 | `volume` | rv | 0.4800 | 285,480 |
| Validation | 30 | `absret_1m` | absret | 0.2199 | 273,870 |
| Validation | 30 | `absret_per_vol` | absret | 0.0801 | 273,870 |
| Validation | 30 | `ret_1m` | absret | -0.0123 | 273,870 |
| Validation | 30 | `signed_vol_proxy` | absret | -0.0116 | 273,870 |
| Validation | 30 | `signed_vol_proxy_resid` | absret | -0.0034 | 273,870 |
| Validation | 30 | `signed_vol_proxy_sum_5` | absret | -0.0267 | 270,774 |
| Validation | 30 | `vol_x_range` | absret | 0.3369 | 273,870 |
| Validation | 30 | `vol_z_tod` | absret | 0.1828 | 273,870 |
| Validation | 30 | `volume` | absret | 0.2475 | 273,870 |
| Validation | 30 | `absret_1m` | ret | 0.0009 | 273,870 |
| Validation | 30 | `absret_per_vol` | ret | 0.0038 | 273,870 |
| Validation | 30 | `ret_1m` | ret | 0.0034 | 273,870 |
| Validation | 30 | `signed_vol_proxy` | ret | 0.0028 | 273,870 |
| Validation | 30 | `signed_vol_proxy_resid` | ret | 0.0005 | 273,870 |
| Validation | 30 | `signed_vol_proxy_sum_5` | ret | 0.0071 | 270,774 |
| Validation | 30 | `vol_x_range` | ret | -0.0019 | 273,870 |
| Validation | 30 | `vol_z_tod` | ret | -0.0058 | 273,870 |
| Validation | 30 | `volume` | ret | -0.0025 | 273,870 |
| Validation | 30 | `absret_1m` | rv | 0.4307 | 273,870 |
| Validation | 30 | `absret_per_vol` | rv | 0.1651 | 273,870 |
| Validation | 30 | `ret_1m` | rv | -0.0244 | 273,870 |
| Validation | 30 | `signed_vol_proxy` | rv | -0.0225 | 273,870 |
| Validation | 30 | `signed_vol_proxy_resid` | rv | -0.0086 | 273,870 |
| Validation | 30 | `signed_vol_proxy_sum_5` | rv | -0.0524 | 270,774 |
| Validation | 30 | `vol_x_range` | rv | 0.6606 | 273,870 |
| Validation | 30 | `vol_z_tod` | rv | 0.3608 | 273,870 |
| Validation | 30 | `volume` | rv | 0.4799 | 273,870 |

## Proxy vs disguised-return check (target=ret, H=15)

### Discovery

- `ret_1m`: Spearman=-0.0066 (n=889,561)
- `signed_vol_proxy`: Spearman=-0.0051 (n=889,561)
- `signed_vol_proxy_resid`: Spearman=-0.0010 (n=889,561)
- `volume`: Spearman=0.0142 (n=889,615)
- `vol_z_tod`: Spearman=0.0095 (n=889,615)

### Validation

- `ret_1m`: Spearman=0.0036 (n=285,480)
- `signed_vol_proxy`: Spearman=0.0021 (n=285,480)
- `signed_vol_proxy_resid`: Spearman=-0.0019 (n=285,480)
- `volume`: Spearman=-0.0023 (n=285,480)
- `vol_z_tod`: Spearman=-0.0034 (n=285,480)

### OOS

- `ret_1m`: Spearman=-0.0027 (n=151,845)
- `signed_vol_proxy`: Spearman=-0.0014 (n=151,845)
- `signed_vol_proxy_resid`: Spearman=0.0001 (n=151,845)
- `volume`: Spearman=0.0260 (n=151,845)
- `vol_z_tod`: Spearman=0.0183 (n=151,845)

## Interpretation gate (descriptive only)

- If `signed_vol_proxy` tracks future returns similarly to `ret_1m`, and `signed_vol_proxy_resid` collapses toward ~0 association, the proxy is largely a **relabeled return transform** — do not call it order-flow information.
- Unsigned `volume` / `vol_z_tod` associations with future `|ret|`/`rv` are activity/vol state, not signed pressure.
- Phase 2 delta-R2 only if residuals or unsigned activity show non-trivial, stable descriptive signal beyond raw return/range.

Artifacts: `phase1_panel_nq.parquet`, `phase1_spearman_nq.csv`, `phase1_conditional_terciles_nq.csv`.
