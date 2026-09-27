# Testing methodology — Strategy 29

## Phase A — Frequency

Is 08:30–09:00 special for HOD/LOD vs control 30m windows?

## Phase B — Oracle scalp

Upper bound using end-of-day HOD_ONLY / LOD_ONLY labels + frozen dip/recovery.

## Phase C — Causal proxies

Same entry engine; sides from `fade_raid` / `fade_extent` / `fade_last_touch` only.

## Kill

A not special → weaken story but still run B/C.  
B fail → close.  
B ok + C fail → close as non-tradable narrative (do not live-trade EOD labels).
