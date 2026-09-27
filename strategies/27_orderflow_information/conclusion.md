# Conclusion

## Verdict

**Phase 0: `PASS` (freeze locked). Phase 1: `DESCRIPTIVES_DONE` — PROXY STUDY.**

Signed OHLCV proxies are **not** order flow. Directional `signed_vol_proxy` is mostly a relabeled return transform; after orthogonalizing to ret/|ret|/range, forward return association collapses. Unsigned activity tracks future |ret|/RV (vol clustering / activity state), not signed pressure.

## Why (Phase 0)

- Local data = Databento continuous 1m **OHLCV only**
- Spearman(`signed_vol_proxy`, `ret_1m`) ≈ **0.93** (ES Discovery RTH)
- R²(|signed_vol_proxy| ~ volume) ≈ **0.87**

## Why (Phase 1)

ES / NQ RTH panels (~1.38M rows each). Example ES H=15 target=`ret`:

| Feature | Discovery | Validation | OOS |
|---------|----------:|-----------:|----:|
| `ret_1m` | -0.023 | -0.002 | -0.004 |
| `signed_vol_proxy` | -0.020 | -0.004 | -0.003 |
| `signed_vol_proxy_resid` | -0.003 | -0.005 | +0.001 |

Raw proxy mirrors `ret_1m`. Residual ≈ noise for direction.

Unsigned `volume` / `vol_z_tod` / `vol_x_range` correlate strongly with future `absret`/`rv` (e.g. ES OOS H15 `vol_x_range`↔`rv` ≈ 0.73) — that is **volatility/activity persistence**, already largely present in `absret_1m`/`range`, not informed signed flow.

## Language lock

Do **not** write “order flow predicts …” for Strategy 27 Phase 1 results.

## Next

- **Do not** open trading rules.
- Phase 2 ΔR² only if we ask a narrower, honest question: *does unsigned activity add incremental RV information beyond recent |ret|/range/TOD?* — not “does order flow predict direction?”
- If that fails or is economically trivial → close 27 → Strategy 28 cross-market lead/lag.
- **Strategy 28 ran and closed `C` / NO_SCALP_EDGE** (1m open lead/lag + 20–30pt scalp grid).
