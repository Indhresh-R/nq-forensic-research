# Strategy 65 — COMPLETE (KILL)

**Status:** Run finished under `CHARTER_C1_DRIVE_EXT_SLEEVE.md`.  
**Verdict:** **`KILL`** — IS mean_net ≤ 0 after 1 pt RT.  
**No promote. No trail follow-on. No character shopping.**

## Sleeve

| Item | Freeze |
| --- | --- |
| Gate | C1_DRIVE_EXT @ 10:30 |
| Side | With exterior (above→long, below→short) |
| Exit | Stop `max(2, 0.35×prefix_range)` or time flat 12:00 |
| Cost | 1.0 pt RT |

## Headline

| Split | n | mean_net | mfe_mae_rel |
| --- | ---: | ---: | ---: |
| IS | 421 | **−0.11** | 0.07 |
| Val | 263 | +2.54 | 0.36 |
| OOS | 244 | +4.92 | −0.01 |

IS fails cost gate (and would fail path gate). Later splits are **not** a rescue under the frozen rules.

## Artifacts

| Path | Role |
| --- | --- |
| `results/trades.parquet` | Trade log |
| `results/summary_by_split.csv` | Split metrics |
| `results/SLEEVE_REPORT.md` | Report |
| `results/verdict.json` | KILL |

## Next

Do **not** add trails to this sleeve. Next atlas sleeve needs a **new** charter (different cell or different payoff), or stop sleeve hunting and keep the atlas as a catalog only.
