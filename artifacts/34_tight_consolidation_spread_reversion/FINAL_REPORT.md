# Tight-consolidation breakout & NQ--ES spread reversion

## Frozen specification

Family A uses **X = 6.50 NQ points**, the Train (2010--2018) 25th percentile of completed trailing 30-minute high-low ranges. Family B uses 1 MNQ + 1 MES ($2/NQ point, $5/ES point), a **$4.00 combined round-trip cost**, spread `2*NQ - 5*ES`, 60-minute rolling z-score and |z| >= 2.0.

## Step 2 -- Train + Inner Validation ranking

### Family A

| candidate           | family   | eligible   | gate                                  |   required_win_rate |   max_stop_dollars |   train_n |   inner_n |    n |   net_dollars |   win_rate |   payoff |   profit_factor |   trades_per_month |   largest_day_dollars |   largest_day_pct |
|:--------------------|:---------|:-----------|:--------------------------------------|--------------------:|-------------------:|----------:|----------:|-----:|--------------:|-----------:|---------:|----------------:|-------------------:|----------------------:|------------------:|
| A3_inside_volume_1R | A        | False      | win rate 0.5496 below required 0.7239 |            0.723921 |                 13 |       700 |        66 |  766 |       -1429.5 |   0.549608 | 0.589444 |        0.719293 |            6.66087 |                  11   |               nan |
| A2_inside_1p5R      | A        | False      | win rate 0.4269 below required 0.5546 |            0.554588 |                 13 |      1208 |        99 | 1307 |       -2986   |   0.426932 | 0.962326 |        0.716927 |           10.9832  |                  17.5 |               nan |
| A1_inside_1R        | A        | False      | win rate 0.5272 below required 0.6793 |            0.679329 |                 13 |      1208 |        99 | 1307 |       -2917.5 |   0.527161 | 0.601995 |        0.671156 |           10.9832  |                  11   |               nan |

### Family B

| candidate            | family   | eligible   | gate                                  |   required_win_rate |   max_stop_dollars |   train_n |   inner_n |    n |   net_dollars |   win_rate |   payoff |   profit_factor |   trades_per_month |   largest_day_dollars |   largest_day_pct |
|:---------------------|:---------|:-----------|:--------------------------------------|--------------------:|-------------------:|----------:|----------:|-----:|--------------:|-----------:|---------:|----------------:|-------------------:|----------------------:|------------------:|
| B4_zmean_nearer_1p5R | B        | False      | win rate 0.6825 below required 0.6877 |            0.687735 |                150 |      1641 |       775 | 2416 |      -230.754 |   0.682533 | 0.460067 |        0.989114 |            17.3813 |                   221 |               nan |
| B5_z_fixed_1p5R      | B        | False      | win rate 0.3891 below required 0.5044 |            0.504371 |                150 |      1641 |       775 | 2416 |    -16459     |   0.389073 | 0.990875 |        0.631045 |            17.3813 |                   221 |               nan |

## Step 2 gate audit

| candidate            | family   |   max_stop_dollars |   train_n |   inner_n |   win_rate |   required_win_rate | eligible   | gate                                  | $150_stop_gate   | Train_100_gate   | Inner_50_gate   | feasibility_gate   |
|:---------------------|:---------|-------------------:|----------:|----------:|-----------:|--------------------:|:-----------|:--------------------------------------|:-----------------|:-----------------|:----------------|:-------------------|
| B4_zmean_nearer_1p5R | B        |                150 |      1641 |       775 |   0.682533 |            0.687735 | False      | win rate 0.6825 below required 0.6877 | True             | True             | True            | False              |
| A3_inside_volume_1R  | A        |                 13 |       700 |        66 |   0.549608 |            0.723921 | False      | win rate 0.5496 below required 0.7239 | True             | True             | True            | False              |
| A2_inside_1p5R       | A        |                 13 |      1208 |        99 |   0.426932 |            0.554588 | False      | win rate 0.4269 below required 0.5546 | True             | True             | True            | False              |
| A1_inside_1R         | A        |                 13 |      1208 |        99 |   0.527161 |            0.679329 | False      | win rate 0.5272 below required 0.6793 | True             | True             | True            | False              |
| B5_z_fixed_1p5R      | B        |                150 |      1641 |       775 |   0.389073 |            0.504371 | False      | win rate 0.3891 below required 0.5044 | True             | True             | True            | False              |

All candidates passed the $150 stop and 100/50 trade-count gates. Every candidate failed the payoff-implied win-rate feasibility gate shown above. This is an aggregate Train + Inner Validation rule, so no single breach date/trade exists.

## Natural-stop diagnostic

Family A's raw (uncapped) stop distribution is below. The $150 gate was applied to each trade; it is not a replacement stop. | candidate           |   count |   share_under_150 |   median |   max |
|:--------------------|--------:|------------------:|---------:|------:|
| A1_inside_1R        |    1312 |                 1 |     11   |    13 |
| A2_inside_1p5R      |    1312 |                 1 |     11   |    13 |
| A3_inside_volume_1R |     770 |                 1 |     11.5 |    13 |

All Family A signals were already below $150 (maximum $13); the gate did no disqualifying work and there is no excluded wide-stop tail. Family B has a predeclared fixed $150 spread stop, so it likewise has no retained-versus-excluded stop tail.

## Selection and account gate

No eligible candidate cleared Step 2; Validation and OOS were not run.

Step 4: incomplete because Step 3 selected no candidate. Step 5: not run by the preregistered rule.

Passes 5%ers $25K constraints: no. Family A viable: no eligible candidate. Family B viable: no eligible candidate.