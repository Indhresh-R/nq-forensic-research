"""Tradability audit for the frozen high-volume early 0.5×IB/2R NQ continuation."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from common.nq_session import load_nq
ART=ROOT/'artifacts'/'30_initial_balance_breakout'
def longest_loss(x):
 best=run=0
 for v in x:
  run=run+1 if v<0 else 0;best=max(best,run)
 return best
def main():
 b=pd.read_csv(ART/'nq_baseline_trades.csv');n=load_nq();n=n[(n.ny_min>=570)&(n.ny_min<=959)].copy();n['sd']=n.session_date.astype(str);n['bucket']=(n.ny_min-570)//5
 ib=n[n.ny_min<630].groupby('sd',as_index=False).volume.sum().rename(columns={'volume':'iv'});f=n.groupby(['sd','bucket'],as_index=False).agg(v=('volume','sum'),end=('ny_min','last'))
 m=b.merge(ib,left_on='session_date',right_on='sd').merge(f,left_on=['session_date','signal_ny_min'],right_on=['sd','end']);m['rv']=m.v/(m.iv/12);cut=m.loc[m.year<=2018,'rv'].quantile(2/3);ids=m[(m.rv>=cut)&(m.signal_ny_min<=690)].session_date
 d=pd.read_csv(ART/'nq_phase2_risk_grid_trades.csv');d=d[d.session_date.isin(ids)&d.stop_rule.eq('0.50x_ib_width')&d.target_r.eq(2.0)].copy().sort_values('session_date');d['gross']=d.net_points+1;d['net_r']=d.net_points/d.risk_points;d['nq_risk_dollars']=d.risk_points*20;d['mnq_risk_dollars']=d.risk_points*2
 rows=[]
 for p,x in d.groupby('split'):
  eq=x.net_points.cumsum();rows.append({'period':p,'n':len(x),'mean_pts':x.net_points.mean(),'mean_R':x.net_r.mean(),'win':(x.net_points>0).mean(),'pf':x.loc[x.net_points>0,'net_points'].sum()/abs(x.loc[x.net_points<0,'net_points'].sum()),'median_risk_pts':x.risk_points.median(),'p95_risk_pts':x.risk_points.quantile(.95),'max_risk_pts':x.risk_points.max(),'median_nq_risk$':x.nq_risk_dollars.median(),'median_mnq_risk$':x.mnq_risk_dollars.median(),'max_dd_pts':(eq-eq.cummax()).min(),'max_consec_loss':longest_loss(x.net_points)})
 s=pd.DataFrame(rows);s.to_csv(ART/'nq_phase18_risk_summary.csv',index=False)
 costs=[]
 for c in (1.,2.,3.,4.):
  for p,x in d.groupby('split'):
   z=x.gross-c;costs.append({'cost_points':c,'period':p,'n':len(x),'mean_net':z.mean(),'mean_R':(z/x.risk_points).mean(),'win':(z>0).mean()})
 cs=pd.DataFrame(costs);cs.to_csv(ART/'nq_phase18_cost_sensitivity.csv',index=False)
 q=np.unique(d[d.split.eq('IS')].risk_points.quantile([.25,.5,.75]).to_numpy());d['risk_bin']=pd.cut(d.risk_points,[-np.inf,*q,np.inf],labels=['Q1','Q2','Q3','Q4'])
 rb=d.groupby(['split','risk_bin'],observed=True).agg(n=('net_points','size'),mean_net=('net_points','mean'),mean_R=('net_r','mean'),median_risk=('risk_points','median')).reset_index();rb.to_csv(ART/'nq_phase18_risk_bins.csv',index=False)
 y=d.groupby(['year','split'],as_index=False).agg(n=('net_points','size'),mean_net=('net_points','mean'),mean_R=('net_r','mean'),win=('net_points',lambda x:(x>0).mean()),median_risk=('risk_points','median'));y.to_csv(ART/'nq_phase18_yearly.csv',index=False)
 (ART/'nq_phase18_continuation_risk_report.md').write_text('# Phase 18 — frozen continuation risk audit\n\nRepresentative: high-volume + early, 0.50×IB stop, 2R target, 1-point baseline round-trip cost.\n\n## Risk summary\n\n'+s.to_markdown(index=False)+'\n\n## Cost sensitivity\n\n'+cs.to_markdown(index=False)+'\n\n## Train-derived risk bins\n\n'+rb.to_markdown(index=False)+'\n\n## Yearly\n\n'+y.to_markdown(index=False),encoding='utf-8');print(s.to_string(index=False));print(cs.to_string(index=False));print(y[y.year>=2025].to_string(index=False))
if __name__=='__main__':main()
