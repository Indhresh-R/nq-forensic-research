# Testing Methodology — Direction resolution ES/NQ

## Causality card

```text
Activity state: NQ session bars <= T (frozen Strategy 12 terciles)
Resolver R: NQ + ES bars <= T only
Entry: NQ next open after T
Outcome: signed NQ points to close at H (or last bar if short)
No future information: YES
```

## Splits

IS 2010–2021 / Val 2022–2024 / OOS 2025–2026; years 2025 & 2026 separate.

## Promotion bar (lift)

Soft: HIGH win−ALL win ≥ +3pp OR HIGH E−ALL E ≥ +0.5 pts on IS; same-sign lift Val+OOS; n floors.
Strong: ≥ +5pp or ≥ +1.0 pts IS lift; Val+OOS material; year-stable where n≥20.
Multi-clock: ≥2 offsets for same (session, R, H).

Kill family if strong/soft survivors = 0 after hostile gates.
