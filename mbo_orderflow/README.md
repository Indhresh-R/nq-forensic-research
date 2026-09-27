# MBO order-flow store

Infrastructure only. This folder does not read `volume_profile/` and it does not contain a trading rule.

The normalized files stay in `data/mbo_research/v2/`. This folder holds the audit of that store. The declared clock is `[09:30, 12:00)` America/New_York, one-second rows, not the full 18:00–17:00 CME session.

```text
python mbo_orderflow/code/audit_infrastructure.py
```

`REPLAY_ENGINE_V2_TIMESTAMP_CORRECT` is frozen. The 25 crossed snapshot rows are feed state and stay in the store. See `reports/INFRASTRUCTURE_AUDIT.md` and `reports/CROSSED_BOOKS.md`.

Information tests are preregistered in `PREREGISTRATION.md` and recorded in `reports/INFORMATION.md`. The from-above previous-POC event does not occur inside the stored 09:30–12:00 window. See `reports/POC_JOIN.md`.
