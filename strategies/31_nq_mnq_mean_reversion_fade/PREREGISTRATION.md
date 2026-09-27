# NQ/MNQ mean-reversion fade -- locked implementation

Frozen 2026-09-14 before the script was run. Cost is **$2.00 round trip per
1 MNQ**: the repository's established 1.0 NQ-index-point round trip, scaled
from the NQ $20/point multiplier to MNQ $2/point.

All entries use a completed signal bar and the next 1-minute open. Trading is
one trade per candidate per session, signals 09:45--15:00 ET, flat at the
15:55 bar close. Stop/target collisions are stops first.

| Candidate | Exact fixed rule |
|---|---|
| VWAP 1R / 1.5R | Cash-session typical-price VWAP. First 1-minute close at least 30 points from VWAP: a fixed 20-point band plus a fixed 10-point extension. Fade at next open. 75-point stop; targets 75 and 112.5 points respectively. |
| Opening range | OR is 09:30--09:59 high/low. First close back inside it within 10 minutes after a close outside it; fade toward midpoint at next open. Stop 87.5 points; target is the smaller of midpoint distance and 87.5 points. |
| HIGH VWAP 1R | VWAP 1R rule, only 09:35--11:00 while the existing `vol_expansion_high` state is active. It is `RTH range to the completed signal bar / ONR >=` the already-frozen 2010--2021 p66 threshold at the latest completed 5-minute clock (from `ny_open_opp_timing_thresholds_IS.json`). |
| 5m extension | First completed 5-minute close more than 2.0 population SD from the mean of the prior 20 completed 5-minute closes; fade at next 1-minute open. 100-point stop, 150-point target. |

The fixed list, thresholds, stops, targets, cost, fills, and train/inner/validation/OOS gates are implemented in `code/run_preregistered_fades.py`. No result-dependent substitutions or parameter changes are allowed.
