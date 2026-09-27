# Data notes — Strategy 27

## Classification

**Phase 1 is a PROXY study on OHLCV volume-pressure fields. It is not an order-flow study.**

Never write “order flow predicts X” for results derived from these series.

## Local series (Phase 0 audit)

| File | Rows | Span (ET) |
|------|------|-----------|
| `data/es_1m_continuous.parquet` | 4,916,275 | 2010-06-06 → 2026-08-26 |
| `data/nq_1m_continuous.parquet` | 4,788,194 | 2010-06-06 → 2026-08-07 |

Schema: `ts_event, open, high, low, close, volume, symbol` only.

## Continuous construction

Databento GLBX.MDP3 OHLCV-1m; volume-based front month per calendar day; no price back-adjustment. See `archive/legacy_scripts/build_continuous_data.py`.

## Volume

- Unsigned. Min=1, **no zeros** in continuous files.
- RTH gap>1m fraction ≈ 0.26–0.27%.

## What we do not have

buy/sell volume, aggressor side, trader type, BBO, depth.

## Phase 0 collinearity (why residual is mandatory)

ES Discovery RTH: Spearman(`signed_vol_proxy`, `ret_1m`) ≈ **0.93**.  
`|signed_vol_proxy|` is mostly volume scale (R² ≈ 0.87 vs volume).

→ Raw `signed_vol_proxy` is largely a **signed-return × volume** transform. Report `signed_vol_proxy_resid` before any information claim.

## Freeze

Authoritative definitions: `rules.md` + `artifacts/27_orderflow_information/phase0_freeze.json`.
