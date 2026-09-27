"""Phase 13: descriptive pre-failure state and aligned path comparison."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from common.nq_session import load_nq
ART=ROOT/'artifacts'/'30_initial_balance_breakout';OPEN=570;IBEND=630
def main():
 e=pd.read_csv(ART/'nq_phase7_failed_acceptance_panel.csv');e['direction']=np.where(e.break_side>0,'upside_failure','downside_failure')
 n=load_nq();n=n[(n.ny_min>=OPEN)&(n.ny_min<=959)].copy();n['sd']=n.session_date.astype(str);n['typ']=(n.high+n.low+n.close)/3;n['pv']=n.typ*n.volume;n['vwap']=n.groupby('sd',sort=False).pv.cumsum()/n.groupby('sd',sort=False).volume.cumsum();g={s:x.set_index('ny_min') for s,x in n.groupby('sd',sort=False)}
 rows=[];path=[]
 for _,r in e.iterrows():
  x=g.get(r.session_date);s=int(r.signal_end);side=r.break_side
  if x is None or not pd.Index(range(s-30,s+1)).isin(x.index).all():continue
  ib=x.loc[OPEN:IBEND-1]; prior=x.loc[s-1]; sig=x.loc[s];
  z={'session_date':r.session_date,'period':r.period,'direction':r.direction,'ib_width':r.ib_width,'signal_end':s,'reentry_end':r.reentry_end,'failure_delay':r.reentry_end-s,'pre_loc_ib':(prior.close-ib.low.min())/r.ib_width,'pre_vwap_ib':(prior.close-prior.vwap)/r.ib_width,'ib_drift':(ib.close.iloc[-1]-ib.open.iloc[0])/r.ib_width,'ib_half_change':(ib.close.iloc[-1]-ib.close.iloc[29])/r.ib_width}
  for h in (5,10,15,30):z[f'ret_{h}m_ib']=(sig.close-x.at[s-h,'close'])/r.ib_width
  rows.append(z)
  for k in range(1,6):
   m=s+5*k
   if m in x.index:path.append({'period':r.period,'direction':r.direction,'bar_after_break':k,'signed_close_disp_ib':side*(x.at[m,'close']-sig.close)/r.ib_width})
 st=pd.DataFrame(rows);pa=pd.DataFrame(path);st.to_csv(ART/'nq_phase13_prefailure_features.csv',index=False);pa.to_csv(ART/'nq_phase13_aligned_paths.csv',index=False)
 features=[c for c in st if c not in ('session_date','period','direction')];out=[]
 for p,x in st.groupby('period'):
  a=x[x.direction.eq('upside_failure')];b=x[x.direction.eq('downside_failure')]
  for f in features:
   k=ks_2samp(a[f].dropna(),b[f].dropna());out.append({'period':p,'feature':f,'up_median':a[f].median(),'down_median':b[f].median(),'ks':k.statistic,'p':k.pvalue})
 comp=pd.DataFrame(out);comp.to_csv(ART/'nq_phase13_state_distributions.csv',index=False)
 ps=pa.groupby(['period','direction','bar_after_break'],as_index=False).agg(n=('signed_close_disp_ib','size'),mean=('signed_close_disp_ib','mean'),median=('signed_close_disp_ib','median'));ps.to_csv(ART/'nq_phase13_path_summary.csv',index=False)
 (ART/'nq_phase13_prefailure_report.md').write_text('# Phase 13 — pre-failure state\n\n## State distributions\n\n'+comp.to_markdown(index=False)+'\n\n## Aligned breakout paths\n\n'+ps.to_markdown(index=False),encoding='utf-8');print(ps.to_string(index=False))
if __name__=='__main__':main()
