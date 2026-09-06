# Rules — Discovery menu (frozen before OOS look)

| ID | Side rule (causal ≤ T) |
|----|------------------------|
| `mom5_follow` | sign(close_T − close_{T−5}) |
| `mom15_follow` | sign(close_T − close_{T−15}) |
| `mom15_fade` | opposite of mom15 |
| `vwap_follow` | sign(close_T − session VWAP to T) |
| `vwap_fade` | opposite |
| `ext_fade` | closer to session high → short; closer to low → long |
| `prior_sess_mid` | sign(close_T − prior **session** mid) (Asia←prior NY_PM; else prior session same day) |
| `gap_follow` | sign(session_open − prior Globex day close) |
| `path30_follow` | sign(Σup − Σ\|down\|) over last 30m closes |
| `path30_fade` | opposite |

H primary **30** (also 60). Strategy 12 gate frozen. No stops/targets.
No adding features after seeing OOS.
