# Strategy 59 — COMPLETE / KILL

**Final:** `KILL` (Step 1 — first-passage)

Target (`1×R` extension) is **not** reached before adverse (`OR_mid`) more often than the reverse.

| split | n | p_target_first | p_adverse_first | Δ_fp |
| --- | --- | --- | --- | --- |
| IS | 2203 | 0.158 | 0.368 | **−0.210** |
| Validation | 727 | 0.179 | 0.374 | −0.195 |
| OOS | 389 | 0.131 | 0.380 | −0.249 |

~47% unresolved by `H_cap=60`. MAE and trade **not run**.

**Do not** retune `W_or` / target multiple / adverse. **Do not** reopen 52–58.

Report: `results/ORB_FIRST_PASSAGE_REPORT.md`
