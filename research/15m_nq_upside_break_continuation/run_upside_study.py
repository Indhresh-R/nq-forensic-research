"""NQ-only causal 15m resistance-break continuation versus matched up moves."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(ROOT))
from common.nq_session import load_nq
from common.splits import split_of
OUT = ROOT / "artifacts" / "15m_nq_upside_break_continuation"; OUT.mkdir(parents=True, exist_ok=True)
H = (1, 5, 15, 30, 60); BINS = [-np.inf,.5,1,1.5,np.inf]; LAB = ("<0.5","0.5-1.0","1.0-1.5","1.5+")

def bars(x):
    y=x.copy(); y["offset"]=(y.ny_min-1080)%1440; y["bucket"]=y.offset//15
    return y.groupby(["session_date","bucket"],sort=True).agg(end=("ts","last"),open=("open","first"),high=("high","max"),low=("low","min"),close=("close","last"),n=("close","size"),year=("year","last"),key=("session_date","last")).reset_index(drop=True).query("n==15").reset_index(drop=True)

def main():
    base=load_nq().sort_values("ts").reset_index(drop=True); b=bars(base)
    hi,lo,op,cl=(b[x].to_numpy(float) for x in ("high","low","open","close")); pc=np.r_[np.nan,cl[:-1]]
    tr=np.maximum(hi-lo,np.maximum(abs(hi-pc),abs(lo-pc))); atr=pd.Series(tr).rolling(20).mean().shift(1).to_numpy()
    resistance=pd.Series(hi).rolling(20).max().shift(1).to_numpy(); up=(cl-op)/atr
    br=(cl>resistance)&(pc<=resistance); ct=(cl>op)&(cl<=resistance)&np.isfinite(up); band=pd.cut(up,BINS,labels=LAB,right=False)
    z=pd.DataFrame({"i":np.arange(len(b)),"break":br,"control":ct,"band":band,"key":b.key,"year":b.year})
    ev=pd.concat([z[z["break"]&(z.i>=21)].drop_duplicates("key").assign(event_type="break"),z[z["control"]&(z.i>=21)].drop_duplicates(["key","band"]).assign(event_type="control")],ignore_index=True).sort_values("i")
    idx=pd.DatetimeIndex(base.ts); rows=[]
    for r in ev.itertuples(index=False):
        i=int(r.i); last=idx.get_indexer([b.end.iat[i]])[0]; ent=last+1
        if last<0 or ent+60>=len(base): continue
        level=float(resistance[i]); entry=float(base.open.iat[ent]); p60=base.iloc[ent:ent+60]; closes=p60.close.to_numpy(float); failures=np.flatnonzero(closes<level)
        common=dict(event_type=r.event_type,signal_time=str(b.end.iat[i]),split=split_of(int(r.year)),year=int(r.year),band=str(r.band),normalized_up_move=float(up[i]),entry=entry,resistance=level,time_to_fail_min=(int(failures[0])+1 if len(failures) else np.nan),fraction_below_60=float(np.mean(closes<level)),max_extension_60_pts=float(p60.high.max()-level))
        for h in H:
            p=base.iloc[ent:ent+h]; ret=float(p.close.iat[-1]-entry)
            rows.append(common|dict(horizon_min=h,long_return_pts=ret,mfe_pts=float(p.high.max()-entry),mae_pts=float(p.low.min()-entry),positive_return=int(ret>0),close_above_level=int(p.close.iat[-1]>level)))
    d=pd.DataFrame(rows); d.to_csv(OUT/"events.csv",index=False)
    s=d.groupby(["split","event_type","band","horizon_min"],as_index=False).agg(events=("long_return_pts","size"),mean_long_return_pts=("long_return_pts","mean"),median_long_return_pts=("long_return_pts","median"),positive_rate=("positive_return","mean"),mfe_pts=("mfe_pts","mean"),mae_pts=("mae_pts","mean"),retention_rate=("close_above_level","mean"),time_to_fail_min=("time_to_fail_min","mean"),fraction_below_60=("fraction_below_60","mean"),max_extension_60_pts=("max_extension_60_pts","mean"))
    s.to_csv(OUT/"summary.csv",index=False); p=s.pivot_table(index=["split","band","horizon_min"],columns="event_type",values=["mean_long_return_pts","positive_rate"],aggfunc="first").dropna(); p["return_diff_break_minus_control"]=p[("mean_long_return_pts","break")]-p[("mean_long_return_pts","control")]; p["positive_rate_diff_break_minus_control"]=p[("positive_rate","break")]-p[("positive_rate","control")]; p.reset_index().to_csv(OUT/"break_minus_control.csv",index=False); print(p.reset_index().to_string(index=False))
if __name__=="__main__": main()
