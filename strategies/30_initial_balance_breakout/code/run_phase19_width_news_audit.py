"""Frozen width/risk and macro-opening-event robustness audit for continuation."""
from __future__ import annotations
import json,sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from common.nq_session import load_nq
ART=ROOT/'artifacts'/'30_initial_balance_breakout'
def metrics(x):
 p=x.net_points;w=p[p>0];l=p[p<0]
 return {'n':len(x),'mean_pts':p.mean(),'mean_R':x.net_r.mean(),'win':(p>0).mean(),'pf':w.sum()/abs(l.sum()) if len(l) else np.nan}
def main():
 b=pd.read_csv(ART/'nq_baseline_trades.csv');n=load_nq();n=n[(n.ny_min>=570)&(n.ny_min<=959)].copy();n['sd']=n.session_date.astype(str);n['bucket']=(n.ny_min-570)//5
 ib=n[n.ny_min<630].groupby('sd',as_index=False).agg(iv=('volume','sum'),ih=('high','max'),il=('low','min'));ib['width']=ib.ih-ib.il;ib['prior20']=ib.width.shift(1).rolling(20,min_periods=20).median();ib['width_vs20']=ib.width/ib.prior20
 f=n.groupby(['sd','bucket'],as_index=False).agg(v=('volume','sum'),end=('ny_min','last'));m=b.merge(ib,left_on='session_date',right_on='sd').merge(f,left_on=['session_date','signal_ny_min'],right_on=['sd','end']);m['rv']=m.v/(m.iv/12);cut=m.loc[m.year<=2018,'rv'].quantile(2/3);ids=m[(m.rv>=cut)&(m.signal_ny_min<=690)][['session_date','width_vs20']]
 d=pd.read_csv(ART/'nq_phase2_risk_grid_trades.csv').merge(ids,on='session_date');d=d[d.stop_rule.eq('0.50x_ib_width')&d.target_r.eq(2.)].copy();d['net_r']=d.net_points/d.risk_points;d['fixed_$200_pnl']=200*d.net_r
 q=np.unique(d[d.split.eq('IS')].risk_points.quantile([.2,.4,.6,.8]));d['risk_q']=pd.cut(d.risk_points,[-np.inf,*q,np.inf],labels=['Q1','Q2','Q3','Q4','Q5'])
 rows=[]
 for (sp,qb),x in d.groupby(['split','risk_q'],observed=True):rows.append({'split':sp,'group':'risk_'+str(qb),**metrics(x)})
 for cap in (20,30,40,50,60,80,100):
  for sp,x in d[d.risk_points<=cap].groupby('split'):rows.append({'split':sp,'group':f'cap_{cap}',**metrics(x)})
 for flag,x in d.assign(group=np.where(d.width_vs20>=d[d.split.eq('IS')].width_vs20.quantile(.9),'extreme_open_range','other_open_range')).groupby('group'):
  for sp,z in x.groupby('split'):rows.append({'split':sp,'group':flag,**metrics(z)})
 # Macro releases scheduled from 08:00 through 10:30 ET, based on existing dated calendar.
 ev=json.loads((ROOT/'artifacts/09_scheduled_events/fred_us_macro_events.json').read_text(encoding='utf-8'))['events'];ts=pd.to_datetime([x['createdAt'] for x in ev],utc=True).tz_convert('America/New_York');dates=set(ts[(ts.hour*60+ts.minute>=480)&(ts.hour*60+ts.minute<=630)].date.astype(str));d['open_macro']=d.session_date.isin(dates)
 for flag,x in d.groupby('open_macro'):
  for sp,z in x.groupby('split'):rows.append({'split':sp,'group':'open_macro' if flag else 'no_open_macro',**metrics(z)})
 out=pd.DataFrame(rows);out.to_csv(ART/'nq_phase19_width_news_audit.csv',index=False);d.to_csv(ART/'nq_phase19_candidate_trades.csv',index=False)
 (ART/'nq_phase19_width_news_report.md').write_text('# Phase 19 — frozen continuation width/risk/news audit\n\nNo rows select or alter the strategy. `open_macro` is an existing-calendar release dated 08:00–10:30 ET; `extreme_open_range` is the Train 90th percentile of IB-width/prior-20-session-median ratio.\n\n'+out.to_markdown(index=False),encoding='utf-8');print(out.to_string(index=False))
if __name__=='__main__':main()
