# NQ/MNQ volume-filtered continuation -- hard-capped stop results

Frozen Train upper-tertile relative-volume threshold: **0.941735**. Cost: **$2.00 MNQ round trip**.

## Step 2 ranking

| candidate                      | eligible   | gate   |   required_win_rate |   max_stop_dollars |   train_n |   inner_n |   n |   net_dollars |   win_rate |   payoff |   profit_factor |   trades_per_month |   largest_day_dollars |   largest_day_pct |
|:-------------------------------|:-----------|:-------|--------------------:|-------------------:|----------:|----------:|----:|--------------:|-----------:|---------:|----------------:|-------------------:|----------------------:|------------------:|
| skip_if_original_stop_over_200 | True       | pass   |            0.367874 |             199.75 |       387 |       161 | 548 |        2968   |   0.410584 |  1.75557 |         1.22292 |            4.21538 |                   335 |         0.112871  |
| hard_150_2r                    | True       | pass   |            0.430301 |             150    |       387 |       167 | 554 |        3171.5 |   0.465704 |  1.3659  |         1.19055 |            4.26154 |                   298 |         0.0939618 |
| hard_200_1p5r                  | True       | pass   |            0.446051 |             200    |       387 |       167 | 554 |        2088   |   0.467509 |  1.27224 |         1.11699 |            4.26154 |                   298 |         0.14272   |
| hard_200_2r                    | True       | pass   |            0.443716 |             200    |       387 |       167 | 554 |        2030.5 |   0.463899 |  1.2842  |         1.11125 |            4.26154 |                   398 |         0.196011  |
| hard_150_1r                    | True       | pass   |            0.459991 |             150    |       387 |       167 | 554 |        1556.5 |   0.474729 |  1.2132  |         1.09646 |            4.26154 |                   148 |         0.0950851 |

## Candidate 5: skip-if-wide-stop

Kept 740/787 original signals; skipped 47 (6.0%).

| group    | period           |   n |   avg_net_points |   avg_net_dollars |
|:---------|:-----------------|----:|-----------------:|------------------:|
| retained | Inner Validation | 161 |         7.76009  |          15.5202  |
| retained | OOS              |  40 |       -12.0344   |         -24.0688  |
| retained | Train            | 387 |         0.606266 |           1.21253 |
| retained | Validation       | 152 |         3.75658  |           7.51316 |
| excluded | Inner Validation |   6 |        93.1042   |         186.208   |
| excluded | OOS              |  29 |        58.9138   |         117.828   |
| excluded | Validation       |  12 |        90.4375   |         180.875   |

Yes: the excluded wide-stop trades materially outperformed retained trades in Inner Validation (+93.10 vs +7.76 points), Validation (+90.44 vs +3.76), and OOS (+58.91 vs -12.03). The evidence says the apparent edge is concentrated in trades this account cannot take.

## Selection and Validation

{
  "research_pass_date": "2026-09-14",
  "cost_dollars_round_trip": 2.0,
  "relative_volume_train_p66": 0.9417349767057853,
  "selection": "skip_if_original_stop_over_200",
  "step4": {
    "status": "fail",
    "rule": "overall EOD trailing",
    "date": "2024-04-22",
    "ending_equity": 1142.0,
    "max_eod_drawdown": 1819.0,
    "worst_daily_pnl": -199.75,
    "consistency_pass": true,
    "n": 152,
    "net_dollars": 1142.0,
    "win_rate": 0.42105263157894735,
    "payoff": 1.5413664777242146,
    "profit_factor": 1.120993801981247,
    "trades_per_month": 4.3428571428571425,
    "largest_day_dollars": 337.0,
    "largest_day_pct": 0.29509632224168125
  },
  "step5": "not run"
}

Selection gates: all five candidates passed the $200 maximum-stop and 100/50 trade-count gates; the payoff-implied feasibility result is in the ranking table. Validation: per-trade stop pass (maximum $199.75); daily-loss pass (worst day $-199.75); EOD trailing **fail** on 2024-04-22; profit-target fail ($1142.00 vs $1,500); consistency pass (largest day 29.5% of Validation profit).

Original uncapped 0.50×IB/2R mean net points: Train +0.61, Inner +10.83, Validation +10.10, OOS +17.78. Selected skip_if_original_stop_over_200: combined win 41.1%, payoff 1.76R, 548 trades, 4.22 trades/month.

The capped selection failed Validation, so Step 5 OOS was not run.

Passes 5%ers $25K constraints: no. Edge survived stop capping: no. Is the edge and this account fundamentally incompatible: yes.
