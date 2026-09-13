"""Descriptive 2D/directional failed-acceptance response surfaces and timing."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from common.nq_session import load_nq
ART=ROOT/'artifacts'/'30_initial_balance_breakout'
def main():
 d=pd.read_csv(ART/'nq_phase7_failed_acceptance_panel.csv');d['direction']=np.where(d.break_side>0,'upside_failure_short','downside_failure_long');d['rejection_ratio']=d.reentry_depth_ib.clip(lower=0)/d.excursion_ib.replace(0,np.nan)
 tr=d[d.period.eq('Train')]; qe=np.unique(tr.excursion_ib.quantile([.2,.4,.6,.8]).to_numpy());qr=np.unique(tr.rejection_ratio.quantile([.2,.4,.6,.8]).to_numpy())
 d['exc_q']=pd.cut(d.excursion_ib,[-np.inf,*qe,np.inf],labels=['Q1','Q2','Q3','Q4','Q5']);d['rej_q']=pd.cut(d.rejection_ratio,[-np.inf,*qr,np.inf],labels=['Q1','Q2','Q3','Q4','Q5'])
 rows=[]
 for k,x in d.dropna(subset=['exc_q','rej_q']).groupby(['period','direction','exc_q','rej_q'],observed=True):rows.append({'period':k[0],'direction':k[1],'exc_q':str(k[2]),'rej_q':str(k[3]),'n':len(x),'mfe60':x.mfe60_ib.mean(),'mae60':x.mae60_ib.mean(),'net60':x.reversal_net_ib.mean()})
 surf=pd.DataFrame(rows);surf.to_csv(ART/'nq_phase10_2d_surface.csv',index=False)
 # Causal reversal timing from the event's stored next-minute entry.
 nq=load_nq();nq['sd']=nq.session_date.astype(str); groups={s:g.set_index('ny_min') for s,g in nq.groupby('sd',sort=False)}; timing=[]
 for _,r in d.iterrows():
  g=groups.get(r.session_date);side=-r.break_side
  if g is None:continue
  for h in (5,10,15,30,60):
   mins=range(int(r.entry_min),int(r.entry_min)+h)
   if not pd.Index(mins).isin(g.index).all():continue
   z=g.loc[list(mins)];e=float(g.at[int(r.entry_min),'open']);w=r.ib_width
   mfe=(e-z.low.min())/w if side<0 else (z.high.max()-e)/w;mae=(z.high.max()-e)/w if side<0 else (e-z.low.min())/w
   timing.append({'period':r.period,'direction':r.direction,'horizon_min':h,'mfe':mfe,'mae':mae,'net':mfe-mae})
 ti=pd.DataFrame(timing); ts=ti.groupby(['period','direction','horizon_min'],as_index=False).agg(n=('net','size'),mfe=('mfe','mean'),mae=('mae','mean'),net=('net','mean'));ts.to_csv(ART/'nq_phase11_reversal_timing.csv',index=False)
 report=['# Phase 10/11 — failed-acceptance response surface and timing','', 'All 2D bins use Train-fixed quintiles. Cells are descriptive; no cell is a rule.','', '## 2D surface', '',surf.to_markdown(index=False),'','## Reversal timing', '',ts.to_markdown(index=False)]
 (ART/'nq_phase10_11_report.md').write_text('\n'.join(report),encoding='utf-8');print(ts.to_string(index=False))
if __name__=='__main__':main()
