"""Finite continuation matrix: risk geometry × causal entry filters."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[3]; sys.path.insert(0,str(ROOT))
from common.nq_session import load_nq  # noqa: E402
ART=ROOT/"artifacts"/"30_initial_balance_breakout"; OPEN=570; IB_END=630
def p(y): return "Train" if y<=2018 else "Inner" if y<=2021 else "Validation" if y<=2024 else "OOS"
def main():
 b=pd.read_csv(ART/"nq_baseline_trades.csv"); b["period"]=b.year.map(p)
 n=load_nq(); n=n[(n.ny_min>=OPEN)&(n.ny_min<=959)].copy(); n["sd"]=n.session_date.astype(str); n["bucket"]=(n.ny_min-OPEN)//5
 ib=n[n.ny_min<IB_END].groupby("sd",as_index=False).volume.sum().rename(columns={"volume":"ibvol"})
 f=n.groupby(["sd","bucket"],as_index=False).agg(vol=("volume","sum"),close_min=("ny_min","last"))
 m=b.merge(ib,left_on="session_date",right_on="sd",how="left").merge(f,left_on=["session_date","signal_ny_min"],right_on=["sd","close_min"],how="left")
 m["relvol"]=m.vol/(m.ibvol/12); lo,hi=m.loc[m.period.eq("Train"),"relvol"].quantile([1/3,2/3])
 m["filter"]="all"; variants=[m]
 for name,mask in [("low_volume",m.relvol<=lo),("high_volume",m.relvol>=hi),("early",m.signal_ny_min<=690),("highvol_early",(m.relvol>=hi)&(m.signal_ny_min<=690))]:
  z=m[mask].copy(); z["filter"]=name; variants.append(z)
 meta=pd.concat(variants,ignore_index=True)[["session_date","filter","period"]]
 d=pd.read_csv(ART/"nq_phase2_risk_grid_trades.csv").merge(meta,on="session_date",how="inner")
 rows=[]
 for k,x in d.groupby(["stop_rule","target_r","filter","period"]):
  q=x.net_points; w=q[q>0]; l=q[q<0]; rows.append({"stop_rule":k[0],"target_r":k[1],"filter":k[2],"period":k[3],"n":len(x),"E":q.mean(),"PF":w.sum()/abs(l.sum()) if len(l) else np.nan,"win":(q>0).mean()})
 s=pd.DataFrame(rows); s.to_csv(ART/"nq_phase6_continuation_matrix_summary.csv",index=False)
 wide=s.pivot(index=["stop_rule","target_r","filter"],columns="period",values="E").reset_index(); counts=s.pivot(index=["stop_rule","target_r","filter"],columns="period",values="n").add_prefix("n_").reset_index(); wide=wide.merge(counts,on=["stop_rule","target_r","filter"])
 base=wide[wide["filter"].eq("all")].set_index(["stop_rule","target_r"])
 keep=[]
 for i,r in wide[~wide["filter"].eq("all")].iterrows():
  q=base.loc[(r.stop_rule,r.target_r)]
  if r.Train>q.Train and r.Inner>q.Inner and r.n_Train>=100 and r.n_Inner>=50: keep.append(i)
 surv=wide.loc[keep].copy(); surv["selection"]="beats same geometry unfiltered in Train+Inner only"; wide.to_csv(ART/"nq_phase6_continuation_matrix.csv",index=False); surv.to_csv(ART/"nq_phase6_continuation_survivors.csv",index=False)
 report=["# Phase 6 — continuation matrix","","Predeclared filters: all, low/high signal-bar relative volume (Train tertiles), early signal (by 11:30), and high-volume early. Each is crossed with the Phase 2 stop/target grid. Selection uses Train and Inner only.","","## Survivors","",surv.to_markdown(index=False) if len(surv) else "_None._","","## Full matrix","",wide.to_markdown(index=False)]
 (ART/"nq_phase6_continuation_matrix_report.md").write_text("\n".join(report),encoding="utf-8"); print(surv.to_string(index=False) if len(surv) else "No Train+Inner survivors")
if __name__=="__main__": main()
