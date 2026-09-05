# Artifacts (grouped by strategy family)

Machine outputs from forensic experiments. Each folder matches a dossier under `strategies/`.

| Folder | Family |
|--------|--------|
| `01_OR5_liquidity_sweep/` | OR5 / Inverse ORB forensics |
| `02_AM_Trades/` | AM Trades |
| `03_NY_open_level_reactions/` | Level accept/reject |
| `04_NY_open_state_transitions/` | State → outcomes |
| `05_NY_open_path_asymmetry/` | Path asymmetry |
| `06_HIGH_opportunity_state/` | Opportunity timing + HIGH mech + frozen gate |
| `07_direction_inside_and_without_HIGH/` | Direction families |
| `08_EOD_options_direction/` | Options E1 |
| `09_scheduled_events/` | Events E2 |
| `10_reactive_HIGH_capture/` | Reactive capture |
| `11_HIGH_residual_economics/` | Residual economics |
| `_shared/` | Shared inputs (e.g. day facts) |

Code resolves paths via `common.paths.art("filename.ext")` → family folder.

**Not in git:** `*.parquet` panels and `data/` market files (regenerate locally). Reports (`.md` / `.json` / `.csv`) are committed.
