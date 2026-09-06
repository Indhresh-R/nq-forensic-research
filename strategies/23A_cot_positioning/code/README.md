# Code — 23A COT Positioning

```bash
# 1) Pull + cache TFF + build lagged features (needs CFTC_APP_TOKEN in .env optional)
python strategies/23A_cot_positioning/code/build_cot_features.py

# 2) IS-only panel + metrics (default)
python strategies/23A_cot_positioning/code/run_23a_test.py --stage IS
```

Env (gitignored `.env`):

```text
CFTC_APP_TOKEN=...
CFTC_APP_SECRET=...   # optional; token usually sufficient for SODA
```

Artifacts via `common.paths.art` → `artifacts/23A_cot_positioning/`.
