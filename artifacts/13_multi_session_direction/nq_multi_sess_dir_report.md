# Strategy 13 — Multi-session Direction (Phase B)

## Freeze

- Stop = Target = **0.25 × psr** (1R)
- Max hold primary **30m** (also 15/45)
- Entry: next open; stress **delay1**
- Costs primary **mid=1.0 pts** RT
- Same-bar ambiguity: **stop first**
- Sessions independent; order: LONDON → NY_PM → NY_AM → ASIA

## Primary card (HIGH_FOLLOW / HIGH_FADE, next_open, H30, mid cost)

### LONDON

| Family | IS n | IS win | IS E_net | Val E_net | OOS E_net | OOS win | Y25 E_net | Y26 E_net | Verdict |
|--------|------|--------|----------|-----------|-----------|---------|-----------|-----------|---------|
| HIGH_FOLLOW | 4055 | 42.0% | -0.92 | -0.88 | -0.30 | 46.0% | -0.49 | +0.19 | **NO_TRADE** |
| HIGH_FADE | 4055 | 46.1% | -1.08 | -1.12 | -1.70 | 51.3% | -1.51 | -2.19 | **NO_TRADE** |
| BLIND_FOLLOW | 11842 | 40.0% | -1.03 | -0.95 | -0.72 | 46.7% | -0.95 | -0.36 | **NO_TRADE** |
| BLIND_FADE | 11842 | 43.3% | -0.97 | -1.05 | -1.28 | 49.8% | -1.05 | -1.64 | **NO_TRADE** |

### NY_PM

| Family | IS n | IS win | IS E_net | Val E_net | OOS E_net | OOS win | Y25 E_net | Y26 E_net | Verdict |
|--------|------|--------|----------|-----------|-----------|---------|-----------|-----------|---------|
| HIGH_FOLLOW | 3959 | 44.5% | -0.79 | +0.10 | -1.02 | 49.3% | +0.40 | -4.07 | **NO_TRADE** |
| HIGH_FADE | 3959 | 45.2% | -1.22 | -2.18 | -0.98 | 49.6% | -2.40 | +2.07 | **NO_TRADE** |
| BLIND_FOLLOW | 11538 | 43.4% | -1.00 | -0.65 | -0.50 | 49.8% | +0.47 | -2.12 | **NO_TRADE** |
| BLIND_FADE | 11538 | 43.7% | -1.00 | -1.38 | -1.50 | 48.5% | -2.47 | +0.12 | **NO_TRADE** |

### NY_AM

| Family | IS n | IS win | IS E_net | Val E_net | OOS E_net | OOS win | Y25 E_net | Y26 E_net | Verdict |
|--------|------|--------|----------|-----------|-----------|---------|-----------|-----------|---------|
| HIGH_FOLLOW | 3269 | 49.1% | -0.83 | -0.42 | +0.35 | 52.6% | +0.58 | +0.00 | **NO_TRADE** |
| HIGH_FADE | 3269 | 50.0% | -1.19 | -1.62 | -2.35 | 47.4% | -2.58 | -2.00 | **NO_TRADE** |
| BLIND_FOLLOW | 9592 | 48.2% | -1.08 | +0.13 | -1.01 | 50.5% | -0.18 | -2.37 | **NO_TRADE** |
| BLIND_FADE | 9592 | 49.3% | -0.92 | -2.14 | -0.99 | 49.1% | -1.82 | +0.37 | **NO_TRADE** |

### ASIA

| Family | IS n | IS win | IS E_net | Val E_net | OOS E_net | OOS win | Y25 E_net | Y26 E_net | Verdict |
|--------|------|--------|----------|-----------|-----------|---------|-----------|-----------|---------|
| HIGH_FOLLOW | 4157 | 36.2% | -1.38 | -0.74 | +0.25 | 50.0% | -1.42 | +2.36 | **NO_TRADE** |
| HIGH_FADE | 4157 | 42.2% | -0.65 | -1.26 | -2.50 | 47.3% | -0.58 | -4.90 | **NO_TRADE** |
| BLIND_FOLLOW | 12050 | 35.1% | -1.32 | -0.91 | -0.17 | 48.8% | -1.24 | +1.60 | **NO_TRADE** |
| BLIND_FADE | 12050 | 39.6% | -0.70 | -1.09 | -1.96 | 46.7% | -0.76 | -3.93 | **NO_TRADE** |

## Cost sensitivity (HIGH families, H30, next_open, OOS E_net)

| Session | Family | tight | mid | wide |
|---------|--------|-------|-----|------|
| LONDON | HIGH_FOLLOW | +0.20 | -0.30 | -1.30 |
| LONDON | HIGH_FADE | -1.20 | -1.70 | -2.70 |
| NY_PM | HIGH_FOLLOW | -0.52 | -1.02 | -2.02 |
| NY_PM | HIGH_FADE | -0.48 | -0.98 | -1.98 |
| NY_AM | HIGH_FOLLOW | +0.85 | +0.35 | -0.65 |
| NY_AM | HIGH_FADE | -1.85 | -2.35 | -3.35 |
| ASIA | HIGH_FOLLOW | +0.75 | +0.25 | -0.75 |
| ASIA | HIGH_FADE | -2.00 | -2.50 | -3.50 |

## Entry delay stress (HIGH, H30, mid, OOS E_net)

| Session | Family | next_open | delay1 |
|---------|--------|-----------|--------|
| LONDON | HIGH_FOLLOW | -0.30 | -0.17 |
| LONDON | HIGH_FADE | -1.70 | -1.83 |
| NY_PM | HIGH_FOLLOW | -1.02 | -2.18 |
| NY_PM | HIGH_FADE | -0.98 | +0.18 |
| NY_AM | HIGH_FOLLOW | +0.35 | -3.03 |
| NY_AM | HIGH_FADE | -2.35 | +0.87 |
| ASIA | HIGH_FOLLOW | +0.25 | +0.05 |
| ASIA | HIGH_FADE | -2.50 | -2.29 |

## Gate summary

- Cells PROMISING/STRONG: **0** / 16
- **Program call: no executable directional edge under frozen card.**

