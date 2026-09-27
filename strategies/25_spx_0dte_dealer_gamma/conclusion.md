# Conclusion

**Verdict: `E` — Invalid due to data/causality problems**

FirmTape blocked wholesale minute-archive download after ~33 distinct session JSON files (`bulk archive copying — the archive is free to browse, not to download wholesale`). Local minute coverage is almost entirely Jul–Sep 2026 (+ one 2024-06-03 day). Discovery (2022–2023) and Validation (2024) are empty for confirmatory design; regime thresholds cannot be frozen on Discovery.

Pipeline, causality rules, hostile tests, and report scaffolding are ready under `strategies/25_spx_0dte_dealer_gamma/`. Re-run after full archive acquisition:

```bash
python strategies/25_spx_0dte_dealer_gamma/code/download_firmtape_polite.py
python strategies/25_spx_0dte_dealer_gamma/code/normalize_firmtape.py
set PYTHONPATH=.
python strategies/25_spx_0dte_dealer_gamma/code/run_spx_dealer_gamma_experiment.py
```

See `DATA_BLOCKER.md` for acquisition options (wait/resume, dataset licence $249/mo, Lab, support@firmtape.com).
