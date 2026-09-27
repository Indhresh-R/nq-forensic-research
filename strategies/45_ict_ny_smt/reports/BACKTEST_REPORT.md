# ICT NY SMT Discretionary Backtest Report

## Verdict (plain language)

**INCONCLUSIVE / likely no reliable edge.** OOS trades=16 is too small for confidence. OOS E[R]=0.07220720280055126. Treat any positive IS result as fragile.

## Assumptions I made

- Timestamps in parquet are UTC; converted to America/New_York with DST via zoneinfo.
- session_date = CME Globex day labeled by the calendar date of the RTH portion (bars from 18:00 ET map to next calendar date), matching repo convention.
- Daily candle = 18:00 -> 17:00 ET (mins_from_anchor < 23h). Known after its close_ts.
- 7H NY filter uses ONLY bin0 (18:00–01:00) as C1 and bin1 (01:00–08:00) as C2. The 08:00–15:00 bin is NOT used for morning entries because it has not closed by 08:30–11:30 (lookahead).
- Daily bias: C2 vs C1 continuation/reversal direction; if neither, fallback to C2 close vs open.
- Daily FVG reaction: CONFIRMED if price traded into FVG and a subsequent 1m close resumed through the FVG in bias direction (last event wins if both resume and against occurred). UNCONFIRMED if closed against. Untested/pending/no_fvg require HTF 1H C1->C2 in bias direction before trades.
- Protected level: latest 1H engulfing (prior opposite candle, close beyond its extreme); fallback to 4H. Invalidation on wick through level.
- Variant A SMT: require 1H SMT (NQ vs ES) AND 5m SMT confirmation, both at/inside a 1H FVG, live during 1H C2 (after C1 close, before C2 close).
- SMT swings: fractal with lookback=3 each side; usable only after right-side bars close (confirmed_at).
- Bearish SMT = one market HH vs prior swing high, other fails; bullish = one LL, other fails.
- Variant B entry: 5m market structure shift (sweep prior confirmed swing and close beyond) OR bullish/bearish close inside 1H FVG.
- Entry at confirming 5m candle close (decision_ts = close_ts - 1m).
- Same-bar SL+TP -> SL first. Force flat at 15:55 ET. Costs: $2.50/side + N ticks slippage/side.
- Liquidity TP: nearest equal high/low (2-tick tol) or nearest confirmed 15m swing beyond entry; fallback 2R if none.
- IS/OOS = chronological 60/40 by session_date count. No parameter choice on OOS.
- Random baseline samples 400 sessions/run × 500 runs; not identical trade-count matched — used as expectancy distribution reference.
- MNQ P&L uses $2/point with same commission (conservative vs typical MNQ fees).
- Do not tune parameters to fit; defaults from the brief only.

## Data quality

- **NQ**: 2010-06-06 18:00:00-04:00 -> 2026-08-07 16:59:00-04:00, bars=4788194, dupes=0, gaps>5m=8595, gaps>60m=4650, tz=UTC
- **ES**: 2010-06-06 18:00:00-04:00 -> 2026-08-26 19:59:00-04:00, bars=4916275, dupes=0, gaps>5m=6470, gaps>60m=4626, tz=UTC

Aligned range: 2010-06-06 18:00:00-04:00 -> 2026-08-07 16:59:00-04:00

## Daily FVG state counts (sessions evaluated)

```
{
  "no_fvg": 581,
  "untested": 1119,
  "unconfirmed": 179,
  "confirmed": 1728,
  "touched_pending": 4
}
```

## Primary cell (fixed a priori: Variant A, SL-A, TP 2R)

- ALL: {'label': 'primary_all', 'n_trades': 39, 'win_rate': 0.3076923076923077, 'avg_win': 384.1666666666667, 'avg_loss': -248.5185185185185, 'avg_r': -0.24214107595571996, 'expectancy_r': -0.24214107595571996, 'expectancy_usd': -53.84615384615385, 'profit_factor': 0.6870342771982116, 'total_pnl_nq': -2100.0, 'max_dd_usd': -4535.0, 'max_dd_pct': -59.0, 'longest_lose_streak': 6, 'sharpe': -1.9765137421869565, 'sortino': -3.602054001445759, 'pct_profitable_months': 0.34285714285714286, 'avg_duration_min': 38.1025641025641}
- IS: {'label': 'primary_is', 'n_trades': 23, 'win_rate': 0.2608695652173913, 'avg_win': 185.0, 'avg_loss': -145.0, 'avg_r': -0.46081813943834343, 'expectancy_r': -0.46081813943834343, 'expectancy_usd': -58.91304347826087, 'profit_factor': 0.45030425963488846, 'total_pnl_nq': -1355.0, 'max_dd_usd': -1615.0, 'max_dd_pct': -59.0, 'longest_lose_streak': 6, 'sharpe': -4.503948888929017, 'sortino': -6.825300182066618, 'pct_profitable_months': 0.3157894736842105, 'avg_duration_min': 48.52173913043478}
- OOS: {'label': 'primary_oos', 'n_trades': 16, 'win_rate': 0.375, 'avg_win': 583.3333333333334, 'avg_loss': -424.5, 'avg_r': 0.07220720280055126, 'expectancy_r': 0.07220720280055126, 'expectancy_usd': -46.5625, 'profit_factor': 0.8244994110718492, 'total_pnl_nq': -745.0, 'max_dd_usd': -3470.0, 'max_dd_pct': -6.3090909090909095, 'longest_lose_streak': 4, 'sharpe': -1.1536998043399103, 'sortino': -2.705293458603618, 'pct_profitable_months': 0.375, 'avg_duration_min': 23.125}
- Bootstrap E[R] ALL: {'mean': -0.2337413378288589, 'lo': -0.6437271581915667, 'hi': 0.21776130748693076}
- Bootstrap E[R] OOS: {'mean': 0.06616690027582499, 'lo': -0.5145245135540772, 'hi': 0.8065635793344671}
- Random baseline percentile (E[R]): 0.8

## Full grid (see `results/grid_summary.csv`)

| variant   | sl_mode   | tp_mode   |   n_trades |   win_rate |   expectancy_r |   expectancy_usd |   profit_factor |   total_pnl_nq |   max_dd_usd |
|:----------|:----------|:----------|-----------:|-----------:|---------------:|-----------------:|----------------:|---------------:|-------------:|
| A         | A         | liquidity |         39 |   0.435897 |    -0.0399145  |       -28.3333   |        0.669656 |        -1105   |      -2005   |
| A         | A         | 1R        |         39 |   0.461538 |    -0.190859   |       -68.3333   |        0.532046 |        -2665   |      -3810   |
| A         | A         | 2R        |         39 |   0.307692 |    -0.242141   |       -53.8462   |        0.687034 |        -2100   |      -4535   |
| A         | A         | 3R        |         39 |   0.25641  |    -0.22867    |       -25.3846   |        0.85558  |         -990   |      -4625   |
| A         | B         | liquidity |         52 |   0.326923 |    -0.393553   |       -58.4135   |        0.376283 |        -3037.5 |      -3560   |
| A         | B         | 1R        |         52 |   0.403846 |    -0.390322   |       -73.0769   |        0.460993 |        -3800   |      -4835   |
| A         | B         | 2R        |         52 |   0.230769 |    -0.521072   |       -67.1154   |        0.56592  |        -3490   |      -5470   |
| A         | B         | 3R        |         52 |   0.173077 |    -0.5925     |      -102.885    |        0.387521 |        -5350   |      -5660   |
| A         | C         | liquidity |         27 |   0.555556 |    -0.0704144  |       -53.4259   |        0.374187 |        -1442.5 |      -1685   |
| A         | C         | 1R        |         27 |   0.296296 |    -0.324153   |      -164.444    |        0.356522 |        -4440   |      -5350   |
| A         | C         | 2R        |         27 |   0.259259 |    -0.252727   |      -134.63     |        0.489466 |        -3635   |      -5110   |
| A         | C         | 3R        |         27 |   0.259259 |    -0.213375   |      -112.963    |        0.571629 |        -3050   |      -5090   |
| B         | A         | liquidity |        183 |   0.420765 |    -0.0519129  |         9.35792  |        1.12792  |         1712.5 |      -3107.5 |
| B         | A         | 1R        |        183 |   0.442623 |    -0.247431   |        -0.245902 |        0.997859 |          -45   |      -4045   |
| B         | A         | 2R        |        183 |   0.349727 |    -0.139624   |        13.6612   |        1.09037  |         2500   |      -6345   |
| B         | A         | 3R        |        183 |   0.284153 |    -0.127652   |        -9.80874  |        0.94278  |        -1795   |     -11285   |
| B         | B         | liquidity |        227 |   0.414097 |    -0.0575604  |       -26.9714   |        0.740874 |        -6122.5 |      -8950   |
| B         | B         | 1R        |        227 |   0.480176 |    -0.139064   |       -12.4009   |        0.901315 |        -2815   |      -8305   |
| B         | B         | 2R        |        227 |   0.365639 |    -0.0302858  |        -4.44934  |        0.972669 |        -1010   |      -7165   |
| B         | B         | 3R        |        227 |   0.273128 |    -0.0595027  |       -21.8502   |        0.883732 |        -4960   |     -15255   |
| B         | C         | liquidity |        101 |   0.60396  |    -0.00538229 |        15.9158   |        1.26234  |         1607.5 |      -2787.5 |
| B         | C         | 1R        |        101 |   0.514851 |    -0.0248578  |        24.0099   |        1.12313  |         2425   |      -4165   |
| B         | C         | 2R        |        101 |   0.435644 |    -0.111584   |       -32.6238   |        0.861787 |        -3295   |      -6545   |
| B         | C         | 3R        |        101 |   0.415842 |    -0.137894   |       -28.4653   |        0.880383 |        -2875   |      -6880   |
| C         | A         | liquidity |         51 |   0.490196 |    -0.0413733  |       -26.8627   |        0.665854 |        -1370   |      -2135   |
| C         | A         | 1R        |         51 |   0.490196 |    -0.135433   |       -51.6667   |        0.657124 |        -2635   |      -4375   |
| C         | A         | 2R        |         51 |   0.333333 |    -0.15504    |       -60.3922   |        0.68491  |        -3080   |      -6535   |
| C         | A         | 3R        |         51 |   0.254902 |    -0.203562   |       -41.3725   |        0.794247 |        -2110   |      -6405   |
| C         | B         | liquidity |         69 |   0.376812 |    -0.326233   |       -58.6957   |        0.349398 |        -4050   |      -4175   |
| C         | B         | 1R        |         69 |   0.434783 |    -0.290622   |       -48.1159   |        0.604527 |        -3320   |      -4090   |
| C         | B         | 2R        |         69 |   0.289855 |    -0.331187   |       -40.8696   |        0.718282 |        -2820   |      -3850   |
| C         | B         | 3R        |         69 |   0.202899 |    -0.466364   |      -103.623    |        0.386266 |        -7150   |      -7255   |
| C         | C         | liquidity |         38 |   0.631579 |    -0.0474577  |       -38.0263   |        0.487589 |        -1445   |      -1652.5 |
| C         | C         | 1R        |         38 |   0.315789 |    -0.304324   |      -151.974    |        0.34635  |        -5775   |      -6840   |
| C         | C         | 2R        |         38 |   0.289474 |    -0.227258   |      -127.632    |        0.464384 |        -4850   |      -6480   |
| C         | C         | 3R        |         38 |   0.289474 |    -0.172981   |      -109.079    |        0.542242 |        -4145   |      -6340   |
| D         | A         | liquidity |        149 |   0.422819 |    -0.164539   |        -6.12416  |        0.900788 |         -912.5 |      -3092.5 |
| D         | A         | 1R        |        149 |   0.47651  |    -0.137996   |        -7.41611  |        0.942553 |        -1105   |      -5305   |
| D         | A         | 2R        |        149 |   0.302013 |    -0.26285    |         4.22819  |        1.0258   |          630   |      -8220   |
| D         | A         | 3R        |        149 |   0.261745 |    -0.205606   |        29.5638   |        1.1717   |         4405   |      -9730   |
| D         | B         | liquidity |        186 |   0.33871  |    -0.34477    |       -32.4731   |        0.524128 |        -6040   |      -7225   |
| D         | B         | 1R        |        186 |   0.413978 |    -0.314365   |       -37.7957   |        0.677671 |        -7030   |      -9400   |
| D         | B         | 2R        |        186 |   0.27957  |    -0.369944   |       -13.3333   |        0.9      |        -2480   |      -8585   |
| D         | B         | 3R        |        186 |   0.22043  |    -0.377199   |       -11.9624   |        0.917209 |        -2225   |     -11475   |
| D         | C         | liquidity |        109 |   0.486239 |    -0.0816391  |       -25.8486   |        0.626821 |        -2817.5 |      -3367.5 |
| D         | C         | 1R        |        109 |   0.412844 |    -0.22922    |       -89.3119   |        0.592763 |        -9735   |     -10670   |
| D         | C         | 2R        |        109 |   0.376147 |    -0.133833   |       -83.8532   |        0.641217 |        -9140   |     -10645   |
| D         | C         | 3R        |        109 |   0.348624 |    -0.174334   |       -92.2018   |        0.616778 |       -10050   |     -12125   |

### IS vs OOS (all cells)

| variant   | sl_mode   | tp_mode   | split   |   n_trades |   expectancy_r |   total_pnl_nq |
|:----------|:----------|:----------|:--------|-----------:|---------------:|---------------:|
| A         | A         | liquidity | IS      |         23 |    -0.114469   |         -340   |
| A         | A         | liquidity | OOS     |         16 |     0.0672568  |         -765   |
| A         | A         | 1R        | IS      |         23 |    -0.373862   |        -1225   |
| A         | A         | 1R        | OOS     |         16 |     0.0722072  |        -1440   |
| A         | A         | 2R        | IS      |         23 |    -0.460818   |        -1355   |
| A         | A         | 2R        | OOS     |         16 |     0.0722072  |         -745   |
| A         | A         | 3R        | IS      |         23 |    -0.490285   |        -1545   |
| A         | A         | 3R        | OOS     |         16 |     0.147403   |          555   |
| A         | B         | liquidity | IS      |         31 |    -0.444524   |         -590   |
| A         | B         | liquidity | OOS     |         21 |    -0.318312   |        -2447.5 |
| A         | B         | 1R        | IS      |         31 |    -0.507244   |        -1680   |
| A         | B         | 1R        | OOS     |         21 |    -0.217722   |        -2120   |
| A         | B         | 2R        | IS      |         31 |    -0.604018   |        -2145   |
| A         | B         | 2R        | OOS     |         21 |    -0.398626   |        -1345   |
| A         | B         | 3R        | IS      |         31 |    -0.691576   |        -2430   |
| A         | B         | 3R        | OOS     |         21 |    -0.446246   |        -2920   |
| A         | C         | liquidity | IS      |         16 |    -0.0657897  |         -655   |
| A         | C         | liquidity | OOS     |         11 |    -0.0771412  |         -787.5 |
| A         | C         | 1R        | IS      |         16 |    -0.34206    |        -1765   |
| A         | C         | 1R        | OOS     |         11 |    -0.298108   |        -2675   |
| A         | C         | 2R        | IS      |         16 |    -0.27956    |        -1685   |
| A         | C         | 2R        | OOS     |         11 |    -0.213698   |        -1950   |
| A         | C         | 3R        | IS      |         16 |    -0.283466   |        -1690   |
| A         | C         | 3R        | OOS     |         11 |    -0.111425   |        -1360   |
| B         | A         | liquidity | IS      |        109 |     0.0216706  |          462.5 |
| B         | A         | liquidity | OOS     |         74 |    -0.1603     |         1250   |
| B         | A         | 1R        | IS      |        109 |    -0.289278   |        -1450   |
| B         | A         | 1R        | OOS     |         74 |    -0.185792   |         1405   |
| B         | A         | 2R        | IS      |        109 |    -0.135803   |         1755   |
| B         | A         | 2R        | OOS     |         74 |    -0.145251   |          745   |
| B         | A         | 3R        | IS      |        109 |    -0.0974861  |         1315   |
| B         | A         | 3R        | OOS     |         74 |    -0.172087   |        -3110   |
| B         | B         | liquidity | IS      |        136 |     0.0359168  |        -1247.5 |
| B         | B         | liquidity | OOS     |         91 |    -0.197262   |        -4875   |
| B         | B         | 1R        | IS      |        136 |    -0.182989   |        -1705   |
| B         | B         | 1R        | OOS     |         91 |    -0.0734179  |        -1110   |
| B         | B         | 2R        | IS      |        136 |    -0.0161313  |           60   |
| B         | B         | 2R        | OOS     |         91 |    -0.0514399  |        -1070   |
| B         | B         | 3R        | IS      |        136 |     0.00863178 |        -1420   |
| B         | B         | 3R        | OOS     |         91 |    -0.16133    |        -3540   |
| B         | C         | liquidity | IS      |         60 |     0.0487533  |         4130   |
| B         | C         | liquidity | OOS     |         41 |    -0.0846051  |        -2522.5 |
| B         | C         | 1R        | IS      |         60 |    -0.0196744  |         1695   |
| B         | C         | 1R        | OOS     |         41 |    -0.0324434  |          730   |
| B         | C         | 2R        | IS      |         60 |    -0.0708573  |          755   |
| B         | C         | 2R        | OOS     |         41 |    -0.171183   |        -4050   |
| B         | C         | 3R        | IS      |         60 |    -0.107663   |          490   |
| B         | C         | 3R        | OOS     |         41 |    -0.182135   |        -3365   |
| C         | A         | liquidity | IS      |         30 |    -0.0982239  |         -505   |
| C         | A         | liquidity | OOS     |         21 |     0.0398418  |         -865   |
| C         | A         | 1R        | IS      |         30 |    -0.232864   |         -395   |
| C         | A         | 1R        | OOS     |         21 |     0.00375547 |        -2240   |
| C         | A         | 2R        | IS      |         30 |    -0.232864   |         -330   |
| C         | A         | 2R        | OOS     |         21 |    -0.0438636  |        -2750   |
| C         | A         | 3R        | IS      |         30 |    -0.388789   |        -1235   |
| C         | A         | 3R        | OOS     |         21 |     0.0610471  |         -875   |
| C         | B         | liquidity | IS      |         41 |    -0.380573   |         -760   |
| C         | B         | liquidity | OOS     |         28 |    -0.246664   |        -3290   |
| C         | B         | 1R        | IS      |         41 |    -0.391279   |        -1285   |
| C         | B         | 1R        | OOS     |         28 |    -0.143232   |        -2035   |
| C         | B         | 2R        | IS      |         41 |    -0.391279   |        -1425   |
| C         | B         | 2R        | OOS     |         28 |    -0.243196   |        -1395   |
| C         | B         | 3R        | IS      |         41 |    -0.47243    |        -2385   |
| C         | B         | 3R        | OOS     |         28 |    -0.457482   |        -4765   |
| C         | C         | liquidity | IS      |         22 |    -0.0675517  |         -635   |
| C         | C         | liquidity | OOS     |         16 |    -0.0198285  |         -810   |
| C         | C         | 1R        | IS      |         22 |    -0.202331   |        -1450   |
| C         | C         | 1R        | OOS     |         16 |    -0.444563   |        -4325   |
| C         | C         | 2R        | IS      |         22 |    -0.111422   |        -1250   |
| C         | C         | 2R        | OOS     |         16 |    -0.386532   |        -3600   |
| C         | C         | 3R        | IS      |         22 |    -0.0688082  |        -1135   |
| C         | C         | 3R        | OOS     |         16 |    -0.316219   |        -3010   |
| D         | A         | liquidity | IS      |         89 |    -0.210831   |        -1585   |
| D         | A         | liquidity | OOS     |         60 |    -0.0958722  |          672.5 |
| D         | A         | 1R        | IS      |         89 |    -0.198552   |        -1575   |
| D         | A         | 1R        | OOS     |         60 |    -0.0481708  |          470   |
| D         | A         | 2R        | IS      |         89 |    -0.443629   |        -1980   |
| D         | A         | 2R        | OOS     |         60 |     0.00530607 |         2610   |
| D         | A         | 3R        | IS      |         89 |    -0.45449    |        -2595   |
| D         | A         | 3R        | OOS     |         60 |     0.163571   |         7000   |
| D         | B         | liquidity | IS      |        111 |    -0.428768   |        -2825   |
| D         | B         | liquidity | OOS     |         75 |    -0.220454   |        -3215   |
| D         | B         | 1R        | IS      |        111 |    -0.399025   |        -3605   |
| D         | B         | 1R        | OOS     |         75 |    -0.189067   |        -3425   |
| D         | B         | 2R        | IS      |        111 |    -0.486112   |        -4195   |
| D         | B         | 2R        | OOS     |         75 |    -0.198017   |         1715   |
| D         | B         | 3R        | IS      |        111 |    -0.590996   |        -6065   |
| D         | B         | 3R        | OOS     |         75 |    -0.0607795  |         3840   |
| D         | C         | liquidity | IS      |         65 |    -0.0977351  |         -937.5 |
| D         | C         | liquidity | OOS     |         44 |    -0.0578609  |        -1880   |
| D         | C         | 1R        | IS      |         65 |    -0.372453   |        -6140   |
| D         | C         | 1R        | OOS     |         44 |    -0.0176256  |        -3595   |
| D         | C         | 2R        | IS      |         65 |    -0.267456   |        -4665   |
| D         | C         | 2R        | OOS     |         44 |     0.0635636  |        -4475   |
| D         | C         | 3R        | IS      |         65 |    -0.311385   |        -4995   |
| D         | C         | 3R        | OOS     |         44 |     0.028127   |        -5055   |

## Charts

- `reports/figures/equity_primary.png`
- `reports/figures/drawdown_primary.png`
- `reports/figures/monthly_heatmap_primary.png`
- `reports/figures/equity_primary_OOS.png`

## Overfitting / sample-size flags

- Large discrete grid (variants × SL × TP) without hierarchical testing inflates false positives.
- SMT + multi-filter stack produces sparse trades; small-n OOS is expected.
- Several rule ambiguities were resolved with conservative causal defaults (see assumptions).
- Random baseline is not trade-count matched; use as rough expectancy reference only.

Runtime: 7296.4s
