# Frozen rules

- Session: 09:30–15:55 ET; incomplete sessions and early closes are excluded.
- Initial Balance: high/low of 09:30–10:29 one-minute bars.
- Signal: first five-minute close from 10:34–15:29 that closes at least one tick beyond an IB edge.
- Entry: next one-minute open; one trade per day.
- Stop: opposite IB edge. Target: one initial risk unit (1R). Flat: 15:55 open.
- A one-minute bar touching both stop and target is booked as a stop.
- Net result deducts round-trip costs in points.
