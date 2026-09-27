# Rules: Strategy 38 Opening Auction Information

## Causal & Information Rules
1. **Strict Checkpoint Cutoffs**: Information extracted at checkpoint $T$ uses only completed bars strictly timestamped `<= T`.
2. **Outcome Isolation**: Remaining-session metrics ($Y_1$ through $Y_4$) are computed strictly from minute $T+1$ forward through $15:55$ ET.
3. **No Overlap Contamination**: The opening window ($09:30 \to T$) is never included in the remaining session targets ($T+1 \to 15:55$).
4. **Information Gate First**: No profit targets, stop-losses, trailing mechanics, or fee models are optimized in this phase.
