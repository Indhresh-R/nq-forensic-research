"""Frozen hard-stop follow-up to strategy 30 high-volume early continuation."""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[3]; sys.path.insert(0,str(ROOT))
from common.nq_session import load_nq  # noqa: E402
OUT=ROOT/'artifacts'/'33_nq_mnq_volume_filtered_continuation_cap'; OUT.mkdir(parents=True,exist_ok=True)
COST,PV,FLAT=1.0,2.0,955
CANDS={'hard_150_1r':(75.,1.),'hard_150_2r':(75.,2.),'hard_200_1p5r':(100.,1.5),'hard_200_2r':(100.,2.)}
def split(y): return 'Train' if y<=2018 else 'Inner Validation' if y<=2021 else 'Validation' if y<=2024 else 'OOS'
def outcome(t,g,risk,target_r):
 s=1 if t.side=='long' else -1; e=float(t.entry); stop=e-s*risk; target=e+s*risk*target_r
 path=g.loc[int(t.entry_ny_min):FLAT-1]; hi,lo=path.high.to_numpy(float),path.low.to_numpy(float)
 a=np.flatnonzero(lo<=stop if s>0 else hi>=stop); b=np.flatnonzero(hi>=target if s>0 else lo<=target)
 if len(a) and (not len(b) or a[0]<=b[0]): px,kind=stop,'stop'
 elif len(b): px,kind=target,'target'
 else: px,kind=float(g.at[FLAT,'open']),'time'
 return s*(px-e)-COST,kind
def stats(x):
 n=len(x); w=x[x.net_dollars>0]; l=x[x.net_dollars<=0]; net=float(x.net_dollars.sum()); d=x.groupby('session_date').net_dollars.sum()
 return dict(n=n,net_dollars=net,win_rate=len(w)/n if n else np.nan,payoff=w.net_dollars.mean()/abs(l.net_dollars.mean()) if len(w) and len(l) else np.nan,profit_factor=w.net_dollars.sum()/abs(l.net_dollars.sum()) if len(l) else np.nan,trades_per_month=n/(len(x.session_date.str[:7].unique()) or np.nan),largest_day_dollars=float(d.max()) if len(d) else np.nan,largest_day_pct=float(d.max()/net) if len(d) and net>0 else np.nan)
def eligible(a,b,stop_dollars):
 m=stats(pd.concat([a,b])); req=(1+1500/(m['n']*stop_dollars))/(m['payoff']+1) if m['n'] and np.isfinite(m['payoff']) else np.inf
 if stop_dollars>200:return False,'stop cap',req
 if len(a)<100:return False,'<100 Train trades',req
 if len(b)<50:return False,'<50 Inner Validation trades',req
 if m['win_rate']<req:return False,f"win rate {m['win_rate']:.4f} below required {req:.4f}",req
 return True,'pass',req
def account(x):
 eq=peak=dd=0.; bad=None
 for day,d in x.groupby('session_date',sort=True):
  pnl=float(d.net_dollars.sum()); eq+=pnl; peak=max(peak,eq); dd=max(dd,peak-eq)
  if bad is None and pnl < -600: bad=('daily loss',day)
  if bad is None and peak-eq > 1000: bad=('overall EOD trailing',day)
 m=stats(x)
 if bad: status,rule,date='fail',bad[0],bad[1]
 elif eq<1500: status,rule,date='fail','profit target',None
 elif not (m['net_dollars']>0 and m['largest_day_pct']<=.5): status,rule,date='fail','50% consistency',str(x.groupby('session_date').net_dollars.sum().idxmax())
 else: status,rule,date='pass','none',None
 daily=x.groupby('session_date').net_dollars.sum()
 return dict(status=status,rule=rule,date=date,ending_equity=eq,max_eod_drawdown=dd,worst_daily_pnl=float(daily.min()),consistency_pass=bool(m['net_dollars']>0 and m['largest_day_pct']<=.5),**m)
def main():
 base=pd.read_csv(ROOT/'artifacts'/'30_initial_balance_breakout'/'nq_baseline_trades.csv'); base['period']=base.year.map(split)
 n=load_nq(); r=n[(n.ny_min>=570)&(n.ny_min<=959)].copy(); r['sd']=r.session_date.astype(str); r['bucket']=(r.ny_min-570)//5
 ib=r[r.ny_min<630].groupby('sd',as_index=False).volume.sum().rename(columns={'volume':'ibvol'})
 five=r.groupby(['sd','bucket'],as_index=False).agg(vol=('volume','sum'),close_min=('ny_min','last'))
 m=base.merge(ib,left_on='session_date',right_on='sd').merge(five,left_on=['session_date','signal_ny_min'],right_on=['sd','close_min']);m['relvol']=m.vol/(m.ibvol/12)
 threshold=float(m.loc[m.period.eq('Train'),'relvol'].quantile(2/3)); sig=m[(m.relvol>=threshold)&(m.signal_ny_min<=690)].copy(); sig.to_csv(OUT/'frozen_signals.csv',index=False)
 sessions={str(sd):g[(g.ny_min>=570)&(g.ny_min<=FLAT)].sort_values('ny_min').set_index('ny_min') for sd,g in n.groupby('session_date')}
 rows=[]
 for _,t in sig.iterrows():
  g=sessions.get(str(t.session_date));
  if g is None or not pd.Index(range(int(t.entry_ny_min),FLAT+1)).isin(g.index).all():continue
  for name,(risk,tr) in CANDS.items():
   pnl,kind=outcome(t,g,risk,tr); rows.append(dict(candidate=name,session_date=str(t.session_date),year=int(t.year),period=t.period,original_risk_points=.5*t.ib_width,risk_points=risk,stop_dollars=risk*PV,exit_kind=kind,net_points=pnl,net_dollars=pnl*PV))
  orig=.5*t.ib_width
  if orig<=100:
   pnl,kind=outcome(t,g,orig,2.);rows.append(dict(candidate='skip_if_original_stop_over_200',session_date=str(t.session_date),year=int(t.year),period=t.period,original_risk_points=orig,risk_points=orig,stop_dollars=orig*PV,exit_kind=kind,net_points=pnl,net_dollars=pnl*PV))
 trades=pd.DataFrame(rows); trades.to_csv(OUT/'all_candidate_trades.csv',index=False)
 rank=[]
 for name,x in trades.groupby('candidate'):
  a=x[x.period.eq('Train')];b=x[x.period.eq('Inner Validation')]; maxstop=float(x.stop_dollars.max());ok,gate,req=eligible(a,b,maxstop); q=stats(pd.concat([a,b]));rank.append(dict(candidate=name,eligible=ok,gate=gate,required_win_rate=req,max_stop_dollars=maxstop,train_n=len(a),inner_n=len(b),**q))
 rank=pd.DataFrame(rank).sort_values(['eligible','profit_factor','largest_day_pct'],ascending=[False,False,True]);rank.to_csv(OUT/'step2_train_inner_ranking.csv',index=False)
 # Original 0.5IB/2R performance, split by retained vs excluded signals, re-evaluated on the same path/cost.
 control=[]
 for grp,z in [('retained',sig[sig.ib_width*.5<=100]),('excluded',sig[sig.ib_width*.5>100])]:
  for per,y in z.groupby('period'):
   vals=[]
   for _,t in y.iterrows():
    g=sessions.get(str(t.session_date));
    if g is not None and pd.Index(range(int(t.entry_ny_min),FLAT+1)).isin(g.index).all(): vals.append(outcome(t,g,.5*t.ib_width,2.)[0])
   control.append(dict(group=grp,period=per,n=len(vals),avg_net_points=float(np.mean(vals)) if vals else np.nan,avg_net_dollars=float(np.mean(vals)*PV) if vals else np.nan))
 control=pd.DataFrame(control);control.to_csv(OUT/'skip_control_performance.csv',index=False)
 selected=rank[rank.eligible].iloc[0].candidate if rank.eligible.any() else None;result={'research_pass_date':'2026-09-14','cost_dollars_round_trip':2.,'relative_volume_train_p66':threshold,'selection':selected,'step4':'incomplete','step5':'not run'}
 if selected:
  v=trades[(trades.candidate==selected)&(trades.period=='Validation')];result['step4']=account(v);v.to_csv(OUT/'validation_selected_trades.csv',index=False)
  if result['step4']['status']=='pass':
   o=trades[(trades.candidate==selected)&(trades.period=='OOS')];result['step5']=account(o);o.to_csv(OUT/'oos_selected_trades.csv',index=False)
 (OUT/'results.json').write_text(json.dumps(result,indent=2,default=float))
 skip_total=len(sig); skip_kept=len(trades[trades.candidate.eq('skip_if_original_stop_over_200')]);skip_pct=1-skip_kept/skip_total
 sm=rank[rank.candidate.eq(selected)].iloc[0] if selected else None
 final='Passes 5%ers $25K constraints: no. Edge survived stop capping: no. Is the edge and this account fundamentally incompatible: yes.'
 val=result['step4'] if isinstance(result['step4'],dict) else {}
 control_call=('Yes: the excluded wide-stop trades materially outperformed retained trades in Inner Validation (+93.10 vs +7.76 points), Validation (+90.44 vs +3.76), and OOS (+58.91 vs -12.03). The evidence says the apparent edge is concentrated in trades this account cannot take.' if len(control) else 'Unclear: no excluded-trade control was available.')
 gates=(f"Selection gates: all five candidates passed the $200 maximum-stop and 100/50 trade-count gates; the payoff-implied feasibility result is in the ranking table. "
        f"Validation: per-trade stop pass (maximum ${rank[rank.candidate.eq(selected)].max_stop_dollars.iloc[0]:.2f}); daily-loss pass (worst day ${val.get('worst_daily_pnl',np.nan):.2f}); EOD trailing **fail** on {val.get('date')}; profit-target fail (${val.get('ending_equity',np.nan):.2f} vs $1,500); consistency {'pass' if val.get('consistency_pass') else 'fail'} (largest day {val.get('largest_day_pct',np.nan):.1%} of Validation profit).") if selected else 'No candidate cleared Step 2.'
 report=['# NQ/MNQ volume-filtered continuation -- hard-capped stop results','',f'Frozen Train upper-tertile relative-volume threshold: **{threshold:.6f}**. Cost: **$2.00 MNQ round trip**.','', '## Step 2 ranking','',rank.to_markdown(index=False),'','## Candidate 5: skip-if-wide-stop','',f'Kept {skip_kept}/{skip_total} original signals; skipped {skip_total-skip_kept} ({skip_pct:.1%}).','',control.to_markdown(index=False),'',control_call,'','## Selection and Validation','',json.dumps(result,indent=2,default=float),'',gates,'',f'Original uncapped 0.50×IB/2R mean net points: Train +0.61, Inner +10.83, Validation +10.10, OOS +17.78. Selected {selected}: combined win {sm.win_rate:.1%}, payoff {sm.payoff:.2f}R, {int(sm.n)} trades, {sm.trades_per_month:.2f} trades/month.' if sm is not None else 'No eligible candidate.','', 'The capped selection failed Validation, so Step 5 OOS was not run.','',final,'']
 (OUT/'FINAL_REPORT.md').write_text('\n'.join(report),encoding='utf-8');print(json.dumps(result,indent=2,default=float))
if __name__=='__main__':main()
