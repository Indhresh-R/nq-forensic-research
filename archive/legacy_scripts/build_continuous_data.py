import glob
import os
import re
import pandas as pd
import databento as db
import numpy as np

print("--- Building Continuous Datasets for NQ and ES ---")

# 1. Load NQ Data
print("Loading NQ data from CSV files...")
nq_files = glob.glob('GLBX-20260809-KQVC5EJ6WC/*.csv')
single_nq_files = []
for f in nq_files:
    base = os.path.basename(f)
    symbol_part = base.split('.ohlcv-1m.')[1].replace('.csv', '')
    if '-' not in symbol_part:
        single_nq_files.append((symbol_part, f))

nq_dfs = []
for sym, fpath in single_nq_files:
    df = pd.read_csv(fpath, usecols=['ts_event', 'open', 'high', 'low', 'close', 'volume', 'symbol'])
    nq_dfs.append(df)

nq_all = pd.concat(nq_dfs, ignore_index=True)
nq_all['ts_event'] = pd.to_datetime(nq_all['ts_event'])
nq_all['date'] = nq_all['ts_event'].dt.date

print(f"Total NQ raw 1m rows: {len(nq_all):,}")

# Volume-based front month selection per day for NQ
daily_nq_vol = nq_all.groupby(['date', 'symbol'])['volume'].sum().reset_index()
# Find symbol with max volume per date
front_nq_symbols = daily_nq_vol.sort_values(['date', 'volume'], ascending=[True, False]).groupby('date').first().reset_index()
front_nq_map = set(zip(front_nq_symbols['date'], front_nq_symbols['symbol']))

# Filter nq_all to active front contract
nq_front = pd.merge(nq_all, front_nq_symbols[['date', 'symbol']], on=['date', 'symbol'], how='inner')
nq_front = nq_front.drop_duplicates(subset=['ts_event']).sort_values('ts_event').reset_index(drop=True)
print(f"Continuous NQ front-month 1m rows: {len(nq_front):,}")
print(f"NQ date range: {nq_front['ts_event'].min()} to {nq_front['ts_event'].max()}")

# 2. Load ES Data
print("Loading ES data from DBN zst file...")
store = db.DBNStore.from_file('GLBX-20260827-CLPF3V6C3T/glbx-mdp3-20100606-20260826.ohlcv-1m.dbn.zst')
es_all = store.to_df().reset_index()
es_all['ts_event'] = pd.to_datetime(es_all['ts_event'])
es_all['date'] = es_all['ts_event'].dt.date

# Filter out spread symbols if any (e.g. '-' in symbol)
es_all = es_all[~es_all['symbol'].astype(str).str.contains('-')]

print(f"Total ES raw 1m rows: {len(es_all):,}")

daily_es_vol = es_all.groupby(['date', 'symbol'])['volume'].sum().reset_index()
front_es_symbols = daily_es_vol.sort_values(['date', 'volume'], ascending=[True, False]).groupby('date').first().reset_index()

es_front = pd.merge(es_all, front_es_symbols[['date', 'symbol']], on=['date', 'symbol'], how='inner')
es_front = es_front.drop_duplicates(subset=['ts_event']).sort_values('ts_event').reset_index(drop=True)
print(f"Continuous ES front-month 1m rows: {len(es_front):,}")
print(f"ES date range: {es_front['ts_event'].min()} to {es_front['ts_event'].max()}")

# Save continuous data to parquet for ultra-fast loading
nq_front[['ts_event', 'open', 'high', 'low', 'close', 'volume', 'symbol']].to_parquet('nq_1m_continuous.parquet')
es_front[['ts_event', 'open', 'high', 'low', 'close', 'volume', 'symbol']].to_parquet('es_1m_continuous.parquet')
print("Continuous parquets saved successfully!")
