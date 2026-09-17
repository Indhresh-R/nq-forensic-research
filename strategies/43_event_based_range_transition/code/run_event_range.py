"""Frozen Strategy 43 event-based range-transition backtest."""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[3]; sys.path.insert(0,str(ROOT))
from common.nq_session import load_nq
from common.splits import split_of
OUT=ROOT/"artifacts"/"43_event_based_range_transition"; OUT.mkdir(parents=True,exist_ok=True)
Ns=(8,10,12,15); TH=(2.5,3.5,4.5); COST=1.; START=585; LAST_SIGNAL=890; FLAT=955

def rth_days():
 x=load_nq().sort_values("ts").reset_index(drop=True); return x[(x.ny_min>=570)&(x.ny_min<=FLAT)].copy()

def exit_trade(pos,timestamp,reason,price):
 gross=pos["side"]*(price-pos["entry"])
 return {**pos,"exit_time":str(timestamp),"exit":float(price),"exit_reason":reason,"gross_pts":gross,"net_pts":gross-COST,"hold_min":int((timestamp-pos["entry_ts"]).total_seconds()/60)}

def simulate(x,n,threshold):
 trades=[]; ranges=[]; breaks=[]
 for sd,g in x.groupby("session_date",sort=True):
  g=g.reset_index(drop=True); o,h,l,c=g.open.to_numpy(float),g.high.to_numpy(float),g.low.to_numpy(float),g.close.to_numpy(float); mins=g.ny_min.to_numpy(int); ts=g.ts.to_numpy(); years=g.year.to_numpy(int)
  prev=np.r_[o[0],c[:-1]]; tr=np.maximum(h-l,np.maximum(abs(h-prev),abs(l-prev))); atr=pd.Series(tr).rolling(20,min_periods=20).mean().to_numpy()
  state="IDLE"; R=None; pending=None; pos=None; br=None
  for i in range(len(g)):
   # Pending next-minute fill, then conservative stop/target check in this minute.
   if pending is not None and pos is None:
    if mins[i]>FLAT: pending=None
    else:
     pos={**pending,"entry":float(o[i]),"entry_ts":ts[i],"entry_time":str(ts[i])}; pending=None
     risk=abs(pos["entry"]-pos["stop"])
     if risk<=0: pos=None
     else: pos["risk"]=risk; pos["target"]=pos["entry"]+pos["side"]*(pos["r_mult"]*risk)
   if pos is not None:
    px=None; why=None
    if pos["side"]==1:
     if o[i]<=pos["stop"]: px,why=o[i],"gap_stop"
     elif o[i]>=pos["target"]: px,why=o[i],"gap_target"
     elif l[i]<=pos["stop"] and h[i]>=pos["target"]: px,why=pos["stop"],"collision_stop"
     elif l[i]<=pos["stop"]: px,why=pos["stop"],"stop"
     elif h[i]>=pos["target"]: px,why=pos["target"],"target"
    else:
     if o[i]>=pos["stop"]: px,why=o[i],"gap_stop"
     elif o[i]<=pos["target"]: px,why=o[i],"gap_target"
     elif h[i]>=pos["stop"] and l[i]<=pos["target"]: px,why=pos["stop"],"collision_stop"
     elif h[i]>=pos["stop"]: px,why=pos["stop"],"stop"
     elif l[i]<=pos["target"]: px,why=pos["target"],"target"
    if px is not None: trades.append(exit_trade(pos,ts[i],why,float(px))); pos=None
   if mins[i]>=FLAT:
    if pos is not None: trades.append(exit_trade(pos,ts[i],"session_flat",float(c[i]))); pos=None
    continue
   if mins[i]<START or mins[i]>LAST_SIGNAL or not np.isfinite(atr[i]) or pos is not None: continue
   a=atr[i]
   if state=="IDLE" and i>=n-1:
    up=float(h[i-n+1:i+1].max()); dn=float(l[i-n+1:i+1].min()); width=up-dn
    if width/a<=threshold:
     R={"upper":up,"lower":dn,"atr":a,"start_i":i,"fade_used":False,"year":int(years[i]),"time":str(ts[i]),"width":width}; state="RANGE"; ranges.append({"session_date":str(sd),"time":str(ts[i]),"year":int(years[i]),"width":width,"width_atr":width/a,"n":n,"threshold":threshold})
   elif state=="RANGE":
    # Breakout takes precedence and cancels any unfilled fade.
    if c[i]>=R["upper"]+.5*a and tr[i]>=a:
     state="BREAKOUT"; pending=None; br={"side":1,"boundary":R["upper"],"break_i":i,"deadline":i+30,"pb":False,"pb_extreme":np.inf,"year":R["year"]}; breaks.append({"session_date":str(sd),"time":str(ts[i]),"year":R["year"],"side":"long","width":R["width"],"width_atr":R["width"]/a,"magnitude_atr":(c[i]-R["upper"])/a,"speed_atr":tr[i]/a})
    elif c[i]<=R["lower"]-.5*a and tr[i]>=a:
     state="BREAKOUT"; pending=None; br={"side":-1,"boundary":R["lower"],"break_i":i,"deadline":i+30,"pb":False,"pb_extreme":-np.inf,"year":R["year"]}; breaks.append({"session_date":str(sd),"time":str(ts[i]),"year":R["year"],"side":"short","width":R["width"],"width_atr":R["width"]/a,"magnitude_atr":(R["lower"]-c[i])/a,"speed_atr":tr[i]/a})
    elif not R["fade_used"] and pending is None:
     if l[i]<=R["lower"]+.1*a and h[i]>=R["upper"]-.1*a: pass
     elif l[i]<=R["lower"]+.1*a:
      pending={"kind":"fade","side":1,"stop":R["lower"]-.25*a,"r_mult":(R["upper"]-.1*a-(R["lower"]+.1*a))/max((R["lower"]+.1*a)-(R["lower"]-.25*a),.01),"signal_time":str(ts[i]),"year":R["year"],"range_width":R["width"],"vol_regime":"low"}; R["fade_used"]=True
     elif h[i]>=R["upper"]-.1*a:
      pending={"kind":"fade","side":-1,"stop":R["upper"]+.25*a,"r_mult":((R["upper"]-.1*a)-(R["lower"]+.1*a))/max((R["upper"]+.25*a)-(R["upper"]-.1*a),.01),"signal_time":str(ts[i]),"year":R["year"],"range_width":R["width"],"vol_regime":"low"}; R["fade_used"]=True
   elif state=="BREAKOUT":
    if i>br["deadline"]: state="IDLE"; br=None
    elif br["side"]==1:
     if not br["pb"] and l[i]<=br["boundary"]+.1*a: br["pb"]=True; br["pb_extreme"]=l[i]
     elif br["pb"]:
      br["pb_extreme"]=min(br["pb_extreme"],l[i])
      if c[i]>h[i-1] and c[i]>=br["boundary"]+.25*a and pending is None:
       pending={"kind":"continuation","side":1,"stop":br["pb_extreme"]-.25*a,"r_mult":1.5,"signal_time":str(ts[i]),"year":br["year"],"range_width":R["width"],"vol_regime":"expansion"}; state="DONE"
    else:
     if not br["pb"] and h[i]>=br["boundary"]-.1*a: br["pb"]=True; br["pb_extreme"]=h[i]
     elif br["pb"]:
      br["pb_extreme"]=max(br["pb_extreme"],h[i])
      if c[i]<l[i-1] and c[i]<=br["boundary"]-.25*a and pending is None:
       pending={"kind":"continuation","side":-1,"stop":br["pb_extreme"]+.25*a,"r_mult":1.5,"signal_time":str(ts[i]),"year":br["year"],"range_width":R["width"],"vol_regime":"expansion"}; state="DONE"
  # Close any position missed only if final session bar logic did not run.
  if pos is not None: trades.append(exit_trade(pos,ts[-1],"session_flat",float(c[-1])))
 return pd.DataFrame(trades),pd.DataFrame(ranges),pd.DataFrame(breaks)

def metrics(d):
 if d.empty:return {"trades":0}
 r=d.net_pts/d.risk; eq=r.cumsum(); pos=r[r>0].sum(); neg=-r[r<0].sum()
 return {"trades":len(d),"win_rate":float((r>0).mean()),"avg_R":float(r.mean()),"median_R":float(r.median()),"total_R":float(r.sum()),"pf_R":float(pos/neg) if neg else np.nan,"expectancy_pts":float(d.net_pts.mean()),"max_dd_R":float((eq-eq.cummax()).min()),"max_consecutive_losses":int(max((len(z) for z in ''.join('1' if v<=0 else '0' for v in r).split('0')),default=0)),"avg_hold_min":float(d.hold_min.mean())}

def main():
 x=rth_days(); selection_x=x[x.year<=2018].copy(); surface=[]
 for n in Ns:
  for th in TH:
   d,ra,br=simulate(selection_x,n,th); surface.append({"n":n,"threshold":th,**metrics(d),"ranges":len(ra),"breakouts":len(br)})
 s=pd.DataFrame(surface); s.to_csv(OUT/"parameter_surface.csv",index=False)
 best=s.sort_values(["expectancy_pts","trades"],ascending=False).iloc[0]; n,th=int(best.n),float(best.threshold); d,ra,br=simulate(x,n,th)
 d["split"]=d.year.map(split_of); d["R"]=d.net_pts/d.risk; d.to_csv(OUT/"selected_trades.csv",index=False); ra.to_csv(OUT/"ranges.csv",index=False); br.to_csv(OUT/"breakouts.csv",index=False)
 rows=[]
 for label,mask in {"Selection_2010_18":(d.year<=2018),"IS_confirmation_2019_21":(d.year.between(2019,2021)),"IS_full":(d.year.between(2010,2021)),"Validation":(d.year.between(2022,2024)),"OOS":(d.year>=2025)}.items():
  for arm,q in [("fade",d[(d.kind=="fade")&mask]),("continuation",d[(d.kind=="continuation")&mask]),("combined",d[mask])]: rows.append({"period":label,"arm":arm,**metrics(q)})
 pd.DataFrame(rows).to_csv(OUT/"selected_summary.csv",index=False)
 yearly=d.groupby(["year","kind"]).apply(lambda q:pd.Series(metrics(q))).reset_index(); yearly.to_csv(OUT/"yearly_results.csv",index=False)
 diag={"selected":{"n":n,"threshold":th},"ranges":len(ra),"avg_range_width":float(ra.width.mean()) if len(ra) else np.nan,"avg_range_width_atr":float(ra.width_atr.mean()) if len(ra) else np.nan,"breakouts":len(br),"upside_breakouts":int((br.side=="long").sum()) if len(br) else 0,"downside_breakouts":int((br.side=="short").sum()) if len(br) else 0,"continuation_trades":int((d.kind=="continuation").sum()),"pullback_to_continuation_rate":float((d.kind=="continuation").sum()/len(br)) if len(br) else np.nan}
 (OUT/"diagnostics.json").write_text(json.dumps(diag,indent=2)); print(s.to_string(index=False)); print(pd.DataFrame(rows).to_string(index=False)); print(json.dumps(diag,indent=2))
if __name__=="__main__":main()
