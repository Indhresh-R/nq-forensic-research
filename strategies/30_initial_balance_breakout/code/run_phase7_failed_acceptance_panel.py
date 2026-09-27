"""Causal mechanism panel for IB Failed-Acceptance Reversal (no trade exits)."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from common.nq_session import load_nq
ART=ROOT/'artifacts'/'30_initial_balance_breakout'; OPEN=570; IBEND=630; LAST=929; FLAT=955
def period(y): return 'Train' if y<=2018 else 'Inner' if y<=2021 else 'Validation' if y<=2024 else 'OOS'
def main():
 d=load_nq(); d=d[(d.ny_min>=OPEN)&(d.ny_min<=FLAT)].copy();d['sd']=d.session_date.astype(str);d['bucket']=(d.ny_min-OPEN)//5
 f=d.groupby(['sd','bucket'],as_index=False).agg(open=('open','first'),high=('high','max'),low=('low','min'),close=('close','last'),volume=('volume','sum'),end=('ny_min','last'))
 ib=d[d.ny_min<IBEND].groupby('sd',as_index=False).agg(ih=('high','max'),il=('low','min'),iv=('volume','sum'),year=('year','first'))
 rows=[]; one={sd:g.set_index('ny_min') for sd,g in d.groupby('sd',sort=False)}
 for _,x in ib.iterrows():
  b=f[f.sd.eq(x.sd)&(f.end>=634)&(f.end<=LAST)].sort_values('end'); g=one[x.sd]; w=x.ih-x.il
  if w<=0 or len(b)==0:continue
  side=0; sig=None
  for j,r in b.iterrows():
   if r.close>=x.ih+.25:side=1;sig=j;break
   if r.close<=x.il-.25:side=-1;sig=j;break
  if sig is None:continue
  after=b.loc[sig:]; outside=(after.close>x.ih) if side>0 else (after.close<x.il)
  # Must demonstrate at least two completed 5m closes outside, then later re-enter.
  if outside.sum()<2:continue
  re=after[(after.end>after.loc[sig,'end']) & ((after.close<=x.ih) if side>0 else (after.close>=x.il))]
  if re.empty:continue
  rr=re.iloc[0]; prior=after[(after.end>=after.loc[sig,'end'])&(after.end<=rr.end)]
  if side>0:
   extreme_end=int(prior.loc[prior.high.idxmax(),'end']); ex=(prior.high.max()-x.ih)/w
  else:
   extreme_end=int(prior.loc[prior.low.idxmin(),'end']); ex=(x.il-prior.low.min())/w
  nout=int(((prior.close>x.ih) if side>0 else (prior.close<x.il)).sum()); depth=(x.ih-rr.close)/w if side>0 else (rr.close-x.il)/w
  ent=int(rr.end)+1
  if ent+59>=FLAT or not pd.Index(range(ent,ent+60)).isin(g.index).all():continue
  path=g.loc[ent:ent+59]; entry=float(g.at[ent,'open']); fade=-side
  mfe=(entry-path.low.min())/w if fade<0 else (path.high.max()-entry)/w
  mae=(path.high.max()-entry)/w if fade<0 else (entry-path.low.min())/w
  rows.append({'session_date':x.sd,'year':x.year,'period':period(x.year),'break_side':side,'signal_end':int(after.loc[sig,'end']),'extreme_end':extreme_end,'reentry_end':int(rr.end),'rejection_minutes':int(rr.end)-extreme_end,'entry_min':ent,'ib_width':w,'excursion_ib':ex,'outside_5m':nout,'reentry_depth_ib':depth,'relvol':after.loc[sig,'volume']/(x.iv/12),'mfe60_ib':mfe,'mae60_ib':mae,'reversal_net_ib':mfe-mae})
 p=pd.DataFrame(rows);p.to_csv(ART/'nq_phase7_failed_acceptance_panel.csv',index=False)
 q=p[p.period.eq('Train')].excursion_ib.quantile([1/3,2/3]).to_numpy();p['exc_bin']=pd.cut(p.excursion_ib,[-np.inf,q[0],q[1],np.inf],labels=['Low','Mid','High'])
 s=p.groupby(['period','exc_bin'],observed=True).agg(n=('mfe60_ib','size'),mfe60=('mfe60_ib','mean'),mae60=('mae60_ib','mean'),net=('reversal_net_ib','mean')).reset_index();s.to_csv(ART/'nq_phase7_excursion_mechanism.csv',index=False)
 (ART/'nq_phase7_failed_acceptance_report.md').write_text('# Phase 7 — Failed-Acceptance mechanism\n\n'+s.to_markdown(index=False)+'\n\nEvent: at least two completed five-minute closes outside IB, then a later five-minute close back inside. Outcome starts next one-minute open and measures 60-minute normalized reversal MFE/MAE.\n',encoding='utf-8');print(s.to_string(index=False))
if __name__=='__main__':main()
