# NQ/MNQ opening-range fade -- exit-structure follow-up results

## Step 2: Train + Inner Validation

All candidates: stop $175 <= $200; Train 1,491 >= 100; Inner Validation 689 >= 50.

| candidate             | eligible   | gate                                  |   required_win_rate |   stop_dollars |    n |   net_dollars |   win_rate |   payoff |   profit_factor |   trades_per_month |   largest_day_dollars |   largest_day_pct |   train_n |   inner_n |
|:----------------------|:-----------|:--------------------------------------|--------------------:|---------------:|-----:|--------------:|-----------:|---------:|----------------:|-------------------:|----------------------:|------------------:|----------:|----------:|
| fixed_2r              | True       | pass                                  |            0.482048 |            175 | 2180 |       6121    |   0.500917 | 1.08264  |        1.08662  |            15.6835 |               348     |         0.0568535 |      1491 |       689 |
| fixed_1p5r            | True       | pass                                  |            0.495301 |            175 | 2180 |       2565.5  |   0.502294 | 1.02691  |        1.03638  |            15.6835 |               260.5   |         0.10154   |      1491 |       689 |
| fixed_1r              | True       | pass                                  |            0.510205 |            175 | 2180 |        772    |   0.511009 | 0.967702 |        1.01128  |            15.6835 |               173     |         0.224093  |      1491 |       689 |
| partial_midpoint_1p5r | False      | win rate 0.5716 below required 0.5779 |            0.577886 |            175 | 2180 |       -909.75 |   0.57156  | 0.73725  |        0.983526 |            15.6835 |               270.375 |       nan         |      1491 |       689 |
| timeboxed_1r_30m      | False      | win rate 0.4491 below required 0.4885 |            0.488538 |            175 | 2180 |      -4149    |   0.449083 | 1.05497  |        0.859966 |            15.6835 |               173     |       nan         |      1491 |       689 |

## Selection

Selected fixed_2r: combined Train+Inner win rate 50.1%, payoff 1.08R. Win rate held versus baseline: no (50.1% vs 70.1%).

## Step 4: Validation account simulation

{
  "status": "fail",
  "rule": "overall EOD trailing",
  "date": "2022-03-21",
  "ending_equity": -10103.0,
  "max_eod_drawdown": 12651.5,
  "n": 694,
  "net_dollars": -10103.0,
  "win_rate": 0.3861671469740634,
  "payoff": 1.3287697528337268,
  "profit_factor": 0.8359396567122976,
  "trades_per_month": 19.27777777777778,
  "largest_day_dollars": 348.0,
  "largest_day_pct": NaN
}

Validation failed the $1,000 EOD-trailing gate on the date shown above; OOS was therefore not run. The reported largest-day percentage is incomplete because Validation total profit is negative.

## Baseline comparison

Strategy 31 combined Train+Inner baseline: 70.1% win rate and 0.38R payoff. Removing the midpoint cap did not preserve the high win rate.

Passes 5%ers $25K constraints: no. Win rate held vs. strategy 31 baseline: no (50.1% vs. 70.1%).
