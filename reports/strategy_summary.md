# Strategy Summary (Master Table)

Footnote: **A\*** = statistically valid **state / opportunity detector**, **not** an executable standalone trading edge.

| # | Hypothesis | Verdict | Headline number |
| - | ---------- | ------- | --------------- |
| 01 | OR5 Liquidity Sweep Fade | **D** | reject-through OOS ORB PF **0.80** (headline was 6.17) |
| 02 | AM Trades | **C** | IS PF **0.894**, E **−1.42** pts (n=730) |
| 03 | NY Open Level Accept/Reject | **C** | best soft IS win **52.2%**; stress E[R] **−0.127** |
| 04 | NY Open State Transitions | **B→kill** | best OOS **59.6%** with IS mean **−0.3** pts |
| 05 | NY Open Path Asymmetry | **B→kill** | strong year-stable cells = **0** |
| 06 | HIGH Opportunity State | **A\*** | HIGH−LOW gap ~**+60pp**; already-moving **90%** |
| 07 | Direction inside / without HIGH | **C/B→kill** | multi-clock strong = **0** |
| 08 | EOD Options → Direction | **C** | survivors **0** (best win 51.1%) |
| 09 | Scheduled Macro Events | **C** | survivors **0** (best win 53.0%) |
| 10 | Reactive HIGH Capture | **C** | IS H10 Δwin **−2.2pp** vs blind |
| 11 | HIGH Residual Economics | **C** | cost-cover Δ mid H30 **+0.1pp** |
| 12 | Multi-session Activity Regime | **A\* CLOSED** | activity real (~**+30–55pp**); **NO TRADE** after 13/14 |
| 13 | Multi-session Direction | **C CLOSED** | 0/16 promising; London OOS E_net **−0.30** |
| 14 | Multi-session Residual Econ | **C CLOSED** | cover HIGH=LOW **~100%**; lift **0pp** |
| 15 | Dir resolution ES/NQ (lift) | **B→kill** | 0 strong lift; soft only; Val flips |
| 16A | Prior Globex daily Bias A | **B→kill** | HIGH+bias ~50–52%; no stable lift vs ALL |
| 16B | Prior-day midpoint location | **B→kill** | 2 strong single-clock; 0 multi-clock; no promote |
| 17 | Session extreme trap | **B→kill** | London OOS spike / Val flip; 0 multi-clock strong |
| 18 | Causal direction discovery | **C_null** | HIGH ~50% up; frozen menu no clean win-lift survivor |
| 19 | HTF horizon (SESS_END/H240) | **B→kill CLOSED** | soft single-clock only; longer H ≠ resolver |
| 20 | Pre-HIGH unusual displacement | **B→kill CLOSED** | soft NY_PM SESS_END only; H30 OOS med lift **−4.7pp** |
| 21 | First post-HIGH bar revelation | **C CLOSED** | soft/strong **0**; residual burn tiny — signal fail |
| 22 | Structural-ticket revelation | **C CLOSED** | soft/strong **0**; tested info failed sign resolve (not “unpredictable”) |

## Split qualitative (with key numeric anchors)

| # | IS | Val | OOS |
| - | -- | --- | --- |
| 01 | early PF~0.9–1.0 | rising contaminated | PF 6.17 → **0.80** causal |
| 02 | PF **0.894** | PF 1.14 | PF 1.02; 2025/26 **1.16/0.85** |
| 03 | soft 52.2%; stress −0.165R | soft high; stress ≤0 | stress −0.103R; 2025 WR 32.8% |
| 04 | +3–6pp / ~55% | weak | 59.6% but year flip |
| 05 | soft only | soft | soft; 2025/26 flip |
| 06 | disc **+62pp**; already 90% | +62pp | +56pp; 2025/26 hold |
| 07 | ~51–58% spikes | unstable | ~50–59%; multi-clock 0 |
| 08–10 | ~50% | ~50% | ~50% / ROC −4.3pp OOS |
| 11 | Δpts **−2.5**; cover Δ **+0.1pp** | cover Δ 0 | cover Δ 0 |
| 12 | disc **+30–55pp** all sessions | same-sign | same-sign; family closed NO-TRADE |
| 13 | E_net mostly **<0** | mostly <0 | 0 promising |
| 14 | cover ~ceiling both | same | HIGH−LOW cover Δ **0pp** |
| 15 | lift soft ~0–3pp | often **negative** | no strong / unstable |
| 16A | HIGH+bias ~51–52% | Val flips / weak | OOS ~45–53%; lift fails |
| 16B | HIGH+loc ~48–54% | soft / mixed | no multi-clock strong |
| 17 | HIGH+trap ~50–56% | Val often **negative** | OOS spikes unstable |

## Program terminal

**Direction branch 13–22: LOCKED FAILED. No Strategy 23.**

**Still true (not trades):**
- NY-open HIGH (06): late activity detector (A\*)
- Multi-session quiet→vol expansion (12): elevated future **activity/path** regime (A\*) — WHEN only

**Closed NO-TRADE:** Strategies **12–14** monetization; **13–22** sign resolution.

**Constraint:** [`research_framework/direction_resolution.md`](../research_framework/direction_resolution.md).

```text
WHEN (12)  -> A* elevated activity/path regime
WHICH WAY (13-22) -> locked failed (tested info)
HOW -> not opened
```

**Strategy 15–22:** all killed/closed (see table). Tree: [`artifacts/_shared/research_tree_activity_direction.md`](../artifacts/_shared/research_tree_activity_direction.md).

**Program status**
| Stage | Status |
|-------|--------|
| **WHEN** (12) | **A\* VALIDATED** — elevated future activity/path regime |
| **WHICH WAY** (13–22) | **LOCKED FAILED** |
| **HOW** | **Not opened** |

**Locked wording:** Strategy 12 appears to be a robust detector of an elevated future activity/path regime, but the tested information does not provide a stable incremental sign resolver.

**Do not claim:** “Direction is unpredictable.”  
**Do claim:** tested observable information failed to resolve direction robustly.

**Stop:** Strategy 23 as another price/state resolver; retuning tickets/windows; manufacturing a trade from residual size alone.

**Optional later branch (not opened):** Strategy 12 WHEN + an **external** causal sign source — not more OHLC features.
