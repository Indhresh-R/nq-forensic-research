# Phase 7 — Failed-Acceptance mechanism

| period     | exc_bin   |   n |    mfe60 |    mae60 |         net |
|:-----------|:----------|----:|---------:|---------:|------------:|
| Inner      | Low       | 177 | 0.245318 | 0.33579  | -0.0904719  |
| Inner      | Mid       | 169 | 0.282106 | 0.381461 | -0.099355   |
| Inner      | High      | 152 | 0.390784 | 0.402733 | -0.0119491  |
| OOS        | Low       | 119 | 0.245058 | 0.277299 | -0.032241   |
| OOS        | Mid       |  87 | 0.323682 | 0.395943 | -0.0722616  |
| OOS        | High      |  73 | 0.375147 | 0.369814 |  0.00533318 |
| Train      | Low       | 338 | 0.22454  | 0.350724 | -0.126184   |
| Train      | Mid       | 337 | 0.306701 | 0.322971 | -0.0162698  |
| Train      | High      | 338 | 0.424947 | 0.356948 |  0.067999   |
| Validation | Low       | 190 | 0.251357 | 0.310598 | -0.0592409  |
| Validation | Mid       | 189 | 0.303387 | 0.357818 | -0.0544315  |
| Validation | High      | 149 | 0.392328 | 0.347578 |  0.0447494  |

Event: at least two completed five-minute closes outside IB, then a later five-minute close back inside. Outcome starts next one-minute open and measures 60-minute normalized reversal MFE/MAE.
