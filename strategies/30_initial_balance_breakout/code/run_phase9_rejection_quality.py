"""Phase 9A: direction and excursion × rejection-quality mechanism audit."""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[3];ART=ROOT/'artifacts'/'30_initial_balance_breakout'
def stat(x):
 return {'n':len(x),'mfe60':x.mfe60_ib.mean(),'mae60':x.mae60_ib.mean(),'net':x.reversal_net_ib.mean(),'p_mfe_025':(x.mfe60_ib>.25).mean(),'p_mfe_050':(x.mfe60_ib>.5).mean()}
def main():
 d=pd.read_csv(ART/'nq_phase7_failed_acceptance_panel.csv');d['side']=np.where(d.break_side>0,'upside_failure_short','downside_failure_long')
 d['rejection_ratio']=d.reentry_depth_ib.clip(lower=0)/d.excursion_ib.replace(0,np.nan);d['rejection_speed']=d.excursion_ib/d.rejection_minutes.replace(0,np.nan)
 tr=d[d.period.eq('Train')]; ex=tr.excursion_ib.quantile(.8); rr=tr.rejection_ratio.quantile(.6)
 d['geometry']=np.where((d.excursion_ib>=ex)&(d.rejection_ratio>=rr),'large_excursion_strong_rejection','other')
 rows=[]
 for keys,x in d.groupby(['period','side','geometry']):rows.append({'period':keys[0],'side':keys[1],'geometry':keys[2],**stat(x)})
 out=pd.DataFrame(rows);out.to_csv(ART/'nq_phase9_rejection_quality.csv',index=False)
 # Same high-quality vs other comparison, pooled, using predeclared Train cutoffs.
 pooled=out.groupby(['period','geometry']).agg(n=('n','sum'),mfe60=('mfe60',lambda s:np.average(s,weights=out.loc[s.index,'n'])),mae60=('mae60',lambda s:np.average(s,weights=out.loc[s.index,'n'])),net=('net',lambda s:np.average(s,weights=out.loc[s.index,'n']))).reset_index()
 report=['# Phase 9A — rejection quality','',f'Train-fixed thresholds: excursion ≥ {ex:.3f} IB widths (top 20%) and rejection ratio ≥ {rr:.3f}. Rejection ratio is re-entry depth divided by maximum outside excursion.','', '## By direction and geometry','',out.to_markdown(index=False),'','## Pooled comparison','',pooled.to_markdown(index=False),'','Outcome is still next-60-minute normalized MFE minus MAE after the first causal re-entry. This is mechanism evidence, not a tradable confirmation rule.']
 (ART/'nq_phase9_rejection_quality_report.md').write_text('\n'.join(report),encoding='utf-8');print(out.to_string(index=False));print('\n',pooled.to_string(index=False))
if __name__=='__main__':main()
