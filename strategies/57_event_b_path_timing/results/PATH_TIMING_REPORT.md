# Path Timing Report — Event B (Strategy 57)

**Path/timing only.** No P&L. No horizon shopping. Not a monetization rescue.

## Freeze / audit

```text
LOOKAHEAD_CHECK = PASS
EVENT_DEFINITION_FROZEN = True
NO_PARAMETER_RETUNE = True
NO_HORIZON_PNL_SHOP = True
NO_TRADE_IN_THIS_RUN = True
```

Predicted side (inherited): `toward_rebreak`

## Primary ladder — `prog_close[H] = side × (close[t+H] − close[t]) / R`

| split | horizon | n | med | mean | p_pos | p_hit_rebreak | med_mfe | med_mae |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| IS | 5 | 40094 | -0.0039 | 0.0009 | 0.4634 | 0.2161 | 0.1141 | 0.1140 |
| IS | 15 | 38444 | -0.0097 | 0.0015 | 0.4738 | 0.4223 | 0.1980 | 0.1941 |
| IS | 30 | 36201 | -0.0154 | -0.0010 | 0.4786 | 0.5513 | 0.2769 | 0.2747 |
| IS | 60 | 31883 | -0.0135 | 0.0037 | 0.4832 | 0.6574 | 0.3818 | 0.3793 |
| Validation | 5 | 14578 | -0.0022 | -0.0007 | 0.4901 | 0.1961 | 0.1066 | 0.1111 |
| Validation | 15 | 14012 | 0.0026 | 0.0016 | 0.5014 | 0.3902 | 0.1853 | 0.1858 |
| Validation | 30 | 13316 | 0.0075 | 0.0046 | 0.5066 | 0.5272 | 0.2635 | 0.2621 |
| Validation | 60 | 11851 | 0.0273 | 0.0294 | 0.5185 | 0.6525 | 0.3717 | 0.3584 |
| OOS | 5 | 7570 | 0.0008 | -0.0036 | 0.5003 | 0.2024 | 0.1142 | 0.1198 |
| OOS | 15 | 7230 | -0.0048 | -0.0050 | 0.4927 | 0.3929 | 0.1899 | 0.1997 |
| OOS | 30 | 6867 | 0.0000 | -0.0083 | 0.4977 | 0.5261 | 0.2639 | 0.2750 |
| OOS | 60 | 6129 | 0.0025 | -0.0006 | 0.5014 | 0.6355 | 0.3519 | 0.3708 |
| ALL | 5 | 62242 | -0.0019 | 0.0000 | 0.4742 | 0.2098 | 0.1120 | 0.1139 |
| ALL | 15 | 59686 | -0.0048 | 0.0007 | 0.4826 | 0.4112 | 0.1937 | 0.1927 |
| ALL | 30 | 56384 | -0.0064 | -0.0005 | 0.4875 | 0.5426 | 0.2722 | 0.2722 |
| ALL | 60 | 49863 | 0.0000 | 0.0092 | 0.4939 | 0.6536 | 0.3761 | 0.3740 |

## First rebreak timing (descriptive)

| split | n_h60_valid | n_hit_by_60 | med_first_bars | p25 | p75 |
| --- | --- | --- | --- | --- | --- |
| IS | 31883 | 20960 | 11.0 | 4.0 | 23.0 |
| Validation | 11851 | 7733 | 12.0 | 5.0 | 26.0 |
| OOS | 6129 | 3895 | 11.0 | 5.0 | 25.0 |
| ALL | 49863 | 32588 | 11.0 | 5.0 | 24.0 |

## Gate detail

- **IS**: n_ok=True, mono=False, med60_pos=False, mid_ladder_pos=False; medians [5:-0.0039 → 15:-0.0097 → 30:-0.0154 → 60:-0.0135]
- **Validation**: n_ok=True, mono=True, med60_pos=True, mid_ladder_pos=True; medians [5:-0.0022 → 15:0.0026 → 30:0.0075 → 60:0.0273]
- **OOS**: n_ok=True, mono=False, med60_pos=True, mid_ladder_pos=False; medians [5:0.0008 → 15:-0.0048 → 30:0.0000 → 60:0.0025]

## Verdict

- **Classification:** `PATH_KILL`
- **Stage:** `STEP1`
- **Reason:** `IS_med60_not_pos+IS_not_monotonic+IS_mid_ladder_not_pos`

Path KILL. **Do not shop horizons for P&L.** Do not retune Event B. Do not open Family 3/4 as a rescue.
