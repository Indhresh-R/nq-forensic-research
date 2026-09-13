"""Distributional, non-threshold test of failed-acceptance directional asymmetry."""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp, spearmanr
ROOT=Path(__file__).resolve().parents[3];ART=ROOT/'artifacts'/'30_initial_balance_breakout'
F=('excursion_ib','outside_5m','reentry_depth_ib','rejection_minutes','relvol','reentry_end')
def main():
 d=pd.read_csv(ART/'nq_phase7_failed_acceptance_panel.csv');d['direction']=np.where(d.break_side>0,'upside_failure_short','downside_failure_long')
 dist=[]; corr=[]
 for p,x in d.groupby('period'):
  up=x[x.direction.eq('upside_failure_short')];dn=x[x.direction.eq('downside_failure_long')]
  for f in F:
   a,b=up[f].dropna(),dn[f].dropna(); k=ks_2samp(a,b)
   dist.append({'period':p,'feature':f,'up_n':len(a),'up_median':a.median(),'down_n':len(b),'down_median':b.median(),'ks_stat':k.statistic,'ks_p':k.pvalue})
  for direction,z in x.groupby('direction'):
   for f in F:
    q=z[[f,'reversal_net_ib']].dropna();r= spearmanr(q[f],q.reversal_net_ib)
    corr.append({'period':p,'direction':direction,'feature':f,'n':len(q),'spearman_r':r.statistic,'p':r.pvalue})
 ds=pd.DataFrame(dist);cs=pd.DataFrame(corr);ds.to_csv(ART/'nq_phase12_direction_distributions.csv',index=False);cs.to_csv(ART/'nq_phase12_direction_correlations.csv',index=False)
 # Broadness rule: correlation sign must agree in Train, Inner, Validation, and OOS for upside, and it must not be a one-period outlier.
 broad=[]
 for (direction,f),z in cs.groupby(['direction','feature']):
  signs=np.sign(z.set_index('period').reindex(['Train','Inner','Validation','OOS']).spearman_r.dropna())
  if len(signs)==4 and len(set(signs))==1 and signs.iloc[0]!=0:broad.append({'direction':direction,'feature':f,'consistent_sign':int(signs.iloc[0]),'correlations':z.set_index('period').spearman_r.to_dict()})
 br=pd.DataFrame(broad);br.to_csv(ART/'nq_phase12_broad_mechanisms.csv',index=False)
 report=['# Phase 12 — upside-failure asymmetry','', 'No threshold selection. This report compares entire event distributions between failure directions and rank-correlates each continuous feature with 60-minute reversal net, separately by direction and period.','', '## Broad, same-sign feature/outcome relationships across all four periods','',br.to_markdown(index=False) if len(br) else '_None._','', '## Directional distributions','',ds.to_markdown(index=False),'','## Directional continuous correlations','',cs.to_markdown(index=False)]
 (ART/'nq_phase12_asymmetry_report.md').write_text('\n'.join(report),encoding='utf-8');print(br.to_string(index=False) if len(br) else 'No broad relationships')
if __name__=='__main__':main()
