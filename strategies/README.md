# Strategy Research Dossiers

The numbered folders are **chronological research objects**, not a leaderboard of trading strategies.

Each dossier should answer:

1. What was the hypothesis?
2. What information was available at decision time?
3. What was frozen before validation/OOS?
4. What was the null or baseline?
5. What execution/cost assumptions were used?
6. What happened in IS / Validation / OOS?
7. What is the narrowest defensible verdict?

## Research families

| Range | Research family |
|---|---|
| 00–05 | Engine validation and initial NY-open / price hypotheses |
| 06–14 | Activity-state discovery and monetization attempts |
| 15–24 | Direction resolution, external information, and execution/economics |
| 25–34 | Options, cross-market, opening, volatility, and intraday structure |
| 35–41 | Continuation, drift, inventory, auction, and volatility information |
| 42–49 | Timeframe structure, event transitions, MBO, SMT, profile, daily-state tests |
| 50–51 | Wyckoff / VSA framework translation |
| 52–59 | Market-state, regime, transition, and first-passage research |
| 60–61 | Cost-feasibility and refusal constraints |
| 62–63 | Value-area / first-passage research |
| 64–65 | Environment atlas and a frozen continuation sleeve |

## Important distinction

A SUPPORTED or A* result can mean that a **market state or information property was detected**. It does not automatically mean an executable strategy was validated.

Conversely, KILL, NOT SUPPORTED, CLOSED, and INCONCLUSIVE results are retained because they constrain the future research space.

See [the master strategy summary](../reports/strategy_summary.md) and [the research framework](../research_framework/README.md).