# Hypothesis — Multi-session opportunity / activity

## Market behavior under test

Activity persistence differs by Globex session. Causal HIGH/LOW states inside
Asia, London, NY AM, or NY PM can reprice P(structural residual >= 0.25 * psr
within H) vs the same session-TOD baseline — without implying direction.

## Economic / mechanical rationale

Liquidity and participation regimes change across the 24h clock. A session that
is already expanding may keep producing large unsigned excursions (opportunity /
activity timing), analogous to the NY-open HIGH detector — but each session must
earn its own IS-frozen thresholds. Prior-session range (`psr`) replaces ONR as
the scale unit outside the old overnight→09:30 frame.

## Success / failure criteria

### Success (promote session family to Phase B)

- Causal signal only (`t <= T`; outcomes from next bar open)
- Same-sign HIGH−LOW discrimination gaps on IS, Validation, and OOS
- Multi-clock stability (not a single offset spike)
- 2025 and 2026 same-sign where n allows
- Thresholds frozen on IS feature terciles only (not fit on forward resolve)

### Failure (kill session family)

- Discrimination gaps ~0 or year flips
- Soft single-clock cells only
- Effect explained entirely as already-moved residual with no leftover for Phase B
