# Code

| Script | Role |
|--------|------|
| `download_firmtape.py` | Download all archive JSON (preserve raw) |
| `normalize_firmtape.py` | Minute panel Parquet |
| `run_spx_dealer_gamma_experiment.py` | Full causal / hostile experiment |

```bash
cd NQ-2
python strategies/25_spx_0dte_dealer_gamma/code/download_firmtape.py
python strategies/25_spx_0dte_dealer_gamma/code/normalize_firmtape.py
python strategies/25_spx_0dte_dealer_gamma/code/run_spx_dealer_gamma_experiment.py
```
