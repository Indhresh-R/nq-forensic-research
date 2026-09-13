"""Descriptive Phase 14: breakout-direction momentum decay before failure."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from common.nq_session import load_nq
ART=ROOT/'artifacts'/'30_initial_balance_breakout';OPEN=570
def main():
 e=pd.read_csv(ART/'nq_phase7_failed_acceptance_panel.csv');e['direction']=np.where(e.break_side>0,'upside_failure','downside_failure')
 n=load_nq();n=n[(n.ny_min>=OPEN)&(n.ny_min<=959)].copy();n['sd']=n.session_date.astype(str);n['bucket']=(n.ny_min-OPEN)//5
 ib=n[n.ny_min<630].groupby('sd').agg(ih=('high','max'),il=('low','min'))
 f=n.groupby(['sd','bucket'],as_index=False).agg(close=('close','last'),end=('ny_min','last'),high=('high','max'),low=('low','min'));fg={s:g.set_index('end') for s,g in f.groupby('sd',sort=False)}
 rows=[]
 for _,r in e.iterrows():
  x=fg.get(r.session_date);s=int(r.signal_end);side=r.break_side
  if x is None or not all((s+5*k) in x.index for k in range(6)):continue
  c0=float(x.at[s,'close']);z={'session_date':r.session_date,'period':r.period,'direction':r.direction,'max_t_5m':(r.extreme_end-s)/5}
  inc=[]
  for k in range(1,6):
   prev=float(x.at[s+5*(k-1),'close']);cur=float(x.at[s+5*k,'close']);v=side*(cur-prev)/r.ib_width;z[f'r{k}']=v;inc.append(v)
  z['decay_r5_minus_r1']=inc[4]-inc[0]
  # Giveback observable on the close immediately before formal re-entry, not the inside re-entry bar itself.
  pre=int(r.reentry_end)-5
  if pre in x.index:
   boundary=float(ib.at[r.session_date,'ih'] if side>0 else ib.at[r.session_date,'il'])
   outside=side*(float(x.at[pre,'close'])-boundary)/r.ib_width
   z['pre_failure_giveback']=1-(max(outside,0)/r.excursion_ib) if r.excursion_ib>0 else np.nan
  rows.append(z)
 d=pd.DataFrame(rows);d.to_csv(ART/'nq_phase14_event_metrics.csv',index=False)
 feats=['r1','r2','r3','r4','r5','decay_r5_minus_r1','max_t_5m','pre_failure_giveback'];out=[]
 for p,x in d.groupby('period'):
  a=x[x.direction.eq('upside_failure')];b=x[x.direction.eq('downside_failure')]
  for q in feats:
   k=ks_2samp(a[q].dropna(),b[q].dropna());out.append({'period':p,'metric':q,'up_mean':a[q].mean(),'down_mean':b[q].mean(),'up_median':a[q].median(),'down_median':b[q].median(),'ks_p':k.pvalue})
 s=pd.DataFrame(out);s.to_csv(ART/'nq_phase14_direction_comparison.csv',index=False)
 (ART/'nq_phase14_momentum_decay_report.md').write_text('# Phase 14 — momentum decay\n\nPositive R means further movement in the original breakout direction; negative R means giveback. Metrics are descriptive post-event diagnostics, not causal entry features.\n\n'+s.to_markdown(index=False),encoding='utf-8');print(s.to_string(index=False))
if __name__=='__main__':main()
