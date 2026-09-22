# Event C Report — Extreme Excursion → Rejection

**Family 4 only. Path-first. No Event A/B rescue. No horizon shopping.**

## Funnel

- Excursion onsets: 93133
- Events (rejection): 71344
- Censored: 21789

## Freeze / audit

```text
LOOKAHEAD_CHECK = PASS
EVENT_DEFINITION_FROZEN = True
NO_PARAMETER_RETUNE = True
NO_EVENT_AB_COMBINE = True
NO_HORIZON_PNL_SHOP = True
```

## Destination asymmetry

| horizon | split | n_valid | p_anchor | p_extreme | p_through | delta_anchor_minus_extreme |
| --- | --- | --- | --- | --- | --- | --- |
| 5 | IS | 47537 | 0.3798 | 0.4138 | 0.2019 | -0.0341 |
| 5 | Validation | 14393 | 0.3709 | 0.3839 | 0.1970 | -0.0129 |
| 5 | OOS | 8094 | 0.3669 | 0.3931 | 0.1934 | -0.0262 |
| 5 | ALL | 70024 | 0.3765 | 0.4053 | 0.1999 | -0.0288 |
| 15 | IS | 45869 | 0.5917 | 0.6196 | 0.4203 | -0.0279 |
| 15 | Validation | 13756 | 0.5874 | 0.5923 | 0.4154 | -0.0049 |
| 15 | OOS | 7756 | 0.5766 | 0.6093 | 0.4085 | -0.0327 |
| 15 | ALL | 67381 | 0.5891 | 0.6129 | 0.4179 | -0.0238 |
| 30 | IS | 43605 | 0.7004 | 0.7148 | 0.5577 | -0.0144 |
| 30 | Validation | 13044 | 0.7049 | 0.6924 | 0.5596 | 0.0125 |
| 30 | OOS | 7359 | 0.6824 | 0.7063 | 0.5365 | -0.0239 |
| 30 | ALL | 64008 | 0.6992 | 0.7093 | 0.5556 | -0.0100 |
| 60 | IS | 39142 | 0.7763 | 0.7856 | 0.6645 | -0.0093 |
| 60 | Validation | 11762 | 0.7846 | 0.7625 | 0.6783 | 0.0221 |
| 60 | OOS | 6615 | 0.7574 | 0.7766 | 0.6369 | -0.0192 |
| 60 | ALL | 57519 | 0.7758 | 0.7798 | 0.6641 | -0.0040 |

## Step 1 / 2 — Destination verdict

- **Classification:** `KILL`
- **Stage:** `STEP1`
- **Reason:** `IS_delta_not_material_or_wrong_sign`

## Step 3 — Path

Not run (destination did not advance).

## Step 6 — Trade

Not run.

## EVENT C FINAL

**KILL**. Do not retune. Do not reopen Event A/B.
