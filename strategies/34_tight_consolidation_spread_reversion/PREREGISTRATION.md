# NQ/MNQ tight-consolidation breakout & NQ--ES spread reversion

Research pass date: 2026-09-14. This document fixes every formerly bracketed
choice before the candidates are evaluated.

## Data and execution

All signals use synchronized continuous one-minute NQ and ES data, restricted
to 09:30--15:55 America/New_York. Periods are Train (2010--2018), Inner
Validation (2019--2021), Validation (2022--2024), and OOS (2025--2026,
available data only). A stop/target collision in a one-minute bar is a stop.
Positions are marked out at the 15:55 close.

Family A executes one MNQ: $2 per NQ point and $2.00 round-trip cost.
Family B executes one MNQ plus one MES: MNQ is $2/NQ point and MES is
$5/ES point. This micro pair is used rather than NQ+ES because it has one
tenth of the per-unit dollar risk. The fixed combined round-trip cost is
$4.00 ($2 per leg).

## Frozen candidates

1. For Family A, calculate every completed trailing 30-one-minute-bar
high-low range in Train RTH data and freeze `X` as its 25th percentile. A
signal is the first breakout per session: after a completed 30-bar window
whose range is no wider than X, the next completed one-minute close beyond
that window's high or low enters in the breakout direction at that close.
The stop is the opposite side of that exact compression range. Candidate A1
uses 1R and A2 uses 1.5R. Candidate A3 is A1 plus breakout-bar volume > 1.5x
the mean volume of the 30-bar compression window. No other entry is taken
that day.

2. For Family B, construct the directly tradable dollar spread
`2 * NQ - 5 * ES` (one MNQ less one MES). At each completed synchronized
one-minute close calculate its rolling 60-close mean and sample standard
deviation, excluding the current close. A z-score at or beyond +/-2.0 enters
on the next minute's close in the opposite spread direction. The signal's
mean is frozen at entry. The stop is a $150 adverse spread P&L. B4's gross
target is the nearer of $225 (1.5R) and the signal-to-mean dollar distance;
B5's gross target is always $225. These are dollar P&L barriers on the two
leg position, not adaptive exits. Only the first signal per session is used.

All candidates have the fixed $150 maximum stop. Selection uses only Train
and Inner Validation. The implementation records the Train-derived X value
in its outputs before candidate construction.
