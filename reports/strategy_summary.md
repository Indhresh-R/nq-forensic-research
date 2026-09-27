# Strategy Summary (Master Table)

Latest: **42 Timeframe Support/Resistance — C**. No identical 20-bar S/R breakout/retest timeframe passes the NQ+ES IS/Validation/OOS gate; NQ 1m/15m OOS retest positives fail IS and ES, while every >=1h arm is negative OOS in both markets.

Latest: **43 Event-Based Range Transition — REJECTED**. All 12 sequential compression cells lose in selection; range fading fails every later split and pullback continuation is non-positive in R after costs.

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
| 23A | COT TFF positioning (under 12 HIGH) | **C CLOSED** | IS +2.5pp vs HIGH-long → Val **−7.4pp** → OOS **−11.3pp** (monotonic worse); 5/120 ≈ noise |
| 23D-ES | Overnight ES/NQ RS (under 12 HIGH) | **C CLOSED** | IS-only kill; strong **0**/24; H30 **all clocks neg** vs HIGH-long |
| 23D-ZN | Overnight ZN/NQ RS (under 12 HIGH) | **C CLOSED** | IS-only; strong **0**/24; hard stop **FIRED**; family 23 done |
| 23D-ZB | Overnight ZB/NQ RS | **UNTESTED** | data never present (ZN dump duplicated) — **not** a rescue |
| 24A | HOW: vol-scaled sizing (inv-vol ± HIGH) | **C CLOSED** | coin-flip; ΔSharpe IS **−3.27** → Val **−0.36** → OOS **−0.18**; mechanical cost×\|size\| |
| 24B | HOW: regime stop/target width | **Absorbed in 24D** | `regime_width` arm; no separate dossier |
| 24D | HOW: symmetric breakout vol-harvest | **C** (HIGH harvest) | Val ΔSharpe regime−wide **−2.79** [−3.53, −2.12]; best E still **−1.74**; width helps unconditionally |
| 24C | HOW: holding period by regime | **Held** | only remaining distinct mechanism |
| 35 | Bull Flags and Bear Flags | **C** | ES OOS PF **0.691**, E **−3.16** pts; NQ bull flags = long beta; bear flags fail |
| 36 | Unconditional NQ Long Bias | **C** | Intraday 5–60m net negative (PF 0.63–0.95); session drift dominated by passive RTH hold (Sharpe 0.085 vs 0.123) |
| 37 | Overnight Inventory → RTH Persistence | **C (Info)** | Gap continuation 50.8% coin flip; efficiency invariant (0.46–0.50); tail regimes flip (True Gap Down Val −135 vs OOS +176 pts) |
| 38 | Opening Auction Information → RTH Persistence | **C (Info)** | Early efficiency does not condition remaining efficiency (0.475 vs 0.464); trend day lift +1.3pp; gross return +0.77 pts (-0.23 net) |
| 39 | Multi-Day Volatility Compression → RTH Expansion/Persistence | **C (Info)** | Volatility clusters: 4+ days compression yields 10.5% large expansion rate vs 33.0% uncompressed; NR7 range 0.881x vs 1.053x; efficiency flat ~0.47 |
| 40 | Volatility Persistence → Directional Distribution | **C (Boundary)** | Directional continuation is 45%–50% coin flip across all vol tiers; tail variance expands symmetrically (+0.5% spread); excursion spread +0.002 ATR |
| 41 | Volatility Regime × Signal Economics | **C (Econ Filter)** | Extreme Vol worsens net losses across all benchmarks (IB: −9.47 pts net, PF 0.775; Drive: −6.46 pts, PF 0.755; Clock: −7.44 pts, PF 0.741); MAE scales faster than MFE |

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
| 23A | strong **5**/120; +2.5pp vs H-long | inc **−7.4pp** | inc **−11.3pp** (monotonic IS→Val→OOS worse) |
| 23D-ES | strong **0**/24; all H30 neg vs H-long | **skipped** (IS kill) | **skipped** (IS kill) |
| 23D-ZN | strong **0**/24; all H30 neg vs H-long | **skipped** (hard stop) | **skipped** (hard stop) |
| 23D-ZB | — | — | **UNTESTED** |
| 24A | Sharpe fixed **−1.90** / invvol **−5.17**; CI ΔSharpe &lt; 0 | confirms null (Δ **−0.36**) | Δ invvol **−0.18**; absolute Sharpe noise+ on fixed |
| 24D | regime−wide ΔSharpe **−3.10**; wide E **−1.24** | **VAL_WIDE_DOMINATES** Δ **−2.79**; wide E **−1.74** | optional |
| 24C | — | — | **held** |
| 35 | ES IS PF 1.08; NQ IS PF 1.35 | ES Val PF 1.38; NQ Val 1.10 | ES OOS PF 0.69 (E −3.16); 2025/26 NQ C1 E −1.70 / +13.48 |
| 36 | 5–60m IS E_net <0; Mode B 0/8 | 5–60m Val E_net <0; Mode B 0/8 | OOS 60m E −3.27 to +0.98; passive RTH Sharpe 0.123 vs active 0.085 |
| 37 | IS gap cont 51.3%; eff 0.464 | Val gap cont 50.7%; eff 0.497 | OOS gap cont 48.0%; eff 0.489; extreme tail regimes flip violently |
| 38 | 15m IS HighEff rem eff 0.463 vs LowEff 0.460 | Val HighEff rem ret −10.91 vs LowEff −15.27 | OOS HighEff rem eff 0.464; lift in trend days +1.3pp; net ret < 0 |
| 39 | IS 4+ days comp exp_125 9.3% vs 0d 36.0%; NR7 norm range 0.858 | Val 4+ days comp exp_125 12.5% vs 0d 23.5%; NR7 range 0.977 | OOS 4+ days comp exp_125 15.2% vs 0d 35.1%; NR7 range 0.838 |
| 40 | IS HighVol continuation 47.7%; ExtremeVol tail spread +1.3% | Val HighVol continuation 39.0%; tail spread 0.0% | OOS HighVol continuation 41.7%; 2025 HIGH_VOL_UP −151 pts vs 2026 +132 pts |
| 41 | IS ExtremeVol IB −12.14 pts net (PF 0.62); Drive −2.91 pts | Val ExtremeVol IB −9.96 pts; Drive −11.03 pts; Clock −18.60 pts | OOS ExtremeVol IB +8.42 pts; Drive −21.46 pts; Clock −38.58 pts |

## Program terminal

**Direction branch 13–22: LOCKED FAILED** (price/state resolvers).

**External branch 23: CLOSED** (hard stop fired on 23D-ZN).

| Leg | Status |
|-----|--------|
| 23A COT | **C** — monotonic incremental degradation +2.5 → −7.4 → −11.3pp |
| 23D-ES | **C** — IS null incremental |
| 23D-ZN | **C** — IS null incremental; **hard stop** |
| 23D-ZB | **UNTESTED** — not a rescue |

**Still true (not trades):**
- NY-open HIGH (06): late activity detector (A\*)
- Multi-session quiet→vol expansion (12): elevated future **activity/path** regime (A\*) — WHEN only

**Closed NO-TRADE:** Strategies **12–14** monetization; **13–22** sign resolution; **family 23** external legs tested above.

**Constraint:** [`research_framework/direction_resolution.md`](../research_framework/direction_resolution.md).

```text
WHEN (12)  -> A* elevated activity/path regime
WHICH WAY (13-22) -> locked failed (tested price/state info)
EXTERNAL (23) -> CLOSED (hard stop)
HOW (24) -> 24A C; 24D C (wide dominates, E<0); 24B absorbed; 24C held
```

**Program status**
| Stage | Status |
|-------|--------|
| **WHEN** (12) | **A\* VALIDATED** — elevated future activity/path regime |
| **WHICH WAY** (13–22) | **LOCKED FAILED** (price/state) |
| **EXTERNAL** (23) | **CLOSED** — COT + ES-overnight + ZN-overnight all **C** |
| **HOW** (24) | 24A/24D **C**; 24B absorbed in 24D; **24C held** |

**Locked wording (13–22):** Strategy 12 appears to be a robust detector of an elevated future activity/path regime, but the tested information does not provide a stable incremental sign resolver.

**Locked HOW reading:** Strategy 12 activity does not monetize via sizing, width, or regime-filter of a direction-agnostic structure under costs; wider helps unconditionally, not because of HIGH.

**Do not claim:** “Direction is unpredictable.”  
**Do claim:** tested price/state and tested external legs failed to resolve direction; HOW sizing/width/HIGH-filter failed to monetize activity under costs; 24C holding-period not yet tested.

**Stop:** further external resolvers without a new argument; ZB-as-rescue; OHLC retunes.
