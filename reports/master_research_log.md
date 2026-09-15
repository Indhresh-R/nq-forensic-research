# Master Research Log

Chronological forensic program (condensed).

## Phase A — Predictive direction at NY open

Named strategies, levels, simple state→return → **failed** after causal cleanup.

## Phase B — Path asymmetry

Soft leftovers only → **B**, not strategy-ready.

## Phase C — Opportunity timing

`vol_expansion_high` / LOW wait states → **A\*** opportunity timing. Frozen permanently.

## Phase D — Direction inside HIGH

Price, ES, volume, multi-scale → **fail / B / C**. Stop stacking filters on HIGH.

## Phase E — Independent direction (no HIGH)

1. Serial dependence → **C kill**
2. Vol-standardized extremes → **B/C kill**
3. Failed movement → **B kill**
4. Expansion→retracement → **B kill** — **stop OHLC directional tree**

## Phase F — External information

1. Prior-day EOD options → intraday direction → **C kill**
2. Scheduled events → direction → **C kill**

## Phase G — Reactive + HIGH economics

1. Reactive displacement inside HIGH → **C**
2. HIGH mechanism decomposition → **persistence / already-moving**
3. Residual economics (direction-neutral) → **C standalone**

## Terminal reading

```text
Direction (tested classes)     ❌
HIGH as activity state         ✅ (late persistence)
HIGH as trade engine           ❌
```

Next research, if any, must be a **new information class or objective** — not another transform of the same killed families.

## Phase H — External sign sources under Strategy-12 HIGH (family 23) — CLOSED

1. **23A COT / TFF** — **C**. Incremental vs HIGH-long **+2.5 → −7.4 → −11.3pp** (monotonic worse-than-baseline).
2. **23D-ES overnight ES/NQ RS** — **C**. IS-only; 0 strong / 24; all H30 neg vs HIGH-long.
3. **23D-ZN overnight ZN/NQ RS** — **C**. IS-only; 0 strong / 24; all H30 neg vs HIGH-long.
   - Hard stop (pre-registered before look) **FIRED** → **family 23 closed**.
   - Data note: both “ZN/ZB” GLBX folders were **identical ZN** dumps; **ZB never present**.
4. **23D-ZB** — **UNTESTED** (data gap). Explicitly **not** a rescue after hard stop.

**Family reading:** three tested externals failed incremental sign over Strategy 12.
No 5th external without a new argument. **HOW opened** as Strategy 24.

## Phase I — HOW: sizing / stops / holding under Strategy-12 HIGH (family 24)

1. **24A vol-scaled sizing** — **C CLOSED**. Triple null; mechanical cost×|size|.
2. **24D symmetric breakout** — **C** on HIGH harvest. Decisive Val cell:
   `regime_width` − `uncond_wide` ΔSharpe **−2.79** [−3.53, −2.12]. Width helps
   unconditionally (Q1); HIGH-conditioning adds nothing (Q2). Best E still &lt; 0.
3. **24B** — **absorbed** into 24D (`regime_width` arm); no separate dossier.
4. **24C holding period** — **held** as only remaining distinct mechanism; await go-ahead.

**Locked HOW reading:** Strategy 12 activity is real but does not monetize via sizing,
width, or regime-filter of a direction-agnostic structure under costs.

See `strategies/24_HOW_sizing_execution/`.

See `strategies/23D_cross_asset_leadlag/conclusion_family_23.md`.

## Phase J — Classical Continuation Patterns: Strategy 35 (Bull & Bear Flags)

1. **35 Bull Flags and Bear Flags** — **C CLOSED**.
   - Tested on continuous NQ and ES futures (2010--2026) under causal next-open fills and adverse collision policy.
   - **ES OOS collapse**: All variants fail out-of-sample on ES (OOS PF **0.53--0.72**, $E = \mathbf{-2.67}$ to $\mathbf{-4.81}$ pts). Frictionless zero-cost test remains negative ($E = -2.17$ to $-4.31$ pts).
   - **NQ Bull vs Bear Asymmetry**: Bull flags on NQ exhibit positive drift, while Bear flags fail (Val $E = -3.19$ pts; OOS $E = -59.43$ pts on C4).
   - **Attribution benchmark**: Pure impulse breakout (pole without flag) beats flag breakout on win rate (55% vs 41%) and sample size. The "flag" consolidation provides zero incremental alpha; positive NQ long drift is entirely explained by secular tech equity beta.
   - **Family verdict: C (KILL)**.

## Phase K — Unconditional Directional Drift: Strategy 36 (NQ Long-Side Bias)

1. **36 Unconditional NQ Long Bias** — **C CLOSED (No Active Edge / Pure Passive Beta)**.
   - Evaluated 198,908 trade executions across 5m, 15m, 30m, 60m, and session close horizons from 2010 to 2026.
   - **Hostile Test Result**: Case A (NQ simply drifted upward) is true; Case B (active exploitable long edge) is FALSE.
   - **Short/Medium Horizons Net Negative**: 5m, 15m, 30m, and 60m are strictly loss-making after 1.0 pt friction. 60m active long holding from 09:35 lost **-2,753.75 net points** over 2010–2026 (Sharpe -0.179).
   - **Session Drift Dominated by Passive Holding**: 09:35 to 15:55 generated +2,429.75 pts (Sharpe 0.085), but was strictly dominated by passive RTH Buy-and-Hold (+3,657.00 pts, Sharpe 0.123). Active timing sacrificed >1,200 points of index drift and paid 58.9% in friction drag.
   - **Mode B Symmetric Structures**: 0/8 cells in IS and 0/8 in Validation showed positive expectancy.
   - **Verdict: C (KILL)**.

## Phase L — Pre-Market Structural Information: Strategy 37 (Overnight Inventory → RTH Persistence)

1. **37 Overnight Inventory → RTH Persistence** — **C CLOSED at Information Gate**.
   - Evaluated 3,470 paired overnight-RTH sessions (2010--2026) testing whether pre-market inventory (gap size, ONR ratio, inventory location pinning, extension regimes, confluence) conditions RTH trendiness.
   - **Gap Continuation is Random**: 50.8% across full sample (IS 51.3%, Val 50.7%, OOS 48.0%).
   - **Directional Efficiency Invariant**: Efficiency is 0.46–0.50 across all regimes (pinned long 0.493 vs balanced 0.472).
   - **Information Gate Failed**: No trade rules evaluated; killed at information stage to prevent curve-fitting.

## Phase M — Intraday Opening Information: Strategy 38 (Opening Auction → RTH Persistence)

1. **38 Opening Auction Information → RTH Persistence** — **C CLOSED at Information Gate**.
   - Evaluated 3,466 complete RTH sessions (2010--2026) across 5m, 10m, and 15m opening checkpoints ($T_5, T_{10}, T_{15}$).
   - **Remaining Efficiency Invariant**: High early efficiency ($\ge 0.70$) yields 0.475 remaining efficiency vs 0.464 for low early efficiency (chop open). Opening behavior does not separate trending days from chop days.
   - **Trend-Day Lift Negligible**: High efficiency open produces only a +1.3 pp lift in clean trend days (27.2% vs 25.9% unconditional).
   - **Friction Erases Gross Return**: Following a 15m high-efficiency open drive averages +0.77 gross points over the remaining session (-0.23 pts net of 1.0 pt friction).
   - **Information Gate Failed**: Killed at information stage.

## Phase N — Macro Volatility State: Strategy 39 (Multi-Day Volatility Compression → RTH Expansion/Persistence)

1. **39 Multi-Day Volatility Compression → RTH Expansion/Persistence** — **C CLOSED at Information Gate**.
   - Evaluated 3,228 complete RTH sessions (2010--2026) testing whether slow-moving volatility compression (range percentiles, NR4/NR7 patterns, contracting day runs, compression duration) conditions subsequent RTH range expansion or directional persistence.
   - **Volatility Clustering (Inertia) Inverts Classical Lore**: Rather than coiling up and exploding into trend days, compression regimes systematically lead to continued low-volatility sessions. Following 4+ days of range below median, next day normalized range is 0.821 (vs 1.155 after uncompressed days), and large expansion probability ($\ge 1.25\times$ ATR) collapses from 33.0% down to 10.5%.
   - **NR7 Days Lead to Lower Volatility**: Following an NR7 day, next day normalized range is 0.881 vs 1.053 for normal days, and trend day rate drops from 20.9% to 14.6%.
   - **Directional Efficiency Invariant**: Directional path efficiency remains flat at 0.46–0.49 across all compression regimes.
   - **Information Gate Failed**: Killed at information stage without trading rules.

## Phase O — Volatility vs Direction: Strategy 40 (Volatility Persistence → Directional Distribution)

1. **40 Volatility Persistence → Directional Distribution** — **C CLOSED (Scientific Boundary Established: Volatility Is Predictable, Direction Is NOT)**.
   - Evaluated 3,470 complete RTH sessions (2010--2026) testing whether high/low volatility regimes condition subsequent RTH direction, continuation of momentum, large tail asymmetry, or excursion bias.
   - **Directional Continuation is a Coin Flip**: Continuation rate hovers at 44.8%–49.8% across all volatility tiers (45.3% in High Vol, 44.8% in Extreme Vol). High volatility does not induce directional momentum.
   - **Tail Variance Expands Symmetrically**: In Extreme Volatility (>1.50 ATR), large up moves (9.9%) and large down moves (9.4%) occur with nearly equal frequency (+0.5% asymmetry spread). Mean upside excursion (0.653 ATR) matches downside excursion (0.651 ATR) to within +0.002 ATR.
   - **Directional Instability**: High-volatility up days flipped violently out-of-sample (-151 pts in 2025 vs +132 pts in 2026).
   - **Scientific Boundary Confirmed**: NQ volatility is predictable and persistent, but subsequent directional polarity is completely symmetric and unconditioned.

## Phase P — Volatility as Economic Filter: Strategy 41 (Volatility Regime × Signal Economics)

1. **41 Volatility Regime × Signal Economics** — **C CLOSED (Fails as Economic Trade Filter)**.
   - Evaluated 3,470 complete RTH sessions across a 2-layer design: (1) Signal-agnostic movement capacity vs fixed 1.0 pt friction, and (2) Stratifying three frozen benchmark signals (Strategy 30 IB Breakout, Strategy 38 Opening Drive, Strategy 36 Fixed-Clock).
   - **Friction Drag Ratio Drops Modestly**: Fixed 1.0 pt friction consumes 3.13% of 60m excursion in Extreme Vol vs 4.24% in Low Vol.
   - **Adverse Excursion Explodes**: While MFE expands, MAE expands faster. In Initial Balance Breakouts, MAE grows from 55.8 pts in Low Vol to 90.1 pts in Extreme Vol (MFE/MAE ratio degrades from 1.00 down to 0.82).
   - **Severe Net Dollar Losses in High Volatility**: Extreme Vol produced negative net expectancy across all benchmark families (IB Breakout: −9.47 pts net, PF 0.775; 15m Drive: −6.46 pts net, PF 0.755; Fixed-Clock: −7.44 pts net, PF 0.741).
   - **Core Finding**: Higher volatility merely scales loss variance rather than creating edge. The 1.0 pt saved on friction drag is obliterated by a +20 to +40 point blowout in trade loss size.







