"""Phase 15: all-event and excursion-matched reversal persistence diagnostic."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from common.nq_session import load_nq
ART=ROOT/'artifacts'/'30_initial_balance_breakout';OPEN=570
def main():
 e=pd.read_csv(ART/'nq_phase7_failed_acceptance_panel.csv');e['direction']=np.where(e.break_side>0,'upside_failure','downside_failure');e['id']=np.arange(len(e))
 n=load_nq();n=n[(n.ny_min>=OPEN)&(n.ny_min<=959)].copy();n['sd']=n.session_date.astype(str);n['bucket']=(n.ny_min-OPEN)//5
 f=n.groupby(['sd','bucket'],as_index=False).agg(close=('close','last'),end=('ny_min','last'));fg={s:g.set_index('end') for s,g in f.groupby('sd',sort=False)}; paths=[]
 for _,r in e.iterrows():
  x=fg.get(r.session_date);s=int(r.signal_end)
  if x is None or not all(s+5*k in x.index for k in range(6)):continue
  c0=x.at[s,'close'];vals=[]
  for k in range(1,6):
   # Positive is reversal/giveback, negative is continued breakout.
   vals.append(-r.break_side*(x.at[s+5*k,'close']-c0)/r.ib_width)
  paths.append({'id':r.id,**{f'gb{k+1}':v for k,v in enumerate(vals)}})
 p=e.merge(pd.DataFrame(paths),on='id');
 # Greedy one-to-one nearest-neighbour matching, separately by chronological period.
 matched=[]
 for per,x in p.groupby('period'):
  up=x[x.direction.eq('upside_failure')].sort_values('excursion_ib');dn=x[x.direction.eq('downside_failure')].copy();used=set()
  for _,u in up.iterrows():
   z=dn[~dn.id.isin(used)];
   if z.empty:break
   j=(z.excursion_ib-u.excursion_ib).abs().idxmin();v=z.loc[j];used.add(v.id);matched.extend([u.id,v.id])
 p_all=p.copy();p_all['sample']='all_events'
 p_match=p[p.id.isin(matched)].copy();p_match['sample']='excursion_matched'
 p=pd.concat([p_all,p_match],ignore_index=True)
 rows=[]
 for (sample,per,direction),x in p.groupby(['sample','period','direction']):
  for k in range(1,6):
   q=x[f'gb{k}'];rows.append({'sample':sample,'period':per,'direction':direction,'bar':k,'n':len(q),'mean_giveback':q.mean(),'median_giveback':q.median(),'p_positive':(q>0).mean()})
 out=pd.DataFrame(rows);out.to_csv(ART/'nq_phase15_persistence.csv',index=False);p.to_csv(ART/'nq_phase15_events.csv',index=False)
 (ART/'nq_phase15_matched_persistence_report.md').write_text('# Phase 15 — excursion-matched reversal persistence\n\nPositive giveback means reversal relative to the first outside close. Matched samples are one-to-one nearest-excursion pairs within period.\n\n'+out.to_markdown(index=False),encoding='utf-8');print(out.to_string(index=False))
if __name__=='__main__':main()
