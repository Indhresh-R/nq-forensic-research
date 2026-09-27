# Conclusion — Strategy 28 ES↔NQ open minute lead/lag

## Verdict

**`C` — `NO_SCALP_EDGE` / CLOSED.**

Minute-level ES↔NQ lead/lag at the NY open does **not** support a fixed 1:1
20–30 pt (NQ) or 8–12 pt (ES) scalp after costs. **0** Val+OOS survivors on the
frozen 288-cell grid.

## Why (numbers)

### Phase 0

- Synced bars: **4,772,587** | sessions: **4,175**
- Discovery RTH same-bar Spearman(ES,NQ) ≈ **0.835** (books move together)

### Phase 1 — lead dies at lag 1

Contemporaneous correlation is high; **lag-1 is ~0**:

| Window | Pair | Disc H1 ρ | Val H1 ρ | OOS H1 ρ |
|--------|------|----------:|---------:|---------:|
| OPEN15 | es→nq | 0.001 | 0.005 | −0.002 |
| OPEN15 | nq→es | 0.003 | 0.013 | 0.021 |
| MID | es→nq | −0.014 | −0.013 | −0.016 |

h1/h0 ratio on OPEN15 es→nq ≈ **0.001** (Discovery). Open is slightly less
mean-reverting than MID, not a tradable lead.

Signed hit-rates hover ~**0.48–0.51** — coin flip after one minute.

### Phase 2 — scalp economics fail

Headline `es_lead_nq` OPEN15 target=25 H=15:

| Split | n | win | E_net (pts) | target% | stop% |
|-------|--:|----:|------------:|--------:|------:|
| Discovery | 32,032 | 46.2% | **−0.93** | 13% | 13% |
| Validation | 10,989 | 49.2% | **−1.22** | 44% | 45% |
| OOS | 5,941 | 49.0% | **−1.49** | 48% | 50% |

- **Survivors (Val+OOS E_net>0, n≥30): 0**
- A few OOS-only soft positives (`nq5_lead_es` OPEN5) fail Validation / Discovery
  (IS-negative) — not promotable

## Interpretation

ES and NQ are **contemporaneous**. At 1-minute resolution there is no stable
leader you can chase for 20–30 NQ points at the open. Path volatility is high
enough to hit ±25 often in Val/OOS, but **stop hits as often as targets**.

Aligns with Strategy **15** (session resolvers) and **23D** (overnight RS):
cross-book information does not resolve a scalp side.

## What not to do next

- Do not retarget 15/20/40 pts or add ORB/confluence on top of this lead
- Do not promote OOS-only OPEN5 soft cells
- Do not reopen overnight RS or HIGH-gated ES follow as a scalp rescue

## Optional later (new data argument only)

Sub-minute / MBO lead-lag — **only** if argued why 1m failure does not apply.
Not a license to keep mining OHLCV open fades.
