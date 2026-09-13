"""Phase 16: remaining causal post-reentry movement, excursion matched."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from common.nq_session import load_nq
ART=ROOT/'artifacts'/'30_initial_balance_breakout'
def main():
 e=pd.read_csv(ART/'nq_phase7_failed_acceptance_panel.csv');e['direction']=np.where(e.break_side>0,'upside_failure_short','downside_failure_long');e['id']=np.arange(len(e))
 n=load_nq();n['sd']=n.session_date.astype(str);g={s:x.set_index('ny_min') for s,x in n.groupby('sd',sort=False)};rows=[]
 for _,r in e.iterrows():
  x=g.get(r.session_date);side=-r.break_side;start=int(r.entry_min)
  if x is None:continue
  for h in (1,2,3,5,10,15,30):
   ix=list(range(start,start+h))
   if not pd.Index(ix).isin(x.index).all():continue
   z=x.loc[ix];entry=float(x.at[start,'open']);mfe=(entry-z.low.min())/r.ib_width if side<0 else (z.high.max()-entry)/r.ib_width;mae=(z.high.max()-entry)/r.ib_width if side<0 else (entry-z.low.min())/r.ib_width
   rows.append({'id':r.id,'period':r.period,'direction':r.direction,'excursion_ib':r.excursion_ib,'horizon':h,'mfe':mfe,'mae':mae,'net':mfe-mae,'positive':mfe>mae})
 d=pd.DataFrame(rows)
 # One-to-one nearest excursion matching separately by period (event-level).
 pairs=[]
 for p,x in e.groupby('period'):
  up=x[x.direction.eq('upside_failure_short')].sort_values('excursion_ib');dn=x[x.direction.eq('downside_failure_long')];used=set()
  for _,u in up.iterrows():
   z=dn[~dn.id.isin(used)]
   if z.empty:break
   v=z.loc[(z.excursion_ib-u.excursion_ib).abs().idxmin()];used.add(v.id);pairs += [u.id,v.id]
 d['sample']='all_events';dm=d[d.id.isin(pairs)].copy();dm['sample']='excursion_matched';d=pd.concat([d,dm])
 out=d.groupby(['sample','period','direction','horizon'],as_index=False).agg(n=('net','size'),mfe_mean=('mfe','mean'),mfe_median=('mfe','median'),mae_mean=('mae','mean'),mae_median=('mae','median'),net=('net','mean'),p_positive=('positive','mean'));out.to_csv(ART/'nq_phase16_causal_reentry.csv',index=False)
 (ART/'nq_phase16_causal_reentry_report.md').write_text('# Phase 16 — causal post-reentry response\n\nOutcome starts at next one-minute open after the causal five-minute re-entry. Matched samples use only event excursion.\n\n'+out.to_markdown(index=False),encoding='utf-8');print(out.to_string(index=False))
if __name__=='__main__':main()
