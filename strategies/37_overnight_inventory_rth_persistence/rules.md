# Rules: Strategy 37 Overnight Inventory → RTH Directional Persistence

## Causal Constraints
1. **Information Horizon**: All overnight features ($G_1$ through $G_5$) must be computed strictly using continuous prints timestamped `<= 09:29:59 ET`. No same-day RTH data is permitted in feature calculation.
2. **Prior Day Anchors**: Prior RTH High, Low, and Close are strictly taken from the preceding completed session's $15:55$ print.
3. **No Retrospective Tuning**: The bins and categories defined in `PREREGISTRATION.md` are frozen.
4. **Information-First Protocol**: No profit targets, stop-losses, trailing stops, or fee models are optimized in this phase.
