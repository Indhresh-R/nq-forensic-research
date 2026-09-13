# FirmTape data acquisition status

## Blocker (2026-09-07)

FirmTape refused further wholesale snapshot downloads after ~33 distinct days:

```text
bulk archive copying — the archive is free to browse, not to download wholesale
You are over the per-visitor limit on distinct archive days.
... The block lifts on its own.
want_the_whole_series:
  licence_the_series: https://firmtape.com/pricing   (dataset licence $249/mo or $2,490/yr)
  backtest_it_here: https://firmtape.com/lab
  ask_about_bulk_access: support@firmtape.com
```

Public `/api/session/{day}` returns **closing summaries only** (not per-minute gamma). MCP was Cloudflare-blocked (browser signature) from this environment after the burst.

## What we have locally

- Minute JSON: ~33 sessions (`2024-06-03` + `2026-07-23`…`2026-09-04`) under `data/firmtape/raw/`
- Day index: 1,096 sessions `2022-04-14` … `2026-09-04` in `data/firmtape/days.txt`
- Pipeline ready: normalize + full causal experiment script

## Paths forward

1. **Wait + polite resume** — `download_firmtape_polite.py` (sequential, oldest-first, stops on block).
2. **Dataset licence** — FirmTape pricing “dataset licence”.
3. **Lab** — run pre-registered rules inside FirmTape Lab (credits); does not give us the raw minute panel.
4. **support@firmtape.com** — ask for research bulk access.

Do **not** attempt to circumvent the block (scraping HTML, rotating IPs, etc.).
