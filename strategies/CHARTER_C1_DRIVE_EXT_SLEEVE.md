# Strategy 65 — C1 Drive-Exterior Continuation Sleeve (prereg)

**Status:** EXECUTED — verdict `KILL` (IS mean_net ≤ 0).  
**Namespace:** `strategies/65_c1_drive_ext_sleeve/`  
**Date:** 2026-09-27  
**Parent:** Environment atlas (`64`) + refusal map R1–R6.  
**Class:** First sleeve test. Cost-aware. **No promote without clearing path + cost gates.**

---

## Hypothesis (one sentence)

On mornings labeled **C1_DRIVE_EXT at 10:30**, a short **with-trend** continuation from the next bar open until **12:00 ET** (or stop) has positive expectancy after **1.0 pt** round-turn — and path MFE meaningfully exceeds MAE.

---

## Why this cell

| Choice | Freeze |
| --- | --- |
| Character | **C1_DRIVE_EXT** only |
| Clock | **10:30** ET (known before entry; thicker persistence into 11:30) |
| Direction | With exterior: `L_ABOVE` → **long**; `L_BELOW` → **short** |
| Not tested here | C2–C5, other clocks, fades back to VA |

---

## Data / gate (immutable from 64)

| Item | Source |
| --- | --- |
| Labels | `64_environment_atlas/results/labels.parquet` |
| Gate row | `clock == "10:30"` and `character == "C1_DRIVE_EXT"` |
| Axis L | Same row (`L_ABOVE` / `L_BELOW`) |
| Bars | `data/nq_1m_continuous.parquet` |
| VA context | 1m proxy (scaffold) — sleeve does **not** claim trade-tape VA precision |

Sessions without a valid gate row → no trade that day.

---

## Execution freeze

| Item | Rule |
| --- | --- |
| Entry | **Next 1m open** at or after **10:31** ET (no trade on the 10:30 bar) |
| Side | Long if `axis_L == L_ABOVE`; short if `L_BELOW` |
| Stop distance | `S = max(2.0 pt, 0.35 × prefix_range)` where `prefix_range` is 08:00–10:30 range from the gate label row |
| Stop price | Long: `entry − S`; short: `entry + S` |
| Exit A | Stop touched (1m high/low; stop first if same bar as time exit) |
| Exit B | **Time flat** at first bar with `ny_min >= 12:00` (exit that bar’s **open**) |
| Target | **None** (not a 1R-extension sleeve — avoids R6 costume of Strategy 60 class) |
| Trail | **None** in primary test |
| Size | 1 contract notionally; report in **points** |
| Cost | **1.0 point** round-turn subtracted from gross |

Intrabar: conservative — if stop level trades in a bar, assume stop fill at stop price (no optimistic close).

---

## Chronological splits (for reporting only)

Use calendar years on `session_date`:

| Split | Years |
| --- | --- |
| IS | 2010–2018 |
| Val | 2019–2022 |
| OOS | 2023–2026 |

**No parameter tuning on Val/OOS.** Primary kill/advance uses **IS** path+cost gates; Val/OOS are confirmation only.

---

## Primary metrics

Per trade and pooled by split:

1. `n`  
2. `mean_gross`, `mean_net` (net = gross − 1.0)  
3. `stop_rate`, `time_exit_rate`  
4. `med_MFE`, `med_MAE` (favorable/adverse excursion in points while in trade, from entry)  
5. `mfe_mae_rel_diff = (med_MFE − med_MAE) / max(med_MAE, 1e-9)`

---

## Decision rules (frozen)

| Verdict | Rule |
| --- | --- |
| **KILL** | IS `mean_net ≤ 0` **or** IS `mfe_mae_rel_diff < 0.25` (path too symmetric / adverse) **or** `n_IS < 200` |
| **INCONCLUSIVE** | IS `mean_net > 0` and path gate passes, but Val `mean_net ≤ 0` or OOS `mean_net ≤ 0` |
| **ADVANCE_RISK_DESIGN** | IS net>0, path gate passes, **and** Val and OOS both `mean_net > 0` — only then allow a *separate* charter for trails/runners |

`ADVANCE_RISK_DESIGN` ≠ promote to live. No live trading from this prereg.

---

## Explicit non-goals

- No fade-to-VA / Patrick first-passage reopen  
- No ORB (R1)  
- No 1R target extension (R6 / Strat 60 class)  
- No shopping other atlas characters after seeing results  
- No retune of `0.35`, stop floor, or exit time after seeing P&L  
- No trail in this run  

---

## Outputs

| Path | Role |
| --- | --- |
| `results/trades.parquet` | One row per gated session |
| `results/summary_by_split.csv` | Metrics by IS/Val/OOS/All |
| `results/SLEEVE_REPORT.md` | Report |
| `results/verdict.json` | KILL / INCONCLUSIVE / ADVANCE_RISK_DESIGN |
| `results/audit.json` | Gate, R-map checks, freeze echo |

---

## Refusal-map checklist

| ID | This sleeve |
| --- | --- |
| R1 | Not ORB |
| R2 | Path MFE/MAE gate required |
| R3 | Cost 1.0; kill if IS net ≤ 0 |
| R4 | Not destination-only; realized P&L + path |
| R5 | Single named character, not generic state routing |
| R6 | Not event→1R hold costume; time+stop continuation only |

Ready for code after this freeze (user go-ahead already given).
