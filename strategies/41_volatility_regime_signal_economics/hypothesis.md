# Strategy 41: Hypothesis -- Volatility Regime × Signal Economics

## 1. Motivation & Theoretical Premise
In financial microstructure and algorithmic trading, transaction costs are fixed per ticket (in NQ futures: 1.0 point round-trip = $20.00).

Strategies 35–40 established:
1. **Strategy 39**: Volatility clusters predictably (ranges expand to $1.21\times$ ATR after high vol, and shrink to $0.85\times$ ATR after low vol).
2. **Strategy 40**: Volatility clustering does **not** provide directional polarity (direction remains a 50/50 coin flip, variance expands symmetrically).

This leads to the fundamental economic hypothesis of Strategy 41:
> **Even if volatility regime contains zero directional information, it can act as a powerful economic filter by expanding available market price excursion relative to fixed transaction friction.**

## 2. The Mechanics of Friction Drag
In a low-volatility session:
- Average 60-minute excursion might be only 20–25 points.
- A 1.0 point round-trip friction consumes **4.0% to 5.0%** of total movement.
- Any statistical edge that is slightly positive gross ($E_{gross} = +0.50$ pts) is crushed into net negative territory ($E_{net} = -0.50$ pts).

In a high-volatility session:
- Average 60-minute excursion expands to 60–100+ points.
- The same 1.0 point friction consumes only **1.0% to 1.5%** of available movement.
- The fixed cost hurdle becomes relatively negligible.

## 3. The Counter-Hypothesis (The Hostile Null)
Does higher volatility actually improve signal net profitability, or does it merely magnify risk?
If a trading strategy enters high volatility, adverse price excursions (MAE) and stop-out whipsaws will expand at the exact same rate as favorable excursions (MFE). If the loss size expands in exact lockstep with win size, the profit factor and net edge may remain flat or degrade.

Strategy 41 tests whether higher volatility improves **net economic survivability** or simply inflates nominal variance.
