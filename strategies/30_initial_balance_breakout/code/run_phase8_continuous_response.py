"""Phase 8A: Train-derived quintile response curves for failed acceptance."""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[3];ART=ROOT/'artifacts'/'30_initial_balance_breakout'
FEATURES=('excursion_ib','outside_5m','reentry_depth_ib','rejection_minutes')
def main():
 d=pd.read_csv(ART/'nq_phase7_failed_acceptance_panel.csv'); rows=[]; cuts={}
 for f in FEATURES:
  x=d.loc[d.period.eq('Train'),f].dropna(); q=np.unique(x.quantile([.2,.4,.6,.8]).to_numpy())
  if len(q)<4: continue
  cuts[f]=q.tolist(); bins=pd.cut(d[f],[-np.inf,*q,np.inf],labels=['Q1','Q2','Q3','Q4','Q5'])
  for (p,b),z in d.assign(bin=bins).dropna(subset=['bin']).groupby(['period','bin'],observed=True):
   rows.append({'feature':f,'period':p,'bin':str(b),'n':len(z),'mfe60_ib':z.mfe60_ib.mean(),'mae60_ib':z.mae60_ib.mean(),'mfe_mae':z.mfe60_ib.mean()/z.mae60_ib.mean(),'net_ib':z.reversal_net_ib.mean(),'p_mfe_025':(z.mfe60_ib>.25).mean(),'p_mfe_050':(z.mfe60_ib>.5).mean(),'p_mfe_100':(z.mfe60_ib>1).mean()})
 out=pd.DataFrame(rows);out.to_csv(ART/'nq_phase8_continuous_response.csv',index=False)
 # A finding must retain the same best/worst ordering in Train and Inner.
 findings=[]
 for f,z in out.groupby('feature'):
  p=z.pivot(index='bin',columns='period',values='net_ib')
  if {'Train','Inner'}.issubset(p):
   best,worst=p.Train.idxmax(),p.Train.idxmin()
   if p.loc[best,'Inner']>p.loc[worst,'Inner']:
    findings.append({'feature':f,'best_train_bin':best,'worst_train_bin':worst,'train_gap':p.loc[best,'Train']-p.loc[worst,'Train'],'inner_gap':p.loc[best,'Inner']-p.loc[worst,'Inner'],'validation_gap':p.loc[best,'Validation']-p.loc[worst,'Validation'],'oos_gap':p.loc[best,'OOS']-p.loc[worst,'OOS']})
 fin=pd.DataFrame(findings);fin.to_csv(ART/'nq_phase8_pre2022_findings.csv',index=False)
 report=['# Phase 8A — continuous failed-acceptance response','', 'Train-derived quintiles; outcome starts at the next one-minute open after re-entry. MFE/MAE use the next 60 minutes and are normalized by IB width.','', '## Pre-2022 ordering findings','',fin.to_markdown(index=False) if len(fin) else '_None._','', '## Full response table','',out.to_markdown(index=False)]
 (ART/'nq_phase8_continuous_response_report.md').write_text('\n'.join(report),encoding='utf-8');print(fin.to_string(index=False) if len(fin) else 'No stable pre-2022 findings')
if __name__=='__main__':main()
