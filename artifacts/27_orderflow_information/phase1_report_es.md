# Strategy 27 — Phase 1 descriptives (ES)

**PROXY STUDY - NOT ORDER FLOW.** No delta-R2. No rules.

- Panel rows (RTH): **1,387,354**
- Residual OLS (Discovery): {"intercept": 77.37232716720933, "ret_1m": 7423804.886056306, "absret_1m": -163192.64449165203, "range_pct": -100183.14452770166, "n_fit": 927123}

## Headline Spearman (Validation + OOS emphasis)

Compare `signed_vol_proxy` vs `signed_vol_proxy_resid` vs raw `ret_1m` / `volume`.

| Split | H | Feature | Target | Spearman | n |
|-------|---|---------|--------|----------|---|
| Discovery | 5 | `absret_1m` | absret | 0.2517 | 914,875 |
| Discovery | 5 | `absret_per_vol` | absret | 0.0415 | 914,875 |
| Discovery | 5 | `ret_1m` | absret | -0.0165 | 914,875 |
| Discovery | 5 | `signed_vol_proxy` | absret | -0.0157 | 914,875 |
| Discovery | 5 | `signed_vol_proxy_resid` | absret | 0.0151 | 914,875 |
| Discovery | 5 | `signed_vol_proxy_sum_5` | absret | -0.0350 | 905,104 |
| Discovery | 5 | `vol_x_range` | absret | 0.3856 | 914,912 |
| Discovery | 5 | `vol_z_tod` | absret | 0.2628 | 914,912 |
| Discovery | 5 | `volume` | absret | 0.3180 | 914,912 |
| Discovery | 5 | `absret_1m` | ret | 0.0019 | 914,875 |
| Discovery | 5 | `absret_per_vol` | ret | 0.0018 | 914,875 |
| Discovery | 5 | `ret_1m` | ret | -0.0408 | 914,875 |
| Discovery | 5 | `signed_vol_proxy` | ret | -0.0351 | 914,875 |
| Discovery | 5 | `signed_vol_proxy_resid` | ret | -0.0049 | 914,875 |
| Discovery | 5 | `signed_vol_proxy_sum_5` | ret | -0.0305 | 905,104 |
| Discovery | 5 | `vol_x_range` | ret | 0.0015 | 914,912 |
| Discovery | 5 | `vol_z_tod` | ret | -0.0012 | 914,912 |
| Discovery | 5 | `volume` | ret | -0.0001 | 914,912 |
| Discovery | 5 | `absret_1m` | rv | 0.3759 | 914,875 |
| Discovery | 5 | `absret_per_vol` | rv | 0.0569 | 914,875 |
| Discovery | 5 | `ret_1m` | rv | -0.0233 | 914,875 |
| Discovery | 5 | `signed_vol_proxy` | rv | -0.0227 | 914,875 |
| Discovery | 5 | `signed_vol_proxy_resid` | rv | 0.0215 | 914,875 |
| Discovery | 5 | `signed_vol_proxy_sum_5` | rv | -0.0512 | 905,104 |
| Discovery | 5 | `vol_x_range` | rv | 0.5766 | 914,912 |
| Discovery | 5 | `vol_z_tod` | rv | 0.3984 | 914,912 |
| Discovery | 5 | `volume` | rv | 0.4755 | 914,912 |
| Discovery | 15 | `absret_1m` | absret | 0.2493 | 890,478 |
| Discovery | 15 | `absret_per_vol` | absret | 0.0445 | 890,478 |
| Discovery | 15 | `ret_1m` | absret | -0.0146 | 890,478 |
| Discovery | 15 | `signed_vol_proxy` | absret | -0.0137 | 890,478 |
| Discovery | 15 | `signed_vol_proxy_resid` | absret | 0.0170 | 890,478 |
| Discovery | 15 | `signed_vol_proxy_sum_5` | absret | -0.0307 | 880,742 |
| Discovery | 15 | `vol_x_range` | absret | 0.3814 | 890,504 |
| Discovery | 15 | `vol_z_tod` | absret | 0.2609 | 890,504 |
| Discovery | 15 | `volume` | absret | 0.3118 | 890,504 |
| Discovery | 15 | `absret_1m` | ret | 0.0066 | 890,478 |
| Discovery | 15 | `absret_per_vol` | ret | 0.0020 | 890,478 |
| Discovery | 15 | `ret_1m` | ret | -0.0231 | 890,478 |
| Discovery | 15 | `signed_vol_proxy` | ret | -0.0201 | 890,478 |
| Discovery | 15 | `signed_vol_proxy_resid` | ret | -0.0028 | 890,478 |
| Discovery | 15 | `signed_vol_proxy_sum_5` | ret | -0.0187 | 880,742 |
| Discovery | 15 | `vol_x_range` | ret | 0.0094 | 890,504 |
| Discovery | 15 | `vol_z_tod` | ret | 0.0035 | 890,504 |
| Discovery | 15 | `volume` | ret | 0.0069 | 890,504 |
| Discovery | 15 | `absret_1m` | rv | 0.4311 | 890,478 |
| Discovery | 15 | `absret_per_vol` | rv | 0.0678 | 890,478 |
| Discovery | 15 | `ret_1m` | rv | -0.0237 | 890,478 |
| Discovery | 15 | `signed_vol_proxy` | rv | -0.0235 | 890,478 |
| Discovery | 15 | `signed_vol_proxy_resid` | rv | 0.0264 | 890,478 |
| Discovery | 15 | `signed_vol_proxy_sum_5` | rv | -0.0547 | 880,742 |
| Discovery | 15 | `vol_x_range` | rv | 0.6616 | 890,504 |
| Discovery | 15 | `vol_z_tod` | rv | 0.4582 | 890,504 |
| Discovery | 15 | `volume` | rv | 0.5422 | 890,504 |
| Discovery | 30 | `absret_1m` | absret | 0.2448 | 854,008 |
| Discovery | 30 | `absret_per_vol` | absret | 0.0462 | 854,008 |
| Discovery | 30 | `ret_1m` | absret | -0.0163 | 854,008 |
| Discovery | 30 | `signed_vol_proxy` | absret | -0.0158 | 854,008 |
| Discovery | 30 | `signed_vol_proxy_resid` | absret | 0.0152 | 854,008 |
| Discovery | 30 | `signed_vol_proxy_sum_5` | absret | -0.0335 | 844,296 |
| Discovery | 30 | `vol_x_range` | absret | 0.3715 | 854,027 |
| Discovery | 30 | `vol_z_tod` | absret | 0.2555 | 854,027 |
| Discovery | 30 | `volume` | absret | 0.3010 | 854,027 |
| Discovery | 30 | `absret_1m` | ret | 0.0105 | 854,008 |
| Discovery | 30 | `absret_per_vol` | ret | 0.0023 | 854,008 |
| Discovery | 30 | `ret_1m` | ret | -0.0148 | 854,008 |
| Discovery | 30 | `signed_vol_proxy` | ret | -0.0131 | 854,008 |
| Discovery | 30 | `signed_vol_proxy_resid` | ret | -0.0007 | 854,008 |
| Discovery | 30 | `signed_vol_proxy_sum_5` | ret | -0.0116 | 844,296 |
| Discovery | 30 | `vol_x_range` | ret | 0.0154 | 854,027 |
| Discovery | 30 | `vol_z_tod` | ret | 0.0064 | 854,027 |
| Discovery | 30 | `volume` | ret | 0.0126 | 854,027 |
| Discovery | 30 | `absret_1m` | rv | 0.4395 | 854,008 |
| Discovery | 30 | `absret_per_vol` | rv | 0.0721 | 854,008 |
| Discovery | 30 | `ret_1m` | rv | -0.0229 | 854,008 |
| Discovery | 30 | `signed_vol_proxy` | rv | -0.0228 | 854,008 |
| Discovery | 30 | `signed_vol_proxy_resid` | rv | 0.0275 | 854,008 |
| Discovery | 30 | `signed_vol_proxy_sum_5` | rv | -0.0532 | 844,296 |
| Discovery | 30 | `vol_x_range` | rv | 0.6707 | 854,027 |
| Discovery | 30 | `vol_z_tod` | rv | 0.4689 | 854,027 |
| Discovery | 30 | `volume` | rv | 0.5460 | 854,027 |
| OOS | 5 | `absret_1m` | absret | 0.2623 | 160,956 |
| OOS | 5 | `absret_per_vol` | absret | 0.0679 | 160,956 |
| OOS | 5 | `ret_1m` | absret | -0.0160 | 160,956 |
| OOS | 5 | `signed_vol_proxy` | absret | -0.0147 | 160,956 |
| OOS | 5 | `signed_vol_proxy_resid` | absret | 0.0095 | 160,956 |
| OOS | 5 | `signed_vol_proxy_sum_5` | absret | -0.0243 | 159,248 |
| OOS | 5 | `vol_x_range` | absret | 0.4167 | 160,958 |
| OOS | 5 | `vol_z_tod` | absret | 0.2698 | 160,958 |
| OOS | 5 | `volume` | absret | 0.3489 | 160,958 |
| OOS | 5 | `absret_1m` | ret | 0.0111 | 160,956 |
| OOS | 5 | `absret_per_vol` | ret | 0.0018 | 160,956 |
| OOS | 5 | `ret_1m` | ret | -0.0092 | 160,956 |
| OOS | 5 | `signed_vol_proxy` | ret | -0.0076 | 160,956 |
| OOS | 5 | `signed_vol_proxy_resid` | ret | -0.0022 | 160,956 |
| OOS | 5 | `signed_vol_proxy_sum_5` | ret | -0.0026 | 159,248 |
| OOS | 5 | `vol_x_range` | ret | 0.0166 | 160,958 |
| OOS | 5 | `vol_z_tod` | ret | 0.0090 | 160,958 |
| OOS | 5 | `volume` | ret | 0.0159 | 160,958 |
| OOS | 5 | `absret_1m` | rv | 0.4030 | 160,956 |
| OOS | 5 | `absret_per_vol` | rv | 0.0967 | 160,956 |
| OOS | 5 | `ret_1m` | rv | -0.0264 | 160,956 |
| OOS | 5 | `signed_vol_proxy` | rv | -0.0216 | 160,956 |
| OOS | 5 | `signed_vol_proxy_resid` | rv | 0.0142 | 160,956 |
| OOS | 5 | `signed_vol_proxy_sum_5` | rv | -0.0448 | 159,248 |
| OOS | 5 | `vol_x_range` | rv | 0.6489 | 160,958 |
| OOS | 5 | `vol_z_tod` | rv | 0.4293 | 160,958 |
| OOS | 5 | `volume` | rv | 0.5478 | 160,958 |
| OOS | 15 | `absret_1m` | absret | 0.2595 | 156,686 |
| OOS | 15 | `absret_per_vol` | absret | 0.0699 | 156,686 |
| OOS | 15 | `ret_1m` | absret | -0.0152 | 156,686 |
| OOS | 15 | `signed_vol_proxy` | absret | -0.0147 | 156,686 |
| OOS | 15 | `signed_vol_proxy_resid` | absret | 0.0046 | 156,686 |
| OOS | 15 | `signed_vol_proxy_sum_5` | absret | -0.0304 | 154,978 |
| OOS | 15 | `vol_x_range` | absret | 0.4142 | 156,688 |
| OOS | 15 | `vol_z_tod` | absret | 0.2649 | 156,688 |
| OOS | 15 | `volume` | absret | 0.3443 | 156,688 |
| OOS | 15 | `absret_1m` | ret | 0.0155 | 156,686 |
| OOS | 15 | `absret_per_vol` | ret | 0.0046 | 156,686 |
| OOS | 15 | `ret_1m` | ret | -0.0038 | 156,686 |
| OOS | 15 | `signed_vol_proxy` | ret | -0.0029 | 156,686 |
| OOS | 15 | `signed_vol_proxy_resid` | ret | 0.0008 | 156,686 |
| OOS | 15 | `signed_vol_proxy_sum_5` | ret | 0.0056 | 154,978 |
| OOS | 15 | `vol_x_range` | ret | 0.0212 | 156,688 |
| OOS | 15 | `vol_z_tod` | ret | 0.0114 | 156,688 |
| OOS | 15 | `volume` | ret | 0.0204 | 156,688 |
| OOS | 15 | `absret_1m` | rv | 0.4576 | 156,686 |
| OOS | 15 | `absret_per_vol` | rv | 0.1184 | 156,686 |
| OOS | 15 | `ret_1m` | rv | -0.0273 | 156,686 |
| OOS | 15 | `signed_vol_proxy` | rv | -0.0232 | 156,686 |
| OOS | 15 | `signed_vol_proxy_resid` | rv | 0.0158 | 156,686 |
| OOS | 15 | `signed_vol_proxy_sum_5` | rv | -0.0518 | 154,978 |
| OOS | 15 | `vol_x_range` | rv | 0.7326 | 156,688 |
| OOS | 15 | `vol_z_tod` | rv | 0.4756 | 156,688 |
| OOS | 15 | `volume` | rv | 0.6138 | 156,688 |
| OOS | 30 | `absret_1m` | absret | 0.2522 | 150,289 |
| OOS | 30 | `absret_per_vol` | absret | 0.0691 | 150,289 |
| OOS | 30 | `ret_1m` | absret | -0.0149 | 150,289 |
| OOS | 30 | `signed_vol_proxy` | absret | -0.0130 | 150,289 |
| OOS | 30 | `signed_vol_proxy_resid` | absret | 0.0092 | 150,289 |
| OOS | 30 | `signed_vol_proxy_sum_5` | absret | -0.0276 | 148,585 |
| OOS | 30 | `vol_x_range` | absret | 0.4008 | 150,290 |
| OOS | 30 | `vol_z_tod` | absret | 0.2575 | 150,290 |
| OOS | 30 | `volume` | absret | 0.3313 | 150,290 |
| OOS | 30 | `absret_1m` | ret | 0.0198 | 150,289 |
| OOS | 30 | `absret_per_vol` | ret | 0.0041 | 150,289 |
| OOS | 30 | `ret_1m` | ret | -0.0032 | 150,289 |
| OOS | 30 | `signed_vol_proxy` | ret | -0.0013 | 150,289 |
| OOS | 30 | `signed_vol_proxy_resid` | ret | 0.0041 | 150,289 |
| OOS | 30 | `signed_vol_proxy_sum_5` | ret | 0.0050 | 148,585 |
| OOS | 30 | `vol_x_range` | ret | 0.0284 | 150,290 |
| OOS | 30 | `vol_z_tod` | ret | 0.0163 | 150,290 |
| OOS | 30 | `volume` | ret | 0.0284 | 150,290 |
| OOS | 30 | `absret_1m` | rv | 0.4650 | 150,289 |
| OOS | 30 | `absret_per_vol` | rv | 0.1248 | 150,289 |
| OOS | 30 | `ret_1m` | rv | -0.0267 | 150,289 |
| OOS | 30 | `signed_vol_proxy` | rv | -0.0221 | 150,289 |
| OOS | 30 | `signed_vol_proxy_resid` | rv | 0.0170 | 150,289 |
| OOS | 30 | `signed_vol_proxy_sum_5` | rv | -0.0499 | 148,585 |
| OOS | 30 | `vol_x_range` | rv | 0.7391 | 150,290 |
| OOS | 30 | `vol_z_tod` | rv | 0.4778 | 150,290 |
| OOS | 30 | `volume` | rv | 0.6141 | 150,290 |
| Validation | 5 | `absret_1m` | absret | 0.2425 | 293,220 |
| Validation | 5 | `absret_per_vol` | absret | 0.0629 | 293,220 |
| Validation | 5 | `ret_1m` | absret | -0.0150 | 293,220 |
| Validation | 5 | `signed_vol_proxy` | absret | -0.0101 | 293,220 |
| Validation | 5 | `signed_vol_proxy_resid` | absret | 0.0112 | 293,220 |
| Validation | 5 | `signed_vol_proxy_sum_5` | absret | -0.0247 | 290,124 |
| Validation | 5 | `vol_x_range` | absret | 0.3759 | 293,220 |
| Validation | 5 | `vol_z_tod` | absret | 0.2538 | 293,220 |
| Validation | 5 | `volume` | absret | 0.3050 | 293,220 |
| Validation | 5 | `absret_1m` | ret | 0.0007 | 293,220 |
| Validation | 5 | `absret_per_vol` | ret | 0.0024 | 293,220 |
| Validation | 5 | `ret_1m` | ret | -0.0115 | 293,220 |
| Validation | 5 | `signed_vol_proxy` | ret | -0.0128 | 293,220 |
| Validation | 5 | `signed_vol_proxy_resid` | ret | -0.0111 | 293,220 |
| Validation | 5 | `signed_vol_proxy_sum_5` | ret | -0.0133 | 290,124 |
| Validation | 5 | `vol_x_range` | ret | -0.0022 | 293,220 |
| Validation | 5 | `vol_z_tod` | ret | -0.0049 | 293,220 |
| Validation | 5 | `volume` | ret | -0.0035 | 293,220 |
| Validation | 5 | `absret_1m` | rv | 0.3827 | 293,220 |
| Validation | 5 | `absret_per_vol` | rv | 0.0943 | 293,220 |
| Validation | 5 | `ret_1m` | rv | -0.0250 | 293,220 |
| Validation | 5 | `signed_vol_proxy` | rv | -0.0187 | 293,220 |
| Validation | 5 | `signed_vol_proxy_resid` | rv | 0.0162 | 293,220 |
| Validation | 5 | `signed_vol_proxy_sum_5` | rv | -0.0382 | 290,124 |
| Validation | 5 | `vol_x_range` | rv | 0.6054 | 293,220 |
| Validation | 5 | `vol_z_tod` | rv | 0.4102 | 293,220 |
| Validation | 5 | `volume` | rv | 0.4936 | 293,220 |
| Validation | 15 | `absret_1m` | absret | 0.2349 | 285,480 |
| Validation | 15 | `absret_per_vol` | absret | 0.0664 | 285,480 |
| Validation | 15 | `ret_1m` | absret | -0.0117 | 285,480 |
| Validation | 15 | `signed_vol_proxy` | absret | -0.0075 | 285,480 |
| Validation | 15 | `signed_vol_proxy_resid` | absret | 0.0122 | 285,480 |
| Validation | 15 | `signed_vol_proxy_sum_5` | absret | -0.0216 | 282,384 |
| Validation | 15 | `vol_x_range` | absret | 0.3634 | 285,480 |
| Validation | 15 | `vol_z_tod` | absret | 0.2423 | 285,480 |
| Validation | 15 | `volume` | absret | 0.2901 | 285,480 |
| Validation | 15 | `absret_1m` | ret | 0.0029 | 285,480 |
| Validation | 15 | `absret_per_vol` | ret | 0.0044 | 285,480 |
| Validation | 15 | `ret_1m` | ret | -0.0018 | 285,480 |
| Validation | 15 | `signed_vol_proxy` | ret | -0.0036 | 285,480 |
| Validation | 15 | `signed_vol_proxy_resid` | ret | -0.0054 | 285,480 |
| Validation | 15 | `signed_vol_proxy_sum_5` | ret | -0.0020 | 282,384 |
| Validation | 15 | `vol_x_range` | ret | -0.0010 | 285,480 |
| Validation | 15 | `vol_z_tod` | ret | -0.0023 | 285,480 |
| Validation | 15 | `volume` | ret | -0.0028 | 285,480 |
| Validation | 15 | `absret_1m` | rv | 0.4307 | 285,480 |
| Validation | 15 | `absret_per_vol` | rv | 0.1145 | 285,480 |
| Validation | 15 | `ret_1m` | rv | -0.0225 | 285,480 |
| Validation | 15 | `signed_vol_proxy` | rv | -0.0170 | 285,480 |
| Validation | 15 | `signed_vol_proxy_resid` | rv | 0.0181 | 285,480 |
| Validation | 15 | `signed_vol_proxy_sum_5` | rv | -0.0396 | 282,384 |
| Validation | 15 | `vol_x_range` | rv | 0.6824 | 285,480 |
| Validation | 15 | `vol_z_tod` | rv | 0.4561 | 285,480 |
| Validation | 15 | `volume` | rv | 0.5481 | 285,480 |
| Validation | 30 | `absret_1m` | absret | 0.2302 | 273,870 |
| Validation | 30 | `absret_per_vol` | absret | 0.0650 | 273,870 |
| Validation | 30 | `ret_1m` | absret | -0.0107 | 273,870 |
| Validation | 30 | `signed_vol_proxy` | absret | -0.0075 | 273,870 |
| Validation | 30 | `signed_vol_proxy_resid` | absret | 0.0102 | 273,870 |
| Validation | 30 | `signed_vol_proxy_sum_5` | absret | -0.0176 | 270,774 |
| Validation | 30 | `vol_x_range` | absret | 0.3561 | 273,870 |
| Validation | 30 | `vol_z_tod` | absret | 0.2363 | 273,870 |
| Validation | 30 | `volume` | absret | 0.2812 | 273,870 |
| Validation | 30 | `absret_1m` | ret | 0.0044 | 273,870 |
| Validation | 30 | `absret_per_vol` | ret | 0.0060 | 273,870 |
| Validation | 30 | `ret_1m` | ret | 0.0002 | 273,870 |
| Validation | 30 | `signed_vol_proxy` | ret | -0.0029 | 273,870 |
| Validation | 30 | `signed_vol_proxy_resid` | ret | -0.0061 | 273,870 |
| Validation | 30 | `signed_vol_proxy_sum_5` | ret | 0.0034 | 270,774 |
| Validation | 30 | `vol_x_range` | ret | 0.0000 | 273,870 |
| Validation | 30 | `vol_z_tod` | ret | -0.0008 | 273,870 |
| Validation | 30 | `volume` | ret | -0.0020 | 273,870 |
| Validation | 30 | `absret_1m` | rv | 0.4398 | 273,870 |
| Validation | 30 | `absret_per_vol` | rv | 0.1224 | 273,870 |
| Validation | 30 | `ret_1m` | rv | -0.0202 | 273,870 |
| Validation | 30 | `signed_vol_proxy` | rv | -0.0152 | 273,870 |
| Validation | 30 | `signed_vol_proxy_resid` | rv | 0.0184 | 273,870 |
| Validation | 30 | `signed_vol_proxy_sum_5` | rv | -0.0376 | 270,774 |
| Validation | 30 | `vol_x_range` | rv | 0.6910 | 273,870 |
| Validation | 30 | `vol_z_tod` | rv | 0.4635 | 273,870 |
| Validation | 30 | `volume` | rv | 0.5489 | 273,870 |

## Proxy vs disguised-return check (target=ret, H=15)

### Discovery

- `ret_1m`: Spearman=-0.0231 (n=890,478)
- `signed_vol_proxy`: Spearman=-0.0201 (n=890,478)
- `signed_vol_proxy_resid`: Spearman=-0.0028 (n=890,478)
- `volume`: Spearman=0.0069 (n=890,504)
- `vol_z_tod`: Spearman=0.0035 (n=890,504)

### Validation

- `ret_1m`: Spearman=-0.0018 (n=285,480)
- `signed_vol_proxy`: Spearman=-0.0036 (n=285,480)
- `signed_vol_proxy_resid`: Spearman=-0.0054 (n=285,480)
- `volume`: Spearman=-0.0028 (n=285,480)
- `vol_z_tod`: Spearman=-0.0023 (n=285,480)

### OOS

- `ret_1m`: Spearman=-0.0038 (n=156,686)
- `signed_vol_proxy`: Spearman=-0.0029 (n=156,686)
- `signed_vol_proxy_resid`: Spearman=0.0008 (n=156,686)
- `volume`: Spearman=0.0204 (n=156,688)
- `vol_z_tod`: Spearman=0.0114 (n=156,688)

## Interpretation gate (descriptive only)

- If `signed_vol_proxy` tracks future returns similarly to `ret_1m`, and `signed_vol_proxy_resid` collapses toward ~0 association, the proxy is largely a **relabeled return transform** — do not call it order-flow information.
- Unsigned `volume` / `vol_z_tod` associations with future `|ret|`/`rv` are activity/vol state, not signed pressure.
- Phase 2 delta-R2 only if residuals or unsigned activity show non-trivial, stable descriptive signal beyond raw return/range.

Artifacts: `phase1_panel_es.parquet`, `phase1_spearman_es.csv`, `phase1_conditional_terciles_es.csv`.
