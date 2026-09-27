# 28. ES↔NQ Open Minute Lead/Lag (Scalp Probe)

**Verdict: `C` — NO_SCALP_EDGE (CLOSED)**

> Do completed 1-minute moves on ES (NQ) lead the other book over the next
> 1–30 minutes at the **NY open**, and does that path support a **fixed 1:1
> scalp** of ~20–30 NQ points (or ES $-equivalent)?

**No.** Same-bar ES↔NQ ρ≈0.83; lag-1 ρ≈0. Headline OPEN15 25pt scalp E_net
Discovery/Val/OOS ≈ −0.93 / −1.22 / −1.49. Survivors: **0**.

Not Strategy 15 (HIGH resolvers) and not Strategy 23D (overnight RS).

## Status gate

| Gate | Status |
|------|--------|
| Differentiation vs 15 / 23D | Locked |
| Rules frozen | Done |
| Phase 0 sync audit | **Done** |
| Phase 1 lead/lag descriptives | **Done** |
| Phase 2 scalp economics | **Done — fail** |
| Trading promotion | **Blocked / closed** |

## Run

```bash
set PYTHONPATH=d:\NQ-2
python strategies/28_es_nq_open_leadlag/code/run_phase0_sync_audit.py
python strategies/28_es_nq_open_leadlag/code/run_phase1_leadlag_open.py
python strategies/28_es_nq_open_leadlag/code/run_phase2_scalp_probe.py
```

Artifacts: `artifacts/28_es_nq_open_leadlag/`.

## Documents

| File | Purpose |
|------|---------|
| hypothesis.md | Research question |
| rules.md | Frozen definitions |
| testing_methodology.md | Phase gates |
| conclusion.md | Verdict after runs |
| DATA_NOTES.md | Sync / coverage notes |
