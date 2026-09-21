"""Frozen replay identifier. Do not change the string without a new clock audit.

The 2026-09-20 crossed-book check replayed the raw feed with these rules.
All 25 crossed snapshot rows matched the stored book. Do not edit this engine to drop them.
"""

REPLAY_ENGINE_VERSION = "REPLAY_ENGINE_V2_TIMESTAMP_CORRECT"

# Row timestamp t is the last instant included in that row.
# Events with ts_event in (t - step, t] belong to row t.
# Events with ts_event in [t, t + step) belong to row t + step.
CLOCK_SEMANTICS = (
    "snapshot_t_includes_events_in_(t-step, t]_only; "
    "book_at_t_is_state_after_events_with_ts_event_le_t; "
    "forward_value_timestamp_gt_observation_timestamp"
)
