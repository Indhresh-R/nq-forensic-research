# Research Overview

## One-line description

A chronological NQ futures research program that tests market hypotheses from causal definition through out-of-sample evidence and execution feasibility, while preserving failed branches and explicit research boundaries.

## The program in one picture

    Initial price hypotheses
            ↓
    NY-open behavior
            ↓
    Activity / opportunity states
            ↓
    Direction information tests
            ↓
    External information + execution economics
            ↓
    Options / cross-market / volatility
            ↓
    Microstructure / MBO
            ↓
    Classical framework translation
            ↓
    Market-state and transition research
            ↓
    Path / first-passage research
            ↓
    Cost feasibility
            ↓
    Refusal map
            ↓
    Value-area / environment research
            ↓
    Current research boundary

## Methodological core

    Hypothesis
      → mechanical definition
      → decision-time information set
      → frozen test
      → null / matched control
      → chronological validation
      → OOS confirmation
      → execution stress
      → verdict

The key distinction is between **information evidence** and **trade evidence**. A state can be real while failing to provide direction, and a path statistic can be real while failing to provide a cost-positive executable path.

## What the program has learned

### 1. Causal execution matters

Early research exposed cases where apparently strong backtest results depended on non-causal fills, especially through-stop behavior. Those results were re-tested with causal execution assumptions rather than preserved as headline performance.

### 2. Activity is not direction

The HIGH / activity branch found a repeatable increase in the probability of large residual movement. Subsequent direction-resolution tests did not establish a stable incremental sign resolver. The activity finding is therefore kept as a **state observation**, not a standalone trade claim.

### 3. Volatility can be persistent without resolving polarity

Several studies found persistent activity/volatility behavior while directional continuation remained unstable. This prevents volatility clustering from being relabeled as directional alpha.

### 4. More features did not solve the information problem

The research tested price geometry, session states, ES/NQ relationships, options/event information, volume-derived measures, profile objects, and MBO summaries. When a family failed its information gate, later parameter shopping was generally prohibited.

### 5. Path matters after the signal

Strategies 55–59 shifted the question from “does the destination occur?” to “can the path be held and paid for?” The repeated result was that destination/touch asymmetries did not survive into a simple cost-positive hold.

### 6. Cost feasibility can close a research class

Strategy 60 formalized whether the observed first-passage and MFE/MAE geometry could clear a 1.0-point round-trip cost under the tested event→hold class. It classified that class as structurally underwater.

### 7. Refusal rules are research output

Strategy 61 turned repeated failures into explicit constraints: do not reopen killed events by retuning targets, horizons, barrier definitions, or destination menus without a genuinely new argument.

### 8. Latest work is environment and structure, not a claimed live system

Strategies 62–64 investigate value-area fields, strict first-passage nulls, and a morning environment atlas. Strategy 65 tests a frozen C1 drive-exterior continuation sleeve and is killed at the IS gate because mean net expectancy remained below zero.

## Current evidence boundary

The strongest defensible statement is not “we found no strategy.”

> The tested directional and simple event→hold classes have repeatedly failed under increasingly strict causal, chronological, matched-control, and cost-aware tests. The remaining research value is in identifying genuinely new information or execution mechanisms, not in repeatedly retuning the same closed families.

That is the purpose of the repository's inventory, frontier, preregistrations, and refusal map.

## Repository map

- [RESEARCH_FRAMEWORKS/](../RESEARCH_FRAMEWORKS/) — framework-discovery and source-translation work
- [research/](../research/) — supporting research material
- [research_framework/](../research_framework/) — formal testing methodology and audit controls
- [strategies/](../strategies/) — chronological research dossiers
- [reports/](./) — program-level summaries and logs
- [mbo_orderflow/](../mbo_orderflow/) — MBO infrastructure
- [volume_profile/](../volume_profile/) — profile research infrastructure
- [scripts/](../scripts/) — shared utility/orchestration scripts
- [archive/](../archive/) — historical engines retained for forensic reference

## Recommended reading path

README → Research Overview → Research Framework → Strategy Summary → one or two representative dossiers → Rejected Hypotheses / Frontier.

A reviewer does not need to read 65 dossiers to understand the program.