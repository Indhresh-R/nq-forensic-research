import pandas as pd
import numpy as np
import time

print("1. Loading raw continuous parquets...", flush=True)
t0 = time.time()
df_nq = pd.read_parquet('nq_1m_continuous.parquet')
df_es = pd.read_parquet('es_1m_continuous.parquet')
print(f"Loaded in {time.time() - t0:.2f}s", flush=True)

print("2. Merging NQ and ES...", flush=True)
t0 = time.time()
df = pd.merge(
    df_nq[['ts_event', 'open', 'high', 'low', 'close', 'volume']],
    df_es[['ts_event', 'open', 'high', 'low', 'close', 'volume']],
    on='ts_event',
    suffixes=('_nq', '_es'),
    how='inner'
).sort_values('ts_event').reset_index(drop=True)
print(f"Merged ({len(df):,} rows) in {time.time() - t0:.2f}s", flush=True)

print("3. Fast Timezone conversion to NY...", flush=True)
t0 = time.time()
ts_ny = pd.to_datetime(df['ts_event']).dt.tz_convert('America/New_York')
df['year'] = ts_ny.dt.year.astype(np.int16)
df['day_id'] = ts_ny.dt.date  # Ultra fast!
df['ny_minutes'] = (ts_ny.dt.hour * 60 + ts_ny.dt.minute).astype(np.int16)
print(f"Timezone converted in {time.time() - t0:.2f}s", flush=True)

print("4. Calculating Daily VWAP & SD...", flush=True)
t0 = time.time()
df['hl2'] = (df['high_nq'] + df['low_nq']) * 0.5
df['pv'] = df['hl2'] * df['volume_nq']
df['v'] = df['volume_nq']
df['pv2'] = df['hl2'] * df['hl2'] * df['volume_nq']

df['cum_pv'] = df.groupby('day_id', observed=True)['pv'].cumsum()
df['cum_v'] = df.groupby('day_id', observed=True)['v'].cumsum()
df['cum_pv2'] = df.groupby('day_id', observed=True)['pv2'].cumsum()

vwap = df['cum_pv'] / df['cum_v']
variance = np.maximum(df['cum_pv2'] / df['cum_v'] - vwap * vwap, 0.0)
stdev = np.sqrt(variance)

dev1, dev2, dev3 = 1.28, 2.01, 2.51
df['upper1'] = (vwap + dev1 * stdev).astype(np.float32)
df['lower1'] = (vwap - dev1 * stdev).astype(np.float32)
df['upper2'] = (vwap + dev2 * stdev).astype(np.float32)
df['lower2'] = (vwap - dev2 * stdev).astype(np.float32)
df['upper3'] = (vwap + dev3 * stdev).astype(np.float32)
df['lower3'] = (vwap - dev3 * stdev).astype(np.float32)
print(f"VWAP calculated in {time.time() - t0:.2f}s", flush=True)

print("5. Calculating Pivots and Signals...", flush=True)
t0 = time.time()
h = df['high_nq'].to_numpy(dtype=np.float32)
l = df['low_nq'].to_numpy(dtype=np.float32)
c = df['close_nq'].to_numpy(dtype=np.float32)
n = len(df)

pivot_h = np.full(n, np.nan, dtype=np.float32)
pivot_l = np.full(n, np.nan, dtype=np.float32)

is_ph = (h[2:-2] > h[:-4]) & (h[2:-2] > h[1:-3]) & (h[2:-2] > h[3:-1]) & (h[2:-2] > h[4:])
is_pl = (l[2:-2] < l[:-4]) & (l[2:-2] < l[1:-3]) & (l[2:-2] < l[3:-1]) & (l[2:-2] < l[4:])

ph_indices = np.where(is_ph)[0] + 4
pl_indices = np.where(is_pl)[0] + 4

pivot_h[ph_indices] = h[ph_indices - 2]
pivot_l[pl_indices] = l[pl_indices - 2]

df['pivot_h'] = pd.Series(pivot_h).ffill()
df['pivot_l'] = pd.Series(pivot_l).ffill()

df['bearish_mss'] = (c < df['pivot_l']) & (np.roll(c, 1) >= df['pivot_l'])
df['bullish_mss'] = (c > df['pivot_h']) & (np.roll(c, 1) <= df['pivot_h'])

df['bull_fvg'] = df['low_nq'] > df['high_nq'].shift(2)
df['bear_fvg'] = df['high_nq'] < df['low_nq'].shift(2)

df['last_bull_fvg'] = np.where(df['bull_fvg'], df['high_nq'].shift(2), np.nan)
df['last_bear_fvg'] = np.where(df['bear_fvg'], df['low_nq'].shift(2), np.nan)

df['last_bull_fvg'] = df['last_bull_fvg'].ffill()
df['last_bear_fvg'] = df['last_bear_fvg'].ffill()

df['bearish_ifvg'] = (c < df['last_bull_fvg']) & (np.roll(c, 1) >= df['last_bull_fvg'])
df['bullish_ifvg'] = (c > df['last_bear_fvg']) & (np.roll(c, 1) <= df['last_bear_fvg'])
print(f"Pivots and signals calculated in {time.time() - t0:.2f}s", flush=True)

print("6. Filtering Session Bars (06:00 to 12:00 NY) & Saving Cache...", flush=True)
t0 = time.time()
session_df = df[(df['ny_minutes'] >= 360) & (df['ny_minutes'] < 720)].copy().reset_index(drop=True)
# Convert day_id to string for parquet serialization
session_df['day_id'] = session_df['day_id'].astype(str)
session_df.to_parquet('session_cached.parquet')
print(f"Cache saved ({len(session_df):,} rows) in {time.time() - t0:.2f}s", flush=True)
