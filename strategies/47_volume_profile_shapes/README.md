# Volume-profile research

Research only. This folder does not test a trade.

## Branch status

**Steps 1–5 (letter shapes → LVN boundary → traverse/reject) are frozen and closed.** See `VERDICT.md`.

| Step | Result |
| --- | --- |
| 1 / 1B | P/b geometry real as location; D/B poor textbook fit |
| 2 | Accepted regions descriptive; valley depth not a boundary |
| 3 | Prior HVN–LVN–HVN often touched next session |
| 4 | Traverse **killed** (≤ geometric null) |
| 5 | Rejection **killed** after null calibration |

Do **not** rescue the LVN object with ATR, direction, time-of-day, POC-distance, or day-of-week filters.

**Next branch (not run until you ask):** prior volume **location / acceptance** — `STEP6_PREREGISTRATION.md`. No LVN reaction events.

## Reproduce closed branch

Inputs: `data/trades_24h_6m/trades_24h_2026-03-25.dbn.zst` through `trades_24h_2026-09-16.dbn.zst`. Session clock: New York time at or after 18:00 belongs to that calendar date.

```text
python strategies/47_volume_profile_shapes/code/build_profiles.py
python strategies/47_volume_profile_shapes/code/detect_shapes.py
python strategies/47_volume_profile_shapes/code/sensitivity.py
python strategies/47_volume_profile_shapes/code/plot_profiles.py
python strategies/47_volume_profile_shapes/code/write_report.py
```

```text
python strategies/47_volume_profile_shapes/code/node_structure.py
python strategies/47_volume_profile_shapes/code/plot_nodes.py
python strategies/47_volume_profile_shapes/code/write_step2_report.py
```

```text
python strategies/47_volume_profile_shapes/code/boundaries.py
python strategies/47_volume_profile_shapes/code/interaction_audit.py
python strategies/47_volume_profile_shapes/code/write_step3_report.py
```

```text
python strategies/47_volume_profile_shapes/code/path_reaction.py
python strategies/47_volume_profile_shapes/code/write_step4_report.py
```

```text
python strategies/47_volume_profile_shapes/code/rejection_null.py
python strategies/47_volume_profile_shapes/code/write_step5_report.py
```

Do not edit `code/frozen.py` or Step 1B formulas to raise a class count.
