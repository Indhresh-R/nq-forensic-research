# 00. Engine sanity (buy-and-hold + SMA 50/200)

**Not a research strategy / not Strategy 23.** Pipeline verification only.

| Check | What it proves |
|-------|----------------|
| Buy-and-hold identity | P&L = last close − first close |
| SMA hand recompute | Rolling averages match numpy means |
| Cross dates vs ^NDX | Signal calendar ≈ public Nasdaq-100 |

```bash
python strategies/00_engine_sanity/code/run_nq_engine_sanity.py
```

Report: [`artifacts/00_engine_sanity/nq_engine_sanity_report.md`](../../artifacts/00_engine_sanity/nq_engine_sanity_report.md)
