# NQ/MNQ mean-reversion fade -- results

## Step 2 ranking

| candidate               | eligible   | gate                                      |   combined_pf |   combined_net |   largest_day_pct |   Train_n |   Train_net_dollars |   Train_win_rate |   Train_payoff |   Train_profit_factor |   Train_trades_per_month |   Train_largest_day_pct |   Inner Validation_n |   Inner Validation_net_dollars |   Inner Validation_win_rate |   Inner Validation_payoff |   Inner Validation_profit_factor |   Inner Validation_trades_per_month |   Inner Validation_largest_day_pct |
|:------------------------|:-----------|:------------------------------------------|--------------:|---------------:|------------------:|----------:|--------------------:|-----------------:|---------------:|----------------------:|-------------------------:|------------------------:|---------------------:|-------------------------------:|----------------------------:|--------------------------:|---------------------------------:|------------------------------------:|-----------------------------------:|
| vwap_fade_1p5r          | False      | win rate 0.459 below payoff-implied 0.478 |      0.925835 |       -4184    |               nan |       400 |               149.5 |         0.4825   |        1.08345 |              1.01017  |                  6.45161 |               1.49164   |                  648 |                       -4333.5  |                    0.444444 |                  1.12014  |                         0.896112 |                             18      |                                nan |
| opening_range_fade      | False      | win rate 0.701 below payoff-implied 0.721 |      0.904328 |       -4692.25 |               nan |      1490 |              -504   |         0.720134 |        0.37879 |              0.97468  |                 14.466   |             nan         |                  689 |                       -4188.25 |                    0.658926 |                  0.443223 |                         0.856269 |                             19.1389 |                                nan |
| vwap_fade_1r            | False      | win rate 0.484 below payoff-implied 0.513 |      0.887982 |       -6004    |               nan |       400 |               590.5 |         0.4975   |        1.05253 |              1.04206  |                  6.45161 |               0.250635  |                  648 |                       -6594.5  |                    0.475309 |                  0.919869 |                         0.833293 |                             18      |                                nan |
| high_state_vwap_fade_1r | False      | win rate 0.472 below payoff-implied 0.503 |      0.885564 |       -3954.5  |               nan |       325 |              1628.5 |         0.507692 |        1.12312 |              1.15822  |                  5.32787 |               0.0908812 |                  401 |                       -5583    |                    0.44389  |                  0.964545 |                         0.769906 |                             11.1389 |                                nan |
| extension_5m_fade_1p5r  | False      | win rate 0.477 below payoff-implied 0.508 |      0.883428 |       -7804    |               nan |      1622 |             -3114.5 |         0.480888 |        0.96267 |              0.891784 |                 15.7476  |             nan         |                  771 |                       -4689.5  |                    0.46952  |                  0.991008 |                         0.877127 |                             21.4167 |                                nan |

## Selection / account gates

```json
{
  "cost_dollars_round_trip": 2.0,
  "selection": null,
  "step4": "incomplete",
  "step5": "not run"
}
```