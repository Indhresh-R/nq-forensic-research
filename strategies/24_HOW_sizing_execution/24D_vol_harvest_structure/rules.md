# Rules — 24D (frozen)

1. HIGH = Strategy-12 frozen `rng_psr` p66; do not refit.
2. `BO_FRAC=0.10`, `STOP_R=1.0`, `TGT_R=1.5`, `WIDTH_HIGH=1.50`, `WIDTH_NON=1.00`, `MAX_HOLD=60`.
3. Side from first breakout touch only — never from state/vol/sign features.
4. Same-bar dual breakout → skip; same-bar stop+target → stop first.
5. Unit size; mid cost 1.0 pt RT.
6. Policies: `uncond_base`, `uncond_wide`, `regime_width`, `high_only_base` only.
7. Splits IS/Val/OOS; stage-gate IS first.
8. No directional claim; 24A null does not auto-kill this ticket.
