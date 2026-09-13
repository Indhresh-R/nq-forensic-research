# 29. 08:30–09:00 HOD/LOD → 09:30 Opposite Dip/Recovery

**Verdict: `C` — NO_CAUSAL_EDGE (corrected Phase D)**

**Correction:** Not end-of-day HOD/LOD. Setup is **day-so-far** extreme in
08:30–09:00, reverse before open, skip if 09:30 still at that extreme, then
probe entries/exits. Phase D: **0** Val+OOS survivors. See `conclusion.md`.

## Run

```bash
set PYTHONPATH=d:\NQ-2
python strategies/29_830_900_hodlod_opposite/code/run_phase_a_frequency.py
python strategies/29_830_900_hodlod_opposite/code/run_phase_bc_scalp.py
python strategies/29_830_900_hodlod_opposite/code/run_phase_d_so_far_causal.py
```

Artifacts: `artifacts/29_830_900_hodlod_opposite/`
