# Data notes — Vilkov panels

## Provenance

- Repo: https://github.com/vilkovgr/0dte-strategies
- Sample claim: SPXW 0DTE, Sep 2016 – Jan 2026
- `data_opt.parquet` LFS oid size ≈ **263 MB** (~3.5M rows claimed)
- Raw Cboe bars **not** redistributed; panels are derived/interpolated

## Acquisition blocker (2026-09)

GitHub LFS budget exceeded on upstream. `data/data_opt.parquet` on GitHub is an LFS **pointer** (134 bytes), not the panel.

**Action:** obtain the real parquet offline (author / mirror / prior clone with LFS cache) and drop into `data/vilkov/`.

## Tier-2 fallback

Rebuild via their Massive or ThetaData ingest (`code/ingest/`) if you have API access — then we still audit timestamps the same way.

## Design implication

Per their reading guide, option cross-section is from **30-minute Cboe bars**. Confirm on real `data_opt` timestamps before registering +1m/+5m tests.
