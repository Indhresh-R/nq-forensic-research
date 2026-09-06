# 23D-bonds — pre-registration (BEFORE IS look)

## Data inventory (2026-09-06)

| Dump folder | Job metadata | Content |
|-------------|--------------|---------|
| `GLBX-20260906-WL8QFM334H` | `ZN.FUT` | ZN 1m OHLCV CSV |
| `GLBX-20260906-XMDRMALJEB` | same job_id / same SHA256 | **duplicate of ZN** |

**ZB.FUT is not present.** Do not treat duplicate ZN folders as ZN+ZB.

| Leg | Status before look |
|-----|--------------------|
| **23D-ZN** | Runnable after continuous build |
| **23D-ZB** | **UNTESTED** — data still absent |

## Frozen grid (23D-ZN only) — 24 cells

| Axis | Values | Count |
|------|--------|------:|
| Session | NY_AM | 1 |
| Clocks | {15, 30, 60, 90} | 4 |
| Horizons | {15, 30, 60} | 3 |
| Signals | `zn_follow`, `zn_fade` | 2 |
| **Total** | | **24** |

Expected false strong @~5%: **~1.2**.

Overnight RS: `overnight_ret_ZN − overnight_ret_NQ` (prior ≤16:00 close → 09:30 open).
Three-way from the start: ALL+sig / HIGH-long / HIGH+sig.
Primary metric: lift vs **HIGH-long**.

## Hard stop (also in `direction_resolution.md`)

If IS shows **0 strong** or 23A/ES-like incremental flip vs HIGH-long → close
**Strategy 23 family**; no 5th external candidate without a new argument.
ZB later ≠ rescue of a ZN kill.
