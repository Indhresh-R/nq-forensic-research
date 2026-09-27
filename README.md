# NQ Forensic Research

A reproducible research program for Nasdaq-100 E-mini futures (NQ), focused on testing market hypotheses under causal, chronological, and execution-aware controls.

This is a **research program, not a collection of claimed profitable strategies**.

## Research question

    What information exists?
            ↓
    Can it be measured causally?
            ↓
    Does it survive chronological validation?
            ↓
    Does it contain incremental information?
            ↓
    Can the path be executed after realistic cost?
            ↓
    If not, what exactly was falsified?

The repository deliberately preserves negative and inconclusive results.

## What is in the repository

| Area | Purpose |
|---|---|
| [research_framework/](research_framework/) | Causal rules, data definitions, splits, execution assumptions, audit checklist, verdict rubric |
| [strategies/](strategies/) | Numbered research dossiers, from engine validation through current market-state/path studies |
| [reports/](reports/) | Program-level summaries, research log, rejected hypotheses, MBO audits |
| [common/](common/) | Shared session, path, split, and data-loading infrastructure |
| [mbo_orderflow/](mbo_orderflow/) | MBO/L3 reconstruction and microstructure research infrastructure |
| [volume_profile/](volume_profile/) | Trade-derived volume-profile research and mechanism tests |
| [research/](research/) | Supporting research material and framework work |
| [artifacts/](artifacts/) | Generated research outputs grouped by study |
| [archive/legacy_scripts/](archive/legacy_scripts/) | Historical engines retained for forensic reproducibility |

## Research progression

The numbered studies are chronological research objects rather than 65 independent trading systems.

    01–05  Initial NY-open / price-direction hypotheses
    06–14  Activity states and attempts to monetize them
    15–24  Direction resolution, external information, and HOW/economics
    25–34  Options, cross-market, opening, and volatility hypotheses
    35–41  Classical continuation, drift, inventory, auction, and volatility tests
    42–49  Timeframe structure, event transitions, MBO, SMT, profile, daily-state tests
    50–51  Wyckoff / VSA framework translation
    52–59  Market-state, regime, transition, and first-passage research
    60–61  Cost-feasibility and refusal-map constraints
    62–63  Value-area / first-passage descriptive and null testing
    64      Morning environment atlas
    65      C1 drive-exterior continuation sleeve

The program has moved from **feature → return** testing toward:

    framework → context → event → reaction → mechanism → falsification

## Current evidence boundary

The repository does **not** establish a universal statement such as “NQ direction is unpredictable.”

It establishes narrower, testable boundaries:

- Multiple pre-specified short-horizon directional information classes failed their chronological/OOS gates.
- Activity and volatility states can be statistically real without supplying a stable directional sign.
- Several apparent trading edges disappeared under causal fills, matched controls, cross-market replication, or realistic friction.
- Strategies 55–59 exposed repeated path problems: destination/touch statistics did not translate into a cost-positive holdable path.
- Strategy 60 formalized a cost-feasibility boundary for the simple event→hold / 1R-extension class.
- Strategy 61 locked explicit refusal rules to prevent reopening killed mechanisms through retuning.
- Strategies 62–64 broaden the research object toward value-area structure and morning-environment description.
- Strategy 65 tested a frozen C1 drive-exterior continuation sleeve; it was killed because IS mean net expectancy remained negative, despite positive later splits.

These are research conclusions, not claims of a live trading system.

## Research controls

- no lookahead or same-bar outcome contamination
- frozen rules before later-period evaluation
- chronological IS / Validation / OOS testing
- matched nulls and controls where appropriate
- adverse/through-stop execution handling
- realistic transaction-cost assumptions
- yearly stability checks
- explicit information-gate vs strategy-gate distinctions
- preregistration and hard-stop rules for selected branches
- preservation of failed hypotheses

See [research_framework/README.md](research_framework/README.md).

## Selected research areas

### Market-state research
[Strategy 52 — Market State Census](strategies/52_market_state_census/) and [Strategy 64 — Morning Environment Atlas](strategies/64_environment_atlas/) move the program toward describing the environment before attaching a trade hypothesis.

### Microstructure
[Strategy 44 — MBO Orderflow](strategies/44_mbo_orderflow/) and [mbo_orderflow/](mbo_orderflow/) investigate order-book information that is not present in OHLC bars or a volume profile. The limited MBO sample is treated as a separate evidence class rather than as a multi-year conclusion.

### Market-profile / value-area research
[Strategy 47 — Volume Profile](strategies/47_volume_profile_shapes/), [Strategy 62](strategies/62_patrick_build_fields/), and [Strategy 63](strategies/63_patrick_strict_va_first_passage/) test value-area objects with explicit nulls rather than assuming profile geometry implies a trade.

### Path / first-passage research
[Strategies 55–59](strategies/) examine destination, barrier, rebreak, rejection, and first-passage behavior. Their postmortem is [RESEARCH_POSTMORTEM_52_59.md](strategies/RESEARCH_POSTMORTEM_52_59.md).

## Start here

1. **[Research overview](reports/research_overview.md)** — the shortest explanation of the full program.
2. **[Strategy summary](reports/strategy_summary.md)** — detailed historical verdict table.
3. **[Rejected hypotheses](reports/rejected_hypotheses.md)** — what was tested and why it was closed.
4. **[Master research log](reports/master_research_log.md)** — chronological development.
5. **[Research inventory](RESEARCH_INVENTORY.md)** — experiment-level audit record.
6. **[Research frontier](RESEARCH_FRONTIER.md)** — what information classes remain open or have been closed.

## Data

Large source datasets are intentionally not committed to the repository.

The core OHLC research uses continuous NQ 1-minute data, with some studies also using ES, trade/MBO data, or specialized datasets. Each dossier records the data and split relevant to that study.

## Reproducibility

Most study dossiers contain a hypothesis or charter, rules/preregistration, code, results, and a conclusion or completion report.

Shared research primitives live in [common/](common/).

## Important limitation

A research repository can demonstrate research process, statistical discipline, software engineering, and falsification quality. It cannot by itself establish that a strategy will remain profitable in live markets.

## License

See [LICENSE](LICENSE).