# Rules: Strategy 35 Bull Flags and Bear Flags

## Causal Rules
1. **Signal Availability**: Signal bar $T$ must be fully completed. All conditions (pole, flag, volume, breakout) evaluate strictly using information $t \le T$.
2. **Execution Timing**: Entry at the open of bar $T+1$ (next 1-minute open).
3. **Session Boundaries**: Cash RTH only (09:30–15:55 ET). Signals permitted between 09:45 and 15:00 ET. All open positions closed flat at 15:55 ET.
4. **Collision Policy**: If stop and target are touched in the same 1-minute bar, resolve as STOP FIRST.
5. **No Parameter Refitting**: All thresholds frozen as per `PREREGISTRATION.md`.
6. **Execution Costs**:
   - NQ: 1.0 point round-trip ($20.00 / contract).
   - ES: 0.50 point round-trip ($25.00 / contract).
