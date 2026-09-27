# Order lifetime and cancel-versus-fill fate

The definitions in `PREREGISTRATION.md` were not changed. This file records the one scoring pass.

Question verdict: `NOT SUPPORTED`

Study P, the two real-time features together: `NOT SUPPORTED`

Study R is not a real-time signal. A supported association is not an execution rule.

The decision row is the held-out 1-second partial association. A feature is supported only when that absolute value is at least 0.02 and the sign matches discovery. Horizons 5, 15, and 30 seconds are confirmatory and do not change the label.

| Study | Feature | Horizon | Discovery partial | Held-out partial | Held-out N | Mean session partial | Sessions matching pooled sign | Verdict |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| P | log(1 + age_ms) | 1 | -0.001577 | -0.001924 | 370566 | -0.001888 | 9/13 | NOT SUPPORTED |
| P | log(1 + age_ms) | 5 | -0.000223 | -0.000468 | 370370 | -0.000447 | 8/13 |  |
| P | log(1 + age_ms) | 15 | -0.002903 | 0.000539 | 369935 | 0.000578 | 6/13 |  |
| P | log(1 + age_ms) | 30 | -0.001000 | 0.000680 | 369252 | 0.000755 | 5/13 |  |
| P | log(1 + trade_size_at_price) | 1 | 0.000071 | -0.003358 | 370566 | -0.003816 | 9/13 | NOT SUPPORTED |
| P | log(1 + trade_size_at_price) | 5 | 0.000856 | -0.002563 | 370370 | -0.002493 | 8/13 |  |
| P | log(1 + trade_size_at_price) | 15 | -0.002545 | -0.000255 | 369935 | 0.000529 | 9/13 |  |
| P | log(1 + trade_size_at_price) | 30 | -0.000128 | 0.001932 | 369252 | 0.002729 | 8/13 |  |
| R | log(1 + lifetime_ms) | 1 | -0.000533 | 0.000405 | 32455909 | 0.000386 | 8/13 | NOT SUPPORTED |
| R | log(1 + lifetime_ms) | 5 | -0.000746 | 0.000933 | 32446720 | 0.000869 | 13/13 |  |
| R | log(1 + lifetime_ms) | 15 | -0.000670 | 0.000904 | 32428787 | 0.000831 | 12/13 |  |
| R | log(1 + lifetime_ms) | 30 | -0.000800 | 0.000521 | 32401377 | 0.000462 | 7/13 |  |
| R | fate, fill versus cancel | 1 | 0.000064 | 0.000408 | 32455909 | 0.000376 | 11/13 | NOT SUPPORTED |
| R | fate, fill versus cancel | 5 | -0.000112 | 0.000264 | 32446720 | 0.000205 | 9/13 |  |
| R | fate, fill versus cancel | 15 | -0.000048 | 0.000358 | 32428787 | 0.000357 | 9/13 |  |
| R | fate, fill versus cancel | 30 | 0.000143 | 0.000502 | 32401377 | 0.000466 | 10/13 |  |

## Reading

Study P does not clear the gate. On this sample, age so far and trade size already printed at the order's price add no incremental 1-second directional association beyond the four one-second controls. That closes this real-time order-fate test. It does not authorize another feature search.
