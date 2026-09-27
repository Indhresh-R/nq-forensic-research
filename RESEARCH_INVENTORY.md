# NQ intraday research inventory

Audit date: 2026-09-21. This file records completed experiments and the verdict written in the original report. It does not search for a new strategy.

Statuses used below are only:

- `SUPPORTED` — the report's own claim held.
- `NOT SUPPORTED` — the report killed, rejected, or closed the claim.
- `INCONCLUSIVE` — the report said the result was unclear, under-powered, retracted, or not a pass/fail.

`NOT TESTED` is recorded separately. It is not a failure.

A supported activity or volatility fact is not a supported directional trade. Where a report established one and rejected the other, both claims are listed.

## How to read a row

| Field | Meaning |
| --- | --- |
| Information | The market object the test actually used |
| Primary test | The pre-registered comparison, not a later rescue |
| Null / baseline | What the apparent effect was compared with |
| Design | Sample, split, and whether a later period could change the rule |
| Friction | Realistic cost, adverse fill, or an explicit information-only test |
| Verdict | Mapped from the report's language. The report's own words are in Failure / result |

Shared OHLC panel, unless a row says otherwise: continuous NQ (and often ES) 1-minute bars, about 2010-06 through 2026-08. Two split conventions appear. Direction-family studies usually use IS 2010–2021, Validation 2022–2024, OOS 2025–2026. Prop-style studies usually use Train 2010–2018, Inner Validation 2019–2021, Validation 2022–2024, OOS 2025–2026, with thresholds frozen before the later periods. Round-trip friction in the later OHLC studies is typically 1.0 NQ point or $2.00 MNQ. Information-only studies say so and do not pretend a cost model was run.

`00` is an engine check, not a market hypothesis. Buy-and-hold identity and SMA recomputation passed. Later failures are not an accounting bug.

---

## A. Price geometry

| ID | Hypothesis | Information | Primary test | Null / baseline | Design | Friction | Verdict | Failure / result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 01 OR5 liquidity sweep | 5-minute opening-range sweep reverses | OR high/low, fade | IS → Val → OOS profit factor after causal fills | Unconditional path; reject-through stress | Standard direction splits | Through-stop fills removed in the stress test | `NOT SUPPORTED` | Contaminated OOS PF 6.17 was an execution artifact. Through-stop trades were 59.6% of the book and 99.6% of OOS PnL. Causal reject-through OOS ORB PF 0.80. Gap-through primary OOS PF 0.75. |
| 02 AM trades | Discretionary AM pattern set | Intraday price pattern | Frozen rule, IS/Val/OOS | None beyond the rule's own expectancy | Standard splits | Included in the reported PF | `NOT SUPPORTED` | IS n=730, WR 34.0%, PF 0.894. OOS PF 1.015. 2025 PF 1.16 vs 2026 PF 0.85. |
| 03 NY open level reactions | PDH/PDL/ONH/ONL acceptance or rejection | Prior-day and overnight levels | Causal win rate and mean points after label overlap removed | ~50% and soft stress book | Standard splits | Stress book on `C_PDL_accept` | `NOT SUPPORTED` | Strict causal survivors = 0. Best soft cell IS h15 win 52.2%. Impulse continuation was an anti-edge (IS win 44.5%). |
| 04 NY open state transitions | Open state predicts the next path | Opening state labels | Multi-clock directional win rate | Unconditional ~52% | Standard splits; year split | Points and ONR normalization | `NOT SUPPORTED` | Weak, year-unstable. Best OOS cell 59.6% with IS mean −0.3 pts. Raw-point edges flipped under ONR normalization. |
| 05 NY open path asymmetry | Open location creates a stable path tilt | Distance to overnight levels, quiet vs active open | Year-stable cells across IS/Val/OOS/2025/2026 | Unconditional resolve rate | Standard splits | Not a promoted trade | `NOT SUPPORTED` | Strong cells = 0. Soft cells flipped by year (`open_near_ONH` 2025 75% / 2026 50%). Side finding: `quiet_wait` cuts structural resolve, which led to the activity-state work. |
| 07 Direction inside / outside HIGH | A short-horizon OHLC resolver works inside or outside the activity state | Open continuation, ES, volume, multiscale, serial, extreme, failed move, retrace | Multi-clock strong cells | Inside-HIGH follow ~51–55% | Standard splits | Information / hit rate | `NOT SUPPORTED` | Multi-clock strong = 0. Report's own close: stop inventing OHLC directional families on this menu. |
| 10 Reactive HIGH capture | Waiting for a reaction after HIGH beats entering at HIGH | Post-HIGH path | React vs blind-at-HIGH | Blind-at-HIGH ~50% | Standard splits | Hit-rate comparison | `NOT SUPPORTED` | IS H10 blind 48.2% vs react 46.0%. OOS H10 delta −4.3 pp. Strong horizons = 0. |
| 16A Prior daily candle | Prior Globex candle sign resolves later direction | Prior session close vs open | Lift vs ALL and vs HIGH, H in {15…120} | Unconditional and HIGH-long | Panel 69,373; standard splits | Hit-rate lift, not a costed book | `NOT SUPPORTED` | 0 strong, 4 soft. London H30 lift IS +2.1 / Val −2.1 / OOS +0.5 pp. |
| 16B Prior-day midpoint | Side of prior midpoint resolves direction | `sign(close − prior mid)` | Same lift design as 16A | Unconditional and HIGH-long | Panel 68,629 | Hit-rate lift | `NOT SUPPORTED` | Soft / single-clock only. 0 multi-clock strong keys. Report forbids a PDH/PDL rescue. |
| 17 Session extreme trap | Trapped buyers/sellers at a session extreme reverse | Session extreme plus trap label | Lift of H30 inside HIGH+trap | HIGH without the trap | Panel 25,201 trap events | Hit-rate lift | `NOT SUPPORTED` | Mix ~50/50. London and NY_PM lifts fail Val or OOS. Do not retune W/threshold. |
| 18 Causal direction discovery | Frozen menu of price resolvers finds WHICH WAY | Prior-session mid and sibling resolvers inside HIGH | Automated multi-clock gate, then manual win-lift check | P(up) inside HIGH ~49–53% | Standard splits | Hit rate | `NOT SUPPORTED` | Printed `B_lead` was fragile. Several “strong” cells had negative OOS win lift. Activity ≠ direction. |
| 19 HTF horizon direction | Longer horizons rescue direction inside the activity state | Static and simple follow resolvers at longer H | Conditional direction edge | Strategy 12 activity gate | Standard splits | Hit rate | `NOT SUPPORTED` | Closed. The activity fact in 12 remains. These resolvers do not add stable conditional direction, including at longer horizons. |
| 20 Pre-HIGH displacement | Unusual displacement before HIGH predicts the remaining path | `|metric|/psr` above IS p66 | `disp_follow` / `path_follow` lift | HIGH baseline | Panel 41,159 | Hit-rate lift | `NOT SUPPORTED` | H30 median lift IS +1.3 / Val −0.2 / OOS −4.7 pp. Gate cells = 0. |
| 21 Post-HIGH first bar | First completed 1m or 5m bar after HIGH predicts the rest | Bar sign after HIGH | Conditional direction | Remaining-path baseline | Panel 65,449 | Hit-rate lift | `NOT SUPPORTED` | Soft = 0, strong = 0. |
| 22 Structural ticket | A structural “ticket” reveals direction | Ticket vs residual at entry | Incremental lift | Entry residual | Panel 61,736 | Hit-rate lift | `NOT SUPPORTED` | Soft = 0, strong = 0. H30 median lift IS +1.6 / Val −1.0 pp. End of the tested WHICH WAY stack (13–22). |
| 29 08:30–09:00 extreme | A pre-09:30 high/low of the day so far, already reversing, fades | Cash-open extreme known before 09:30 | Frozen entry/exit grid, Val+OOS survivors | Corrected causal reading; an earlier end-of-day HOD/LOD label was lookahead and was discarded | Standard splits | Grid economics | `NOT SUPPORTED` | Phase D: 0 Val+OOS survivors. The lookahead version is not evidence. |
| 30 Initial Balance | First 5m close outside the 09:30–10:30 IB continues, or a low-volume re-entry fades | IB width, break time, relative volume, candle, VWAP alignment | Chronological gates; opposite-IB and fractional stops; R targets | Unfiltered IB baseline; ES replication | Train / Inner / Val / OOS; NQ 3,476 RTH sessions, 2010-06–2026-08 | 1-point NQ RT; adverse stop-first | See note | No live strategy was validated. Low-volume re-entry fade failed Train and Inner Validation: `NOT SUPPORTED`. Tested dollar risk caps failed to keep OOS expectancy: `NOT SUPPORTED`. High-volume early continuation had positive mean net points in every gate (+0.61 / +10.83 / +10.10 / +17.78) but median stop grew from 12.1 to 91.9 points. The report leaves that cell as an unresolved tradability problem, not a promoted mechanism. |
| 31 VWAP / OR / extension fade | Stretched opens revert | VWAP distance, opening range, 5m extension | Train+Inner win rate vs payoff-implied hurdle | Payoff-implied win rate; $2 MNQ RT | Train+Inner only; Val/OOS not run because nothing passed | $2.00 | `NOT SUPPORTED` | Every listed candidate failed the Step 2 gate (combined PFs about 0.88–0.93). |
| 32 OR fade exits | A different exit saves the opening-range fade | Same OR fade, new targets | Account simulation after Train+Inner selection | Strategy 31 win-rate baseline | `fixed_2r` selected, then Validation | $2.00; $175 stop | `NOT SUPPORTED` | Validation ending equity −$10,103, PF 0.836, failed the EOD-trailing gate on 2022-03-21. OOS was not run, by rule. |
| 35 Bull / bear flags | Flag geometry adds continuation beyond the pole | 5m flag after an impulse | Frozen exits: measured move, 1R, 1.5R, 2R, EOD | Immediate impulse with no flag; same-TOD | NQ and ES, 2010–2026, frozen thresholds | Frictionless and costed; stop-first | `NOT SUPPORTED` | ES OOS PF 0.53–0.72. NQ bull-flag profit was beta: entering after the pole without a flag won more often (55% vs 41%). Bear flags failed on both markets. |
| 42 Timeframe S/R | The same 20-bar breakout or retest becomes an edge on a higher timeframe | 20-bar high/low at 1m through weekly | Positive net expectancy in both NQ and ES on IS, Val, and OOS, n≥30 OOS | Same rule on the other market and earlier splits | 2010–2026-08 | NQ 1.0 pt, ES 0.5 pt; five-bar exit | `NOT SUPPORTED` | No arm passed. Immediate breakout was OOS-negative in both markets at every timeframe. Positive NQ retest cells failed IS or ES. |
| 42b 15m S/R information | A 15m 20-bar break contains continuation information | Same 15m event, path at 1–60m, no trade | Same-signed continuation in NQ and ES on every split | Unconditional event path | Information only; no stop or target | None (information) | `NOT SUPPORTED` | No horizon passed the cross-market gate. Short breaks moved against the breakout in both markets. |
| 15m downside-break failure | Support breaks bounce more than ordinary down closes | 15m support break vs non-break down close | Break minus control inside frozen displacement/ATR bands | Matched ordinary 15m down move | NQ and ES, chronological splits | None (information) | `NOT SUPPORTED` | Banded break−control advantage changed sign. NQ OOS pooled 60m fade advantage was +0.05 pt. Bounce is ordinary post-down-move reversion. |
| 15m upside-break continuation | Resistance breaks continue more than ordinary up closes | 15m resistance break vs non-break up close | Stable positive break−control at 30m and 60m | Matched ordinary 15m up move | NQ, chronological splits | None (information) | `NOT SUPPORTED` | Required stable advantage was absent. Bands disagreed in sign. Report closes the 15m generic S/R branch. |
| 43 Compression → range → break → pullback | A detected range produces a fade or a pullback continuation | Completed 1m range, break, later pullback | 12-cell detector ranked on 2010–2018 only | The grid itself; all cells had to clear costs | N=15 and range/ATR20≤2.5 selected as least-negative, not as a winner | 1.0 pt RT; adverse stop | `NOT SUPPORTED` | All 12 selection cells lost money (about −1.24 to −0.74 pt). Combined expectancy negative in every period, including OOS −1.53. OOS continuation +0.81 pt had negative average R and PF 0.97. |
| 34 Family A tight consolidation | A compressed 30m range breakout reverts or continues | Trailing 30m range ≤ Train p25 (6.50 pt) | Train+Inner payoff-implied win rate | Feasibility hurdle | Val/OOS not run; nothing passed Step 2 | Stops already ≤ $13 | `NOT SUPPORTED` | A1/A2/A3 all failed the win-rate gate. |
| 46 Prior-day structure | After a clean break of the prior close, retracement depth orders the next return | Prior candle, separation, first return into the prior range | Frozen ordering of penetration vs forward return on 30m and 60m | Spearman of penetration vs range-normalized return; split agreement | IS 2010–2021 / Val 2022–2024 / OOS 2025–2026; 696 retracement events | None. Report states no strategy was tested | `INCONCLUSIVE` | Frozen label is `MECHANISM UNCLEAR`. Not a profitability result. |
| 48 Daily candle continuation | A qualifying Globex candle, or a frozen state machine, forecasts the next session's sign | Complete Globex OHLC | Hit rate minus the matched bull/bear base rate | Always-long and unconditional P(Up)/P(Down) | 3,400 complete sessions, 2010-06-07–2026-08-07 | None (information) | `NOT SUPPORTED` | Report: `NOT REAL`. Test 1 pooled lift IS −1.84 pp, OOS −3.21 pp. Test 2 pooled lift negative on IS, Val, and OOS. Always-long matches or beats the bullish state. |
| 49 Daily streak persistence | Multi-day same-sign streaks are longer, or continue more often, than the base rate | Bull/bear labels on the same Globex candles as 48 | Permutation of run counts; continuation after length 2 and 3 minus matched base | 10,000 label shuffles keeping bull/bear/flat counts; seed 49 | Same 3,400 sessions; streaks do not cross splits | None (information) | `NOT SUPPORTED` | Report: `NOT REAL`. Pooled length ≥3 observed 411 vs null mean 422.4 (p=0.82). L=2 continuation lift −0.39 pp; L=3 −1.44 pp. |
| Price-action top 5 | Pin bar, inside-bar breakout, engulfing, inside fake-out, three-bar reversal | 5m RTH candles | Positive net expectancy in NQ and ES on IS, Val, and OOS | Other market and earlier splits | 2010–2026; 60m exit | NQ 1.0 / ES 0.5 pt | `NOT SUPPORTED` | No pattern/side passed. Large NQ OOS cells conflicted with an earlier split or with ES. |
| 45 ICT NY SMT | NQ vs ES SMT plus FVG / structure shift during the NY window | 1m/5m/1H/4H/7H geometry and ES divergence | Chronological 60/40 backtest vs a random-session expectancy distribution | 500×400 random sessions | OOS n=16 | $2.50/side plus slippage; stop-first | `INCONCLUSIVE` | Report: inconclusive / likely no reliable edge. OOS E[R] ≈ 0.07. Sample too small to close or promote. |

## B. Volatility and state

| ID | Hypothesis | Information | Primary test | Null / baseline | Design | Friction | Verdict | Failure / result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 06 HIGH opportunity state | A causal activity state raises the chance of a large residual move | Morning range / activity vs same time of day | P(structural move ≥ 0.25×ONR) HIGH vs LOW | Same-TOD and ONR-matched control | Multi-clock, year-stable | Not a standalone trade | `SUPPORTED` | As a state detector only. LOW cuts resolve by about −25 to −35 pp. HIGH−LOW gaps about +55 to +62 pp. Mechanism is activity persistence, not direction. |
| 11 HIGH residual economics | That state is economically selective in points after cost | HIGH vs LOW absolute points and cost coverage | Mid-cost coverage and point residual | LOW / control at the same time | Standard splits | Mid cost | `NOT SUPPORTED` | ONR structural edge is real (IS H30 96.0% vs 65.8%) but absolute points do not favor HIGH (median 12.75 vs 15.25). Cost coverage delta +0.1 pp. Clocks are 96.4% adjacent. |
| 12 Multi-session opportunity | The same activity regime exists in Asia, London, NY AM, NY PM | Session activity state | Phase A discrimination; Phase B direction and economics | Baseline activity | With 13 and 14 | Mid cost in the economic phase | `SUPPORTED` as a state; closed for trading | Report `A*` then `CLOSED NO-TRADE`. Regime is real and is not directional. |
| 13 Multi-session direction | Follow or fade inside that regime | Strategy 12 gate plus follow/fade | Frozen card: stop = target = 0.25×psr, H30 | Mid-cost baseline | 16 cells | Mid cost | `NOT SUPPORTED` | 0/16 promising. London HIGH_FOLLOW OOS E_net −0.30. |
| 14 Multi-session residual economics | HIGH adds economic information beyond being in the market | Post-HIGH movement vs LOW | Cost coverage | LOW/control | Standard splits | Mid cost | `NOT SUPPORTED` | OOS coverage ~100% on both sides. Cover lift +0.0 pp. |
| 24A Vol-scaled sizing | Inverse-vol size improves a direction-agnostic book | HIGH-aware and inverse-vol size | ΔSharpe vs fixed size | Fixed-size coin-flip H=30 | IS / Val / OOS | Cost × \|size\| | `NOT SUPPORTED` | IS fixed Sharpe −1.90; inv-vol ΔSharpe −3.27. Failure is mechanical. |
| 24D Vol-harvest structure | Stop/target width or a regime filter monetizes HIGH | Direction-agnostic breakout width | HIGH-conditional monetization | Unconditional width effect | IS then Val; OOS not required to close the claim | Realistic costs | `NOT SUPPORTED` | IS partial, Val `WIDE_DOMINATES`. Wider stops help unconditionally, not because of HIGH. |
| 39 Multi-day compression | NR4/NR7 and compressed runs precede range expansion and trend days | Trailing range percentile, NR4/NR7, compression runs | Next-day normalized range, P(range ≥ 1.25×ATR), path efficiency | Uncompressed days | 3,228 RTH sessions, 2010–2026; IS/Val/OOS | Information gate; no execution model | `NOT SUPPORTED` for the expansion claim | Sign was opposite. After 4+ compressed days, next normalized range 0.821 vs 1.155, and P(large expansion) 10.5% vs 33.0%. Clustering itself is the supported fact. Path efficiency stayed ~0.46–0.49. |
| 40 Vol regime → direction | High-vol days continue, reverse, or skew the tails | Prior-day range / ATR regime | Continuation rate and tail asymmetry | Coin-flip and symmetric tails | 3,470 RTH sessions, 2010–2026 | Information | `NOT SUPPORTED` | Continuation after high vol 45.3%; after extreme vol 44.8%. Upside vs downside tail 9.9% vs 9.4%. 2025 and 2026 flipped. |
| 41 Vol as an economic filter | Trade only in high vol so fixed costs matter less | IB breakout, 15m drive, fixed-clock momentum inside vol regimes | Net points and MFE/MAE by regime | Low-vol version of the same signal | 3,470 sessions; 1.0 pt RT | 1.0 pt | `NOT SUPPORTED` | Adverse excursion scaled faster than favorable. IB breakout in extreme vol: E_net −9.47 pt, PF 0.775. High vol scaled a mediocre signal; it did not create one. |

## C. Time and calendar

| ID | Hypothesis | Information | Primary test | Null / baseline | Design | Friction | Verdict | Failure / result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 09 Scheduled events | Event impulse or fade (CPI, PPI, and the frozen event set) | Scheduled macro timestamps | Survivor cells after hostile gates | ~50% | Standard splits | Included in the gate | `NOT SUPPORTED` | Zero survivors. Best IS median 53.0% (PPI impulse continuation, n=100). |
| 36 Unconditional long | Being long NQ intraday is the edge | Clock time only | 5/15/30/60m and 09:35–15:55 vs buy-and-hold; symmetric 1R and 1.5R | Passive RTH buy-and-hold | 2010–2026; 16 years | 1.0 pt RT; stop-first | `NOT SUPPORTED` as alpha | Passive drift is real: 09:35–15:55 +2,429.75 net pts vs buy-and-hold +3,657. Short horizons are net negative after 1 pt. 0/8 symmetric stop cells positive in IS or Val. The drift fact is `SUPPORTED` and is not an intraday timing edge. |
| 37 Overnight inventory | Gap, overnight range, inventory location, or extension forecasts RTH direction | Globex information known by 09:29:59 | RTH continuation and path efficiency by frozen bins | Unconditional RTH | 3,470 paired sessions; IS 2010–2021 / Val 2022–2024 / OOS 2025–2026 | Information gate | `NOT SUPPORTED` | Gap continuation 50.8% (OOS 48.0%). Efficiency stayed 0.46–0.50 across bins. Extreme bins flipped sign across Val and OOS. |
| 38 Opening auction | The first 5/10/15 RTH minutes reveal whether the rest of the day trends | Opening efficiency and range | Remaining-session efficiency and trend-day rate from T+1 to 15:55 | Unconditional remaining session | 3,466 sessions; same splits | 1.0 pt on the gross-point check | `NOT SUPPORTED` | Remaining efficiency 0.46–0.48 across bins. High-efficiency open added +1.3 pp to trend-day rate (27.2% vs 25.9%). 15m follow-through +0.77 gross pt, −0.23 after 1 pt. |

Weekday as its own hypothesis was not given a completed primary test. Slices inside other studies are not a weekday verdict.

## D. Volume, profile, POC, LVN

OHLC volume and trade-built profiles are not order flow. They are listed here.

| ID | Hypothesis | Information | Primary test | Null / baseline | Design | Friction | Verdict | Failure / result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 27 Phase 1 | Signed OHLCV volume is directional order flow | 1m OHLCV signed-volume proxy | Spearman vs forward return, raw and residual to ret / \|ret\| / range | `ret_1m` and an orthogonalized residual | ES and NQ RTH, ~1.38M rows; Discovery / Val / OOS | Information | `NOT SUPPORTED` | Proxy vs 1m return Spearman ≈ 0.93. Residual forward association ≈ 0 (ES H15 residual OOS +0.001). Unsigned volume tracks future \|return\| / RV. Report forbids calling this order flow. |
| 33 Volume-filtered IB continuation with a hard stop cap | Keeping only upper-tertile relative volume and skipping wide stops preserves the 30 lead | IB break plus Train p66 relative volume (0.942) | Account gate on the skip-if-stop-over-$200 rule | Trades excluded by the cap | Train / Inner / Val / OOS | $2.00 MNQ | `NOT SUPPORTED` | Validation failed the EOD-trailing gate (max EOD drawdown $1,819 on 2024-04-22). Excluded wide-stop trades outperformed retained trades in Inner, Val, and OOS (OOS −12.0 pt retained vs +58.9 pt excluded). |
| 34 Family B | NQ–ES spread z-score reverts | `2*NQ − 5*ES`, 60m z, \|z\|≥2 | Same Step 2 feasibility gate as Family A | Payoff-implied win rate | Train+Inner; Val/OOS not run | $4 combined RT; $150 stop | `NOT SUPPORTED` | B4 win rate 68.25% vs required 68.77%. B5 failed by a wide margin. |
| 47 Steps 1–2 | Letter shapes (P/b/D/B) are the right profile objects | Trade-built session profiles | Frozen shape rules vs textbook labels | Sensitivity of the cuts | 96 complete non-roll sessions, trade files 2026-03-25–2026-09-16 | None | `NOT SUPPORTED` as the primary representation | P/b geometry is real as location. D/B are a poor textbook fit. Accepted HVN regions are a usable description. Valley depth is not a boundary. |
| 47 Step 3 | Prior HVN–LVN–HVN is touched next session | Prior accepted regions | Touch frequency | Descriptive | Same ~6-month trade sample | None | Touch rate only | Boundaries are frequently touched. A touch is not a reaction result. |
| 47 Step 4 | Price preferentially traverses an LVN from one HVN to the opposite HVN | Prior LVN band after an accepted-region approach | Traverse share vs geometric null | Geometry given the starting location | H30/H60/H120 and session end; N=34 at H60 | None | `NOT SUPPORTED` | H60: traverse 1, reject 19, remain 14. Decided traverse share 0.050 vs null 0.155. |
| 47 Step 5 | Price preferentially rejects at the LVN | Same boundary | Reject rate vs geometric null, including a same-minute removal | Null B and Null D | Same sample | None | `NOT SUPPORTED` | H60 observed reject 0.559 vs null 0.835 (−27.6 pp). Null D −38.0 pp. Report: `MECHANISM NOT SUPPORTED`. |
| 47 Step 6 | Prior volume location says where the next session trades | Prior POC, third shares, concentration | Measurement only | No location null in this step | 95 next-session pairs; no chronological pass/fail | None | `INCONCLUSIVE` | The preregistration had no null, p-value, or pass/fail rule. The step measured the object and stopped. |
| 47 Step 7 | Next-session trade prefers the prior POC band over a distance-matched mirror | Prior POC ±10% of prior range | Paired touch count, POC band minus mirror band | Geometric reflection of the same distance | 95 pairs; calendar split was descriptive only | None | `NOT SUPPORTED` | Primary difference −6 pairs (−0.063). Mirror was touched more often. Report: `MECHANISM NOT SUPPORTED`. The LVN/POC/volume-profile branch is closed. |
| `volume_profile` mechanism note | First trade at prior POC, VAH, or VAL has a stable 5-minute response | Trade prints, 1-tick touch | Conditional median return by approach side | Bootstrap interval of the mean; early vs late half | About six months; POC from below N=22, from above N=28 | None | `INCONCLUSIVE` | Written as a conditional description before Steps 4–7. Intervals are wide and the note says horizons were not ranked. It does not override the later nulls. |

30's VWAP-alignment filter was one cell inside the IB program. It was not a standalone VWAP study. The standalone VWAP fade is 31, and it failed.

## E. Cross-asset and external information

| ID | Hypothesis | Information | Primary test | Null / baseline | Design | Friction | Verdict | Failure / result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 08 EOD options → direction | Prior-day options positioning forecasts the next direction | Lagged EOD options features | Hostile soft/strong gates | ~50% | Standard splits; release lag enforced | Gate economics | `NOT SUPPORTED` | Zero survivors. Best IS median win 51.1%. |
| 15 ES/NQ direction resolution | ES sign, relative strength, or agreement resolves NQ | Concurrent ES/NQ state inside HIGH | Multi-clock lift | HIGH without the resolver | Panel 195,058 | Hit-rate lift | `NOT SUPPORTED` | 0 strong, 8 soft. London best IS lift +1.7 pp then negative. NY_AM IS +3.4 / Val −2.5 pp. |
| 23A COT | Lagged COT extremes add direction beyond HIGH | TFF positioning, W=104 z, p10/p90; trade only after Friday release | Incremental win rate vs HIGH-long | Strategy 12 HIGH-long | 120 cells; headline NY_AM `lev_fade` | Hit rate | `NOT SUPPORTED` | Headline incremental lift IS +2.5 / Val −7.4 / OOS −11.3 pp. 5/120 IS-strong ≈ noise rate. |
| 23D-ES | Overnight ES−NQ relative strength adds direction | Overnight ES vs NQ | Incremental vs HIGH-long | HIGH-long | IS gate; family hard stop | Hit rate | `NOT SUPPORTED` | 0 strong / 24. All H30 clocks negative vs HIGH-long. |
| 23D-ZN | Overnight ZN−NQ relative strength adds direction | Overnight ZN vs NQ | Same | HIGH-long | IS only; hard stop fired | Hit rate | `NOT SUPPORTED` | 0 strong / 24. Family 23 closed. No fifth external candidate without a new argument. |
| 23D-ZB | Overnight ZB−NQ | ZB | — | — | `ZB.FUT` was never downloaded | — | `NOT TESTED` | Absence is not a null. It is also not a reason to reopen family 23. |
| 28 ES↔NQ open lead/lag | One market's last minute leads the other into a 20–30 pt scalp | Synced 1m ES and NQ | Lag-1 correlation and a frozen 288-cell scalp grid | Contemporaneous correlation; h1/h0 | 4,175 sessions; Discovery / Val / OOS | Costs inside E_net | `NOT SUPPORTED` | Same-bar Spearman ≈ 0.835. OPEN15 es→nq lag-1 ρ ≈ 0.001. 0 Val+OOS survivors. Headline OPEN15 target 25, H15: Discovery E_net −0.93, Val −1.22. |
| 25 SPX 0DTE dealer gamma | Dealer gamma regime forecasts direction | FirmTape SPX 0DTE surface | Confirmatory IS/Val design | Regime thresholds to be frozen on Discovery | Discovery and Validation empty | Not run | `NOT TESTED` | Verdict in the report is `E` / invalid. About 33 sessions, almost all Jul–Sep 2026. Pipeline exists. This is a data blocker, not a negative result. |
| 26 Vilkov 0DTE surface | Surface shape forecasts subsequent realized vol, then NQ | 30-minute SPX/ES surface, 2016–2024 | ΔR² vs IV, time-of-day, and placebos | IV ATM + market state; residual placebos | No 2025–26 in `data_opt` | Research R², then an explicit decision not to open a trading phase | Mixed, split by claim | ES RV30/60 identity ΔR² about +0.012 / +0.014 beat placebos: a small ES variance association `SUPPORTED`. It is horizon-noisy, regime-unstable, and does not transfer cleanly to NQ. Trading claim `NOT SUPPORTED`. Do not open a rule. |

## F. Order flow, by data class

These are not interchangeable.

### F1. OHLC-derived proxies

27 is the test. Signed volume collapsed into a return transform. Unsigned volume tracked volatility. Status: `NOT SUPPORTED` as directional order flow. See section D.

### F2–F3. Top-of-book and MBP-10 style depth

| ID | Hypothesis | Information | Primary test | Null / baseline | Design | Friction | Verdict | Failure / result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 44 H01 | Resting bid/ask imbalance predicts the mid | `OBI_1` and `OBI_5` from reconstructed MBO, which is top-of-book and five-level depth | Mean rank IC ≥ 0.02, monotonic quintiles | IC = 0; one tick = 0.25 pt; 1 pt round trip | 26 sessions, 234,000 one-second rows, 2026-07-08–2026-08-12, RTH morning | Compared with 1 tick and ≥1 pt RT. No strategy built | `NOT SUPPORTED` | Killed at the information gate. `OBI_1` 1s IC +0.016, quintile spread +0.086 pt. `OBI_5` is noise by 5–15s. |
| MBO diagnostic, book side | The same book features on the corrected clock | `obi_1`, `obi_5`, spread, top depth, `depth_net_change` | Full grid of Spearman IC at 1/5/15/30/60s; early vs late half | Sign agreement and split stability. No feature was dropped after the numbers | Same 26 sessions; window 09:30–12:00 ET; 25 crossed rows excluded as anchors | Information only. Report says this sample cannot establish a multi-year edge | `INCONCLUSIVE` for a durable edge | `obi_1` stays positive at all five horizons (1s IC 0.016, sign agreement 51.3%, median forward return 0.00 pt). `depth_net_change` 1s IC 0.011, decaying toward 0. The report does not issue a kill word. The magnitudes match H01 and sit inside one tick. |

### F4. MBO / L3 aggregates already measured

| ID | Hypothesis | Information | Primary test | Null / baseline | Design | Friction | Verdict | Failure / result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 44 H02 | Aggressive delta (CVD / taker classification) predicts short-horizon continuation, including after a range control | Trade delta and L3 interactions | IC, incremental ΔIC, execution | Contaminated clock | 26 sessions | Taker spread in the retracted run | `INCONCLUSIVE` | The promotion used trades from `[t, t+1)` stored on row `t`. That run is retracted. Validation was not opened. The corrected frozen execution rule, rebuilt on all 26 sessions: n=11,514, gross −0.023, net −1.200, 0/26 days. The conclusion says a full information rerun was still required before killing sub-hypotheses. |
| MBO diagnostic, trade side | Buyer- vs seller-initiated volume predicts the next mid | `trade_imbalance`, signed volume, count imbalance, buy and sell volume | Same IC grid as the book diagnostic | Early vs late half | Corrected engine `REPLAY_ENGINE_V2_TIMESTAMP_CORRECT` | Information only | `INCONCLUSIVE` for a durable edge | 1s trade imbalance IC between −0.006 and −0.001 at every horizon, same sign in both halves. Longer windows change sign. Largest absolute IC in the whole grid is −0.020 (30s net replenishment vs 30s return) and that cell flips across halves (−0.007 vs −0.035). |
| MBO diagnostic, queue aggregates | Adds, cancels, and replenishment predict the mid | `add_signed`, `cancel_signed`, `replenish_net`, `obi_x_flow` | Same grid | Split halves | 1-second bins. Modify counts were not in the frozen store | Information only | `INCONCLUSIVE` | `replenish_net` is not horizon-stable. `obi_x_flow` stays between 0.001 and 0.005 and changes sign in one half. |
| 44 H02-D / H03 absorption | Large aggressive volume that fails to move the mid predicts a reversal | Absorption ratio vs passive depth | Reversal vs continuation | Unconditional return; trade-only vs L3 | H02-D tables exist only inside the retracted clock. H03 has a preregistration and no conclusion | Not a valid costed test | `NOT TESTED` on a valid clock | The retracted tables showed continuation, not reversal. Those numbers are not a kill and not a confirmation. |
| 44 H04 queue dynamics | Cancellation imbalance and net queue velocity predict a queue collapse | `CIR` and `NQV` at 1/5/15s | Preregistered IC gate | IC = 0 | Preregistration only | — | `NOT TESTED` | Aggregate add/cancel size was later described in the diagnostic. The H04 definitions were not run as that hypothesis. |

### F5–F6. What the MBO feed contains that those tests did not use

The book engine tracks `order_id` through add, cancel, modify, and fill. The frozen one-second store collapses that stream.

| Object | In OHLC or a profile? | Tested? |
| --- | --- | --- |
| Queue state at the inside, summed | No | Yes, as `obi_1` / top depth. Near zero, inside one tick. `NOT SUPPORTED` under H01's gate. |
| Depth behind the inside, five levels | No | Yes, as `obi_5`. `NOT SUPPORTED`. |
| Order additions and cancellations, summed per second | No | Described. `INCONCLUSIVE`, magnitudes near zero. |
| Executions and aggressor sign | A bar cannot separate them from price | Yes, as trade imbalance on the corrected clock. Near zero, not continuation. `INCONCLUSIVE` as a durable-edge claim. |
| Replenishment, summed per second | No | Described. Not stable across halves. |
| Queue depletion as a price-level sum | No | Only inside those sums. |
| Liquidity migration across prices | No | `NOT TESTED` |
| Order lifetime | No | Study R. Held-out 1s partial +0.0004. `NOT SUPPORTED`. See `mbo_orderflow/order_fate/REPORT.md`. |
| Cancel-versus-fill fate of one order | No | Study R. Held-out 1s partial +0.0004. `NOT SUPPORTED`. |
| Age and trade exposure while still resting | No | Study P. Age held-out 1s −0.0019; trade size −0.0034. `NOT SUPPORTED`. |
| Modify counts | No | Explicitly not in the frozen store. Not a scored feature. |
| Event order inside one second | No | `NOT TESTED`. One-second sums destroy it. Study P/R use event times for age and lifetime, not the intra-second sequence of other orders. |
| MBO outside 09:30–12:00 | — | `NOT TESTED`. Expanding the same features to other hours would repeat the diagnostic, not create a new object. |
| MBO joined to a prior POC touch | — | `NOT TESTED`. On these 26 dates the from-above POC touch prints near 18:00, outside the stored window. Six eligible events, zero inside 09:30–12:00. |

---

## What is exhausted, and what is only one formulation

### Price geometry

The tested formulations are `NOT SUPPORTED`: opening-range sweeps, NY-open level accept/reject, path asymmetry, post-extreme displacement, flags, the five candlestick patterns, generic 20-bar support/resistance from 1-minute through weekly, matched-move S/R continuation and failure, compression-range fade and pullback continuation, opening-range and VWAP fades under the prop gate, and Globex candle continuation and streak persistence.

Two results stay `INCONCLUSIVE`: prior-day retracement penetration (46) and the ICT SMT backtest (45, OOS n=16). Another prior-day candle rule, another flag filter, or another S/R timeframe would be a rebrand. 16A, 16B, 48, and 49 already cover sign, midpoint, qualifying continuation, and streak length. 42 already moved the same S/R rule across timeframes and the matched-move studies removed the “it was just the size of the move” excuse.

30's high-volume early IB cell is the one geometry result the report did not kill on sign. 33 then showed the positive result concentrated in stops a small account cannot hold. Treating that as a new IB parameterization is the kind of search this audit is not authorizing.

### Volatility and state

The information itself was tested, not just one nickname. Activity persistence is `SUPPORTED` (06, 12, 39's clustering sign). Direction inside that state was tested with many resolvers (07, 10, 13, 17–22, 40) and is `NOT SUPPORTED`. Using the state to size or to filter a directionless book is `NOT SUPPORTED` (11, 14, 24A, 24D, 41). A new “regime filter” on a failed entry is a rebrand.

### Time and calendar

Overnight inventory, the opening 5–15 minutes, and the frozen macro impulse/fade set are `NOT SUPPORTED` against their base rates, with splits and, where relevant, costs. Session-long passive drift is real and is not an intraday edge (36). A surprise-magnitude macro study was not run. That is `NOT TESTED`, and this repository does not currently show a surprise series that would make it testable without new data.

### Volume and profile

Bar volume as a signed-flow proxy is `NOT SUPPORTED` (27). The LVN traverse, LVN rejection, and prior-POC geometric-reflection claims are `NOT SUPPORTED` on the six-month trade sample, against geometry nulls that made the raw hit rates look real (47 Steps 4, 5, 7). Step 6's location table is `INCONCLUSIVE` because it had no null; Step 7 supplied the null and closed the claim. Another profile band, node cut, or POC distance is a reparameterization. The sample is also short of a multi-year OOS, which is a reason the branch was closed rather than a reason to retune it.

### Cross-asset

Minute ES/NQ lead, overnight ES and ZN relative strength, COT, and ES-agreement resolvers are `NOT SUPPORTED`, generally because they added nothing beyond contemporaneous movement or beyond the activity state. Dealer-gamma 0DTE is `NOT TESTED` because the archive was blocked. Vilkov's small ES variance residual does not justify an NQ rule.

### Order flow

Failing LVN rejection does not mean order flow failed. Failing POC location does not mean every volume fact failed. What did fail, or come in near zero, is specific:

- OHLC signed volume is not flow (27).
- Top-of-book and five-level imbalance do not clear an economic or IC gate (H01).
- One-second trade imbalance, depth change, and replenishment were measured on a corrected clock and are tiny (diagnostic). The diagnostic itself is `INCONCLUSIVE` as a multi-year claim because it is 26 mornings.
- Absorption and the named H04 cancellation-velocity test were not completed on a valid clock.

Order lifetime, fill-versus-cancel fate, and real-time age / trade exposure were tested under `mbo_orderflow/order_fate/PREREGISTRATION.md` and are `NOT SUPPORTED` on this sample. Liquidity migration across prices and the ordering of unrelated events inside one second remain untested. Expanding the same features to other hours, or joining them to a prior POC touch, would not introduce a new object. The frontier argument and the closed recommended question are in `RESEARCH_FRONTIER.md`.
