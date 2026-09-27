"""Frozen economic test: causal upside failed-acceptance short, time exits only."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from common.nq_session import load_nq
ART=ROOT/'artifacts'/'30_initial_balance_breakout';STOP_FRAC=.25;COSTS=(1.0,2.0);HOLDS=(3,5,10,15)
def main():
 e=pd.read_csv(ART/'nq_phase7_failed_acceptance_panel.csv');e=e[e.break_side.eq(1)].copy()
 n=load_nq();n['sd']=n.session_date.astype(str);g={s:x.set_index('ny_min') for s,x in n.groupby('sd',sort=False)};rows=[]
 for _,r in e.iterrows():
  x=g.get(r.session_date);entry_min=int(r.entry_min)
  if x is None:continue
  for h in HOLDS:
   ix=list(range(entry_min,entry_min+h))
   if not pd.Index(ix).isin(x.index).all():continue
   entry=float(x.at[entry_min,'open']);stop=entry+STOP_FRAC*r.ib_width;path=x.loc[ix];hit=path.high>=stop
   if hit.any(): exit_price=stop;kind='stop'
   else: exit_price=float(path.close.iloc[-1]);kind='time'
   gross=entry-exit_price
   for cost in COSTS:rows.append({'session_date':r.session_date,'year':r.year,'period':r.period,'hold_min':h,'cost_points':cost,'entry':entry,'stop':stop,'exit_kind':kind,'gross_points':gross,'net_points':gross-cost})
 t=pd.DataFrame(rows);summ=[]
 for k,x in t.groupby(['hold_min','cost_points','period']):
  p=x.net_points;w=p[p>0];l=p[p<0];eq=p.cumsum();dd=(eq-eq.cummax()).min()
  summ.append({'hold_min':k[0],'cost_points':k[1],'period':k[2],'n':len(x),'mean_net':p.mean(),'median_net':p.median(),'win':(p>0).mean(),'pf':w.sum()/abs(l.sum()) if len(l) else np.nan,'max_dd_points':dd,'stop_rate':(x.exit_kind=='stop').mean()})
 s=pd.DataFrame(summ);s.to_csv(ART/'nq_phase17_frozen_summary.csv',index=False);t.to_csv(ART/'nq_phase17_frozen_trades.csv',index=False)
 y=t[t.period.eq('OOS')].groupby(['hold_min','cost_points','year'],as_index=False).agg(n=('net_points','size'),mean_net=('net_points','mean'),median_net=('net_points','median'),win=('net_points',lambda z:(z>0).mean()))
 y.to_csv(ART/'nq_phase17_oos_yearly.csv',index=False)
 report=['# Phase 17 — frozen causal upside-failure short','', 'Rules frozen before result review: first existing Phase 7 upside failed-acceptance event; short next one-minute open after re-entry; emergency stop 0.25× IB width; time exit at 3/5/10/15 minutes. No target or filter. Costs shown at 1 and 2 NQ points round trip.','', '## Chronological results','',s.to_markdown(index=False),'','## OOS yearly diagnostic','',y.to_markdown(index=False)]
 (ART/'nq_phase17_frozen_report.md').write_text('\n'.join(report),encoding='utf-8');print(s.to_string(index=False));print(y.to_string(index=False))
if __name__=='__main__':main()
