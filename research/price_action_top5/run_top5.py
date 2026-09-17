"""Frozen 5m RTH price-action top-five payoff screen."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT))
from common.nq_session import load_nq,load_es
from common.splits import split_of
OUT=ROOT/"artifacts"/"price_action_top5"; OUT.mkdir(parents=True,exist_ok=True)
COST={"NQ":1.,"ES":.5}; OPEN=570; CLOSE=955

def bars5(base):
 x=base[(base.ny_min>=OPEN)&(base.ny_min<CLOSE)].copy(); x["bucket"]=(x.ny_min-OPEN)//5
 return x.groupby(["session_date","bucket"],sort=True).agg(end=("ts","last"),open=("open","first"),high=("high","max"),low=("low","min"),close=("close","last"),n=("close","size"),year=("year","last"),key=("session_date","last")).reset_index(drop=True).query("n==5").reset_index(drop=True)

def signals(g):
 o,h,l,c=(g[x].to_numpy(float) for x in ("open","high","low","close")); ans=[]
 for i in range(3,len(g)-12):
  rng=h[i]-l[i]; body=abs(c[i]-o[i]);
  if rng<=0: continue
  # pin bar
  if c[i]>o[i] and c[i]>=l[i]+2*rng/3 and min(o[i],c[i])-l[i]>=2*body and c[i]<c[i-3]: ans.append((i,"pin_bar",1))
  if c[i]<o[i] and c[i]<=l[i]+rng/3 and h[i]-max(o[i],c[i])>=2*body and c[i]>c[i-3]: ans.append((i,"pin_bar",-1))
  # inside breakout, i is confirming bar
  if h[i-1]<h[i-2] and l[i-1]>l[i-2]:
   if c[i]>h[i-2]: ans.append((i,"inside_breakout",1))
   if c[i]<l[i-2]: ans.append((i,"inside_breakout",-1))
  # body engulfing
  if c[i-1]<o[i-1] and c[i]>o[i] and o[i]<=c[i-1] and c[i]>=o[i-1]: ans.append((i,"engulfing",1))
  if c[i-1]>o[i-1] and c[i]<o[i] and o[i]>=c[i-1] and c[i]<=o[i-1]: ans.append((i,"engulfing",-1))
  # fake-out of mother after inside bar
  if h[i-1]<h[i-2] and l[i-1]>l[i-2]:
   if h[i]>h[i-2] and l[i]<c[i]<h[i-2]: ans.append((i,"inside_fakeout",-1))
   if l[i]<l[i-2] and l[i]<c[i]<h[i-2]: ans.append((i,"inside_fakeout",1))
  # two closes then confirmed opposite reversal
  if c[i-2]<o[i-2] and c[i-1]<o[i-1] and c[i]>o[i] and c[i]>h[i-1]: ans.append((i,"three_bar_reversal",1))
  if c[i-2]>o[i-2] and c[i-1]>o[i-1] and c[i]<o[i] and c[i]<l[i-1]: ans.append((i,"three_bar_reversal",-1))
 return ans

def run(base,market):
 b=bars5(base); idx=pd.DatetimeIndex(base.ts); rows=[]
 for _,g in b.groupby("key",sort=True):
  g=g.reset_index(); seen=set()
  for j,pat,side in signals(g):
   k=(pat,side)
   if k in seen: continue
   i=int(g["index"].iat[j]); entry_i=idx.get_indexer([b.end.iat[i]])[0]+1
   if entry_i>=len(base): continue
   seen.add(k); entry=float(base.open.iat[entry_i]); exit=float(b.close.iat[i+12]); gross=side*(exit-entry)
   rows.append(dict(market=market,pattern=pat,side="long" if side==1 else "short",signal_time=str(b.end.iat[i]),year=int(b.year.iat[i]),entry=entry,exit=exit,gross_pts=gross,net_pts=gross-COST[market]))
 return rows

def main():
 rows=[]
 for market,loader in (("NQ",load_nq),("ES",load_es)): rows+=run(loader().sort_values("ts").reset_index(drop=True),market)
 d=pd.DataFrame(rows); d["split"]=d.year.map(split_of); d.to_csv(OUT/"trades.csv",index=False)
 s=d.groupby(["market","pattern","side","split"],as_index=False).agg(trades=("net_pts","size"),win_rate=("net_pts",lambda x:(x>0).mean()),gross_expectancy_pts=("gross_pts","mean"),net_expectancy_pts=("net_pts","mean"),net_total_pts=("net_pts","sum"),profit_factor=("net_pts",lambda x:x[x>0].sum()/-x[x<0].sum() if (x<0).any() else np.nan))
 s.to_csv(OUT/"summary.csv",index=False); print(s.to_string(index=False))
if __name__=="__main__": main()
